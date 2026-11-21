"""Ingredient availability, cost traces, trial-card and agent validation regressions."""
import json
from pathlib import Path

import pytest

from menushift.agent_contract import (
    KitchenBrief,
    evaluate_candidate,
    parse_proposals,
    run_agent,
)
from menushift.bedrock_adapter import BedrockPlanner
from menushift.kitchen_optimizer import INVENTORY_ITEMS, explore
from menushift.recipe_trial import build_trial

SOURCES = Path(__file__).resolve().parents[1] / "data" / "sources"
EQUIPMENT = frozenset({"grill", "press", "freezer", "frying_pan"})


def _plan(**kwargs):
    params = {
        "budget_ngn": 3000.0, "protein_target_g": 10.0,
        "max_prep_minutes": 240.0, "equipment": EQUIPMENT,
        "available_ingredients": frozenset(INVENTORY_ITEMS),
        "portions_g": (100, 140), "oil_cl": 1.0,
    }
    params.update(kwargs)
    return explore(SOURCES, **params)


def _proposal(method="awara_firm", portion=140, **kwargs):
    value = {
        "method_id": method, "portion_g": portion,
        "onion_g": 0, "pepper_g": 0, "salt_g": 0, "seasoning_g": 0,
        "reason": "Test source-referenced portions without unsupported nutrition claims",
    }
    value.update(kwargs)
    return value


def _brief(**kwargs):
    params = {
        "budget_ngn": 3000.0, "min_protein_g": 10.0, "max_prep_minutes": 240.0,
        "equipment": EQUIPMENT, "available_ingredients": frozenset(INVENTORY_ITEMS),
    }
    params.update(kwargs)
    return KitchenBrief(**params)


def test_stock_absence_excludes_only_relevant_methods():
    no_oil = _plan(available_ingredients=frozenset(INVENTORY_ITEMS) - {"oil"})
    assert no_oil.skipped_ingredients == 2
    assert all(c.evaluation.option_id != "awara_fried" for c in no_oil.candidates)
    without_awara = _plan(available_ingredients=frozenset(INVENTORY_ITEMS) - {"awara"})
    assert without_awara.skipped_ingredients == 8
    assert not without_awara.eligible


def test_optional_spice_stock_filters_only_selected_recipe_lines():
    # Pepper is not required if its quantity is zero.
    stock = frozenset(INVENTORY_ITEMS) - {"pepper"}
    assert _plan(available_ingredients=stock, pepper_g=0).skipped_ingredients == 0
    result = _plan(available_ingredients=stock, pepper_g=5)
    assert result.skipped_ingredients == 8
    assert not result.eligible


def test_peanut_exclusion_abstains_even_if_yaji_not_modelled():
    result = _plan(avoid_allergens=("peanut",))
    assert not result.eligible
    assert result.skipped_unverified_yaji > 0


def test_unknown_inventory_rejected_without_silent_default():
    with pytest.raises(ValueError, match="Unknown inventory"):
        _plan(available_ingredients=frozenset({"random-food"}))


def test_cost_and_nutrient_trace_reconciles_with_underlying_engine():
    result = _plan(price_shock=0.2, onion_g=10, pepper_g=3)
    assert result.eligible
    for c in result.candidates:
        assert abs(sum(i.estimated_cost_ngn for i in c.ingredient_lines) -
                   c.evaluation.ingredient_cost_ngn) < 0.06
        assert abs(sum(i.estimated_protein_g for i in c.ingredient_lines) -
                   c.evaluation.protein_g) < 0.06
        assert c.evaluation.cost_ngn >= c.evaluation.ingredient_cost_ngn


def test_trial_card_has_explicit_limits_and_source_references():
    candidate = _plan().best("budget")
    assert candidate is not None
    trial = build_trial(candidate)
    report = trial.to_markdown(candidate)
    assert "Not approved for food service" in report
    assert "## Ingredients" in report
    assert "## At a glance" in report
    assert "  - Price:" in report
    assert "## Method — numbered kitchen trial" in report
    assert "## Measurements needed for a real recipe" in report


def test_no_trial_card_for_ineligible_formulation():
    candidate = _plan(budget_ngn=1).candidates[0]
    with pytest.raises(ValueError, match="ineligible"):
        build_trial(candidate)


def test_parser_requires_exact_json_contract():
    raw = json.dumps({"proposals": [_proposal()]})
    assert parse_proposals(raw)[0]["method_id"] == "awara_firm"
    for payload in (
        "```json\n" + raw + "\n```",
        json.dumps({"proposals": [_proposal(unknown_key=1)]}),
        json.dumps({"proposals": [_proposal(portion=True)]}),
        json.dumps({"proposals": [_proposal(salt_g=99)]}),
        json.dumps({"proposals": [_proposal(method="mystery")]}),
        json.dumps({"proposals": [_proposal()] * 7}),
    ):
        with pytest.raises(ValueError):
            parse_proposals(payload)


class FakePlanner:
    calls = 0

    def propose(self, *, brief, feedback, round_number):
        self.calls += 1
        if round_number == 1:
            return json.dumps({"proposals": [
                _proposal(method="awara_fried"),
                _proposal(method="awara_firm"),
            ]})
        assert feedback  # Needs explicit local critique before retrying.
        return json.dumps({"proposals": [_proposal(method="awara_pressed", portion=180)]})


def test_bounded_agent_rejects_missing_stock_and_keeps_valid_candidates():
    fake = FakePlanner()
    brief = _brief(available_ingredients=frozenset(INVENTORY_ITEMS) - {"oil"})
    result = run_agent(fake, brief, SOURCES)
    assert fake.calls <= 2
    assert result.rounds <= 2
    assert any(not d.accepted for d in result.decisions)
    assert all(c.eligible for c in result.accepted)
    assert all("awara_fried" not in c.identifier for c in result.accepted)


def test_agent_allergy_exclusion_cannot_be_overridden_by_model():
    decision = evaluate_candidate(
        _proposal(method="awara_firm"), _brief(avoid_allergens=("soy",)), SOURCES
    )
    assert not decision.accepted


class FakeConverseClient:
    def __init__(self):
        self.kwargs = None

    def converse(self, **kwargs):
        self.kwargs = kwargs
        return {"output": {"message": {"content": [
            {"text": json.dumps({"proposals": [_proposal()]})}
        ]}}}


def test_bedrock_adapter_passes_only_bounded_opaque_brief():
    fake = FakeConverseClient()
    planner = BedrockPlanner("amazon.nova-lite-v1:0", client=fake)
    response = planner.propose(brief=_brief(), feedback=(), round_number=1)
    assert parse_proposals(response)
    assert fake.kwargs["modelId"] == "amazon.nova-lite-v1:0"
    assert fake.kwargs["inferenceConfig"]["maxTokens"] <= 900
    assert "aws_secret_access_key" not in json.dumps(fake.kwargs).lower()


def test_sandbox_region_and_model_id_are_validated():
    with pytest.raises(ValueError):
        BedrockPlanner("foo", region="eu-west-1", client=FakeConverseClient())
    with pytest.raises(ValueError):
        BedrockPlanner("model with spaces", client=FakeConverseClient())
