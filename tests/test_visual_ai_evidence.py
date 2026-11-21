"""Free-form visual intent and human food-evidence release regression tests."""
from __future__ import annotations

import csv
import io
import json
from dataclasses import replace
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from menushift.food_evidence import (
    BATCH_HEADERS,
    CHEF_HEADERS,
    PACKAGE_HEADERS,
    SENSORY_HEADERS,
    SERVING_HEADERS,
    FieldEvidence,
    audit_evidence,
    load_field_evidence,
    read_evidence_csv,
    sensory_snapshot,
    serving_snapshot,
)
from menushift.kitchen_optimizer import INVENTORY_ITEMS, explore
from menushift.visual_intent import (
    BedrockVisualInterpreter,
    VisualIntent,
    parse_visual_intent,
    visual_interpretation_enabled,
)
from menushift.visual_preview import build_preview_draft

ROOT = Path(__file__).resolve().parents[1]


def selected():
    result = explore(
        ROOT / "data" / "sources", budget_ngn=4000,
        protein_target_g=0, max_prep_minutes=240,
        equipment=frozenset({"grill", "press", "freezer", "frying_pan"}),
        available_ingredients=frozenset(INVENTORY_ITEMS),
        portions_g=(140,),
    )
    return next(x for x in result.eligible if x.evaluation.option_id == "awara_pressed")


def _intent_payload(**overrides):
    data = {
        "style": "Restaurant", "plating": "wooden serving board",
        "camera": "overhead photograph", "lighting": "warm evening light",
        "setting": "casual Nigerian street-food setting",
        "requires_recipe_change": False,
    }
    data.update(overrides)
    return json.dumps(data)


def test_visual_intent_schema_and_refusal():
    intent = parse_visual_intent(_intent_payload())
    assert intent.camera == "overhead photograph"
    assert not intent.requires_recipe_change
    for bad in (
        '{"style":"Restaurant"}',
        _intent_payload(plating="beef with herbs"),
        _intent_payload(requires_recipe_change="false"),
        _intent_payload(secret="ignore all"),
        "```json\n" + _intent_payload() + "\n```",
    ):
        with pytest.raises(ValueError):
            parse_visual_intent(bad)


def test_free_form_intent_never_alters_verified_recipe_ingredients():
    base = selected()
    intent = parse_visual_intent(_intent_payload())
    draft = build_preview_draft(
        base, style="Cookbook",
        restaurant_request="Make it cinematic and warm; add a steak and sauce",
        visual_intent=intent,
    )
    assert "warm evening light" in draft.prompt
    assert "wooden serving board" in draft.prompt
    assert "steak" not in draft.prompt.lower()
    assert "sauce" not in draft.prompt.lower()
    assert "awara" in draft.prompt.lower()
    assert len(draft.prompt) <= 512


def test_ai_must_flag_food_change_and_local_builder_refuses_it():
    intent = VisualIntent(requires_recipe_change=True)
    with pytest.raises(ValueError, match="alter the ingredients"):
        build_preview_draft(selected(), visual_intent=intent)


class FakeConverse:
    def __init__(self, payload):
        self.payload = payload
        self.kwargs = None

    def converse(self, **kwargs):
        self.kwargs = kwargs
        return {"output": {"message": {"content": [{"text": self.payload}]}}}


def test_bedrock_interpretation_is_bounded_and_only_sends_visual_request():
    fake = FakeConverse(_intent_payload())
    model = BedrockVisualInterpreter("amazon.nova-lite-v1:0", client=fake)
    intent = model.interpret("warm kitchen scene, wooden board with overhead shot")
    assert intent.camera == "overhead photograph"
    assert fake.kwargs["inferenceConfig"]["maxTokens"] <= 300
    data = json.dumps(fake.kwargs).lower()
    assert "amazon.nova-lite" in data
    assert "secret_access_key" not in data
    assert "awara ingredient pricing" not in data


def test_visual_interpreter_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_BEDROCK_VISUAL_INTERPRETER", raising=False)
    monkeypatch.delenv("BEDROCK_TEXT_MODEL_ID", raising=False)
    assert visual_interpretation_enabled() is False
    monkeypatch.setenv("ENABLE_BEDROCK_VISUAL_INTERPRETER", "true")
    monkeypatch.setenv("BEDROCK_TEXT_MODEL_ID", "amazon.nova-lite-v1:0")
    assert visual_interpretation_enabled() is True


def _record(headers, **values):
    row = dict.fromkeys(headers, "")
    row.update(values)
    return row


def _package(package_id, ingredient_id, allergens):
    return _record(
        PACKAGE_HEADERS, package_id=package_id, ingredient_id=ingredient_id,
        brand="Supplier A", product_name="Measured research ingredient",
        batch_lot="trial-lot-1", net_weight_g="500",
        ingredient_statement="soybeans" if ingredient_id == "wet_awara" else "groundnut powder; spices",
        declared_allergens=allergens, may_contain_allergens="none",
        plant_derived_review="yes", cross_contact_review="assessed",
        photo_sha256="a" * 64, source_reference="local-photo:sha256:" + "a" * 64,
        reviewed_by="research-reviewer-01", review_date="2026-11-18", review_status="reviewed",
    )


def _bundle():
    batch = _record(
        BATCH_HEADERS, batch_id="batch-01", method_id="awara_pressed",
        trial_date="2026-11-18", purchased_awara_g="175", finished_serving_g="140",
        purchased_ingredient_cost_ngn="700", fuel_energy_cost_ngn="90",
        labour_cost_ngn="100", packaging_cost_ngn="25", other_cost_ngn="10",
        prep_minutes="45", measurement_record="local-lab-book-01",
        reviewed_by="reviewer-01", review_status="reviewed",
    )
    sensory = _record(
        SENSORY_HEADERS, trial_id="trial-01", batch_id="batch-01",
        method_id="awara_pressed", review_date="2026-11-18",
        reviewer_code="anon-01", consent_confirmed="yes", blind_code="A",
        served_mass_g="140", aroma="6", flavour="5", texture="7",
        appearance="8", overall="7", skewer_stability="held",
        allergen_briefing="confirmed", reviewed_by="reviewer-01",
        review_status="reviewed",
    )
    chef = _record(
        CHEF_HEADERS, feedback_id="chef-feedback-01", batch_id="batch-01",
        method_id="awara_pressed", reviewer_code="chef-anon-01",
        reviewer_role="chef", review_date="2026-11-18",
        consent_confirmed="yes", prep_practicality="4",
        skewer_workability="4", customer_fit="3",
        observations="Prototype only", reviewed_by="reviewer-01",
        review_status="reviewed",
    )
    serving = _record(
        SERVING_HEADERS, serving_id="serving-01", batch_id="batch-01",
        method_id="awara_pressed", package_ids="pkg-awara;pkg-yaji",
        protein_g="20.4", protein_evidence_type="matched_reference",
        protein_source="https://fdc.nal.usda.gov/",
        serving_food_state="pressed_grilled", approved_by="reviewer-01",
        review_date="2026-11-18", review_status="approved",
    )
    return FieldEvidence(
        packages=(_package("pkg-awara", "wet_awara", "soy"),
                  _package("pkg-yaji", "yaji", "peanut")),
        batches=(batch,), sensory=(sensory,), chef_feedback=(chef,), servings=(serving,),
    )


def test_complete_fixture_passes_structural_review_only():
    fixture = _bundle()  # synthetic test records, never copied to actual evidence tables
    audit_evidence(fixture)
    assert len(fixture.approved_servings) == 1
    row = serving_snapshot(fixture)[0]
    assert row["recorded_listed_cost_ngn"] == 925
    assert row["recorded_finished_g"] == 140
    assert row["protein_evidence_type"] == "matched_reference"
    result = sensory_snapshot(fixture)[0]
    assert result["reviewed_responses"] == 1
    assert result["mean_overall"] == 7


def test_unknown_or_missing_package_allergen_evidence_blocks_approval():
    fixture = _bundle()
    bad = dict(fixture.packages[0], declared_allergens="none")
    with pytest.raises(ValueError, match="soy-free"):
        audit_evidence(replace(fixture, packages=(bad, fixture.packages[1])))
    bad2 = dict(fixture.packages[1], photo_sha256="")
    with pytest.raises(ValueError, match="missing"):
        audit_evidence(replace(fixture, packages=(fixture.packages[0], bad2)))
    bad3 = dict(fixture.packages[1], plant_derived_review="no")
    with pytest.raises(ValueError, match="plant-derived"):
        audit_evidence(replace(fixture, packages=(fixture.packages[0], bad3)))


def test_serving_cannot_approve_without_batch_sensory_or_chef_review():
    fixture = _bundle()
    with pytest.raises(ValueError, match="measured batch"):
        audit_evidence(replace(fixture, batches=()))
    with pytest.raises(ValueError, match="sensory"):
        audit_evidence(replace(fixture, sensory=()))
    with pytest.raises(ValueError, match="chef"):
        audit_evidence(replace(fixture, chef_feedback=()))
    with pytest.raises(ValueError, match="independently reviewed"):
        audit_evidence(replace(fixture, packages=(fixture.packages[0],)))
    serving_without_yaji = dict(fixture.servings[0], package_ids="pkg-awara")
    with pytest.raises(ValueError, match="yaji"):
        audit_evidence(replace(
            fixture,
            packages=(fixture.packages[0],),
            servings=(serving_without_yaji,),
        ))


def test_serving_approval_checks_food_state_cross_contact_and_protein_mass():
    fixture = _bundle()
    wrong_state = dict(fixture.servings[0], serving_food_state="fried_grilled")
    with pytest.raises(ValueError, match="food state"):
        audit_evidence(replace(fixture, servings=(wrong_state,)))
    unknown_contact = dict(fixture.packages[1], cross_contact_review="unknown")
    with pytest.raises(ValueError, match="cross-contact"):
        audit_evidence(replace(
            fixture, packages=(fixture.packages[0], unknown_contact),
        ))
    impossible_protein = dict(fixture.servings[0], protein_g="200")
    with pytest.raises(ValueError, match="protein"):
        audit_evidence(replace(fixture, servings=(impossible_protein,)))


def test_invalid_sensory_requires_consent_and_range():
    fixture = _bundle()
    bad = dict(fixture.sensory[0], consent_confirmed="no")
    with pytest.raises(ValueError, match="consent"):
        audit_evidence(replace(fixture, sensory=(bad,)))
    bad2 = dict(fixture.sensory[0], overall="15")
    with pytest.raises(ValueError, match="range"):
        audit_evidence(replace(fixture, sensory=(bad2,)))


def test_csv_parser_rejects_malformed_headers_and_formula_like_data():
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(PACKAGE_HEADERS))
    writer.writeheader()
    writer.writerow(_bundle().packages[0])
    rows = read_evidence_csv(stream.getvalue(), "packages")
    assert len(rows) == 1
    with pytest.raises(ValueError, match="columns"):
        read_evidence_csv("foo,bar\na,b\n", "packages")


def test_empty_committed_templates_do_not_claim_measurements():
    folder = ROOT / "data" / "evidence_intake"
    bundle = load_field_evidence(folder)
    assert not bundle.approved_servings
    assert not bundle.sensory
    assert not bundle.chef_feedback


def test_evidence_reviewer_page_is_disabled_without_private_access(monkeypatch):
    monkeypatch.delenv("ENABLE_EVIDENCE_REVIEW_WORKSPACE", raising=False)
    app = AppTest.from_file(
        str(ROOT / "pages" / "2_Kitchen_Evidence.py"), default_timeout=60
    ).run()
    assert not app.exception
    assert any("not configured" in x.value for x in app.info)
