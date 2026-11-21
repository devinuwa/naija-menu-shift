"""Hospital mode: documented UNTH menu, fail-closed transforms, honest gaps.

The menu is published research data (Maduforo et al., 2016), not demo data.
These tests pin the honesty contract: exactly 14 items, stew never assigned a
protein, already-plant items never transformed, allergen exclusions fail
closed, and the comparison never recomputes numbers.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from menushift.engine import validate_dataset
from menushift.functional import plant_proteins
from menushift.hospital import (
    CONDITIONS,
    FEEDBACK_FIELDS,
    MENU_SOURCE,
    THERAPEUTIC_PRESETS,
    append_hospital_feedback,
    build_any_dish_comparison,
    build_baseline,
    build_comparison,
    build_condition_menu,
    build_hospital_dataset,
    display_text,
    email_hospital_feedback,
    get_condition,
    get_dish,
    load_protein_prices,
    load_unth_menu,
    plant_protein_dataset,
    recommend_for_dish,
    submit_hospital_feedback,
    suggest_for_any_dish,
)

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "pages" / "3_Hospital_Menu.py"


@pytest.fixture(scope="module")
def menu():
    return load_unth_menu()


def test_menu_loads_exactly_14_items(menu):
    assert len(menu) == 14
    assert len({d.item_id for d in menu}) == 14


def test_only_fish_and_meat_carry_documented_animal_protein(menu):
    documented = {d.item_id: d.documented_animal_protein
                  for d in menu if d.protein_status == "documented_animal"}
    assert documented == {"fish": "fish", "meat": "meat"}


def test_stew_and_soups_stay_unspecified(menu):
    for item_id in ("stew", "bitterleaf_soup", "okro_soup", "egusi_soup"):
        dish = get_dish(menu, item_id)
        assert dish.protein_status == "unspecified"
        assert dish.documented_animal_protein == ""


def test_already_plant_based_flags(menu):
    flagged = {d.item_id for d in menu if d.already_plant_based}
    assert flagged == {"beans_and_yam_pottage", "okpa", "moimoi", "pap"}


def test_already_plant_items_are_never_transformed(menu):
    for item_id in ("moimoi", "okpa", "beans_and_yam_pottage", "pap"):
        result = recommend_for_dish(item_id, menu=menu)
        assert result.status == "already_plant_based"
        assert result.alternatives == ()
        assert result.requires_dietitian_signoff is True


def test_unspecified_dish_is_never_transformed(menu):
    result = recommend_for_dish("stew", menu=menu)
    assert result.status == "protein_unspecified"
    assert result.alternatives == ()


def test_dataset_builds_and_validates():
    data = build_hospital_dataset()
    validate_dataset(data)  # must not raise
    assert {d["dish_id"] for d in data.dishes} == {"unth_fish", "unth_meat"}


def test_fish_transformation_returns_ranked_plant_alternatives(menu):
    result = recommend_for_dish("fish", menu=menu)
    assert result.status == "ok"
    assert result.alternatives, "expected at least one eligible alternative"
    for alt in result.alternatives:
        assert alt.protein_id not in ("beef", "fish", "meat", "dawadawa")
        assert alt.protein_g > 0
        assert alt.cost_ngn > 0
    assert result.reference is None  # no cited fish baseline exists
    assert any("Dawadawa" in note for note in result.notes)


def test_meat_transformation_has_beef_reference_comparison_only(menu):
    result = recommend_for_dish("meat", menu=menu)
    assert result.status == "ok"
    assert result.reference is not None
    assert all(a.protein_id != "beef" for a in result.alternatives)


def test_gluten_exclusion_removes_seitan_fail_closed(menu):
    for label in ("gluten", "wheat"):
        result = recommend_for_dish("meat", avoid_allergens=(label,), menu=menu)
        assert all(a.protein_id != "seitan" for a in result.alternatives)
        seitan_rejections = [r for r in result.rejected if r.protein_id == "seitan"]
        assert seitan_rejections, "seitan must be rejected, not silently dropped"
        assert any("allergen" in reason.lower()
                   for reason in seitan_rejections[0].reasons)


def test_soy_exclusion_removes_all_soy_proteins(menu):
    result = recommend_for_dish("fish", avoid_allergens=("soy",), menu=menu)
    assert all(a.protein_id not in ("soy_chunks", "awara", "soy_milk")
               for a in result.alternatives)


def test_high_protein_preset_floor_is_enforced(menu):
    result = recommend_for_dish("fish", preset_id="high_protein", menu=menu)
    assert result.preset.protein_floor_g == 35.0
    assert result.alternatives
    assert all(a.protein_g >= 35.0 for a in result.alternatives)


def test_low_protein_preset_cap_is_enforced(menu):
    result = recommend_for_dish("fish", preset_id="low_protein", menu=menu)
    assert result.preset.protein_cap_g_per_meal == 20.0
    assert result.alternatives
    assert all(a.protein_g <= 20.0 for a in result.alternatives)


def test_low_sodium_preset_states_its_limitation(menu):
    result = recommend_for_dish("fish", preset_id="low_sodium", menu=menu)
    assert any("no sodium values" in note for note in result.notes)


def test_impossible_constraints_give_honest_empty_result(menu):
    result = recommend_for_dish("fish", budget_ngn=10.0, menu=menu)
    assert result.status == "ok"
    assert result.alternatives == ()
    assert result.rejected  # reasons are shown, not hidden
    assert any("No plant alternative passes" in note for note in result.notes)


def test_comparison_uses_recommendation_numbers_without_drift(menu):
    result = recommend_for_dish("meat", menu=menu)
    comparison = build_comparison(result)
    assert comparison is not None
    top = result.alternatives[0]
    assert comparison.alternative_protein_g == top.protein_g
    assert comparison.alternative_cost_ngn == top.cost_ngn
    assert comparison.alternative_prep_minutes == top.prep_minutes
    assert comparison.alternative_functional == top.functional
    assert comparison.alternative_allergens == top.allergens
    assert comparison.portion_g == top.portion_g
    assert comparison.original_protein_g == result.reference.protein_g
    assert comparison.original_cost_ngn == result.reference.cost_ngn


def test_comparison_omits_calories_without_cited_values(menu):
    result = recommend_for_dish("fish", menu=menu)
    comparison = build_comparison(result)
    assert comparison is not None
    assert comparison.original_calories_kcal is None
    assert comparison.alternative_calories_kcal is None
    # Fish has no cited original values; they stay unknown, never estimated.
    assert comparison.original_protein_g is None
    assert comparison.original_cost_ngn is None


def test_comparison_none_when_nothing_to_compare(menu):
    result = recommend_for_dish("moimoi", menu=menu)
    assert build_comparison(result) is None


def test_feedback_appends_rows_with_expected_columns(tmp_path):
    target = tmp_path / "hospital_feedback.csv"
    append_hospital_feedback(
        target, dish="Fish", alternative="Soy chunks (TVP)", preset="standard",
        availability="available", practicality="practical",
        cost_realistic="partly", acceptability="accepted",
        comment="Kitchen found chunks at the market.",
    )
    append_hospital_feedback(
        target, dish="Meat", alternative="Seitan (wheat gluten)",
        preset="high_protein", availability="hard to find",
        practicality="some difficulty", cost_realistic="no",
        acceptability="mixed", comment="",
    )
    with target.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert tuple(rows[0].keys()) == FEEDBACK_FIELDS
    assert len(rows) == 2
    assert rows[0]["dish"] == "Fish"
    assert rows[0]["availability"] == "available"
    assert rows[0]["review_status"] == "pending"
    assert rows[1]["alternative"] == "Seitan (wheat gluten)"


def test_feedback_rejects_uncontrolled_values(tmp_path):
    with pytest.raises(ValueError):
        append_hospital_feedback(
            tmp_path / "x.csv", dish="Fish", alternative="Awara",
            preset="standard", availability="sometimes",
            practicality="practical", cost_realistic="yes",
            acceptability="accepted",
        )


def test_hospital_page_renders_without_exception():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(PAGE), default_timeout=60).run()
    assert not at.exception
    assert any("Hospital food service" in t.value for t in at.title)


# ----------------------------------------------------------------------
# Any-dish mode: staff type any dish, the same gates rank alternatives
# ----------------------------------------------------------------------

def test_any_dish_beef_returns_ranked_alternatives_with_reasoning():
    result = suggest_for_any_dish(
        "Grilled beef skewers", current_protein="beef",
        portion_g=100, method="grill",
    )
    assert result.status == "ok"
    assert result.alternatives, "expected at least one eligible alternative"
    for alt in result.alternatives:
        assert alt.protein_id not in ("beef", "dawadawa")
        assert alt.reasons, "every ranked alternative carries its reasoning"
    assert result.requires_dietitian_signoff is True
    # Cited beef baseline: 20.3 g/100 g (WAFCT 07_023) and the WFP price row.
    assert result.baseline.protein_g == pytest.approx(20.3)
    assert result.baseline.cost_ngn == pytest.approx(637.50)


def test_any_dish_gluten_exclusion_removes_seitan_fail_closed():
    result = suggest_for_any_dish(
        "Beef pepper soup", current_protein="beef", portion_g=100,
        method="soup", avoid_allergens=("gluten",),
    )
    assert all(a.protein_id != "seitan" for a in result.alternatives)
    seitan_rejections = [r for r in result.rejected
                         if r.protein_id == "seitan"]
    assert seitan_rejections, "seitan must be rejected, not silently dropped"
    assert any("allergen" in reason.lower()
               for reason in seitan_rejections[0].reasons)


def test_any_dish_empty_name_is_a_clear_error():
    for bad in ("", "   "):
        with pytest.raises(ValueError, match="Dish name is required"):
            suggest_for_any_dish(bad, current_protein="beef", method="grill")


def test_any_dish_method_screen_rejects_with_reasons():
    # Soy milk is the sauce base: at the low-protein preset's floor it passes
    # the engine gates at 200 g, but its gelation/water-holding profile
    # cannot survive grilling - the method screen must be what rejects it.
    result = suggest_for_any_dish(
        "Grilled fish", current_protein="fish", portion_g=100,
        method="grill", preset_id="low_protein",
    )
    soy_milk = [r for r in result.rejected if r.protein_id == "soy_milk"]
    assert soy_milk, "soy milk must appear in rejected, with reasons"
    assert any("FAILED" in reason for reason in soy_milk[0].reasons)
    assert all(a.protein_id != "soy_milk" for a in result.alternatives)


def test_any_dish_fish_alternatives_without_cited_baseline():
    result = suggest_for_any_dish(
        "Fish pepper soup", current_protein="fish",
        portion_g=150, method="soup",
    )
    assert result.alternatives, "alternatives are ranked even with no baseline"
    assert result.baseline.protein_g is None
    assert result.baseline.cost_ngn is None
    assert any("No cited baseline" in note for note in result.notes)
    comparison = build_any_dish_comparison(result)
    assert comparison is not None
    assert comparison.original_protein_g is None
    assert comparison.original_cost_ngn is None
    top = result.alternatives[0]
    assert comparison.alternative_protein_g == top.protein_g
    assert comparison.alternative_cost_ngn == top.cost_ngn
    assert comparison.original_calories_kcal is None
    assert comparison.alternative_calories_kcal is None


def test_any_dish_chicken_protein_baseline_without_cited_cost():
    result = suggest_for_any_dish(
        "Chicken stew", current_protein="chicken",
        portion_g=100, method="soup",
    )
    assert result.alternatives
    # 23.0 g/100 g is cited (WAFCT 07_033); no cited chicken price exists.
    assert result.baseline.protein_g == pytest.approx(23.0)
    assert result.baseline.cost_ngn is None
    comparison = build_any_dish_comparison(result)
    assert comparison is not None
    assert comparison.original_protein_g is not None
    assert comparison.original_cost_ngn is None


def test_plant_protein_dataset_matches_functional_catalogue():
    rows = plant_protein_dataset()
    assert [r.protein_id for r in rows] == [p.id for p in plant_proteins()]
    assert len(rows) == 8
    by_id = {r.protein_id: r for r in rows}
    assert by_id["dawadawa"].role == "adjunct"  # listed, never ranked
    assert by_id["seitan"].allergens == ("wheat",)
    assert by_id["awara"].price_derived is True
    assert by_id["soy_chunks"].price_derived is False


def test_hospital_page_offers_any_dish_mode_and_dataset():
    source = PAGE.read_text(encoding="utf-8")
    assert "Any dish" in source
    assert "suggest_for_any_dish" in source
    assert "Plant protein dataset" in source
    assert "plant_protein_dataset" in source


# ----------------------------------------------------------------------
# Patient conditions: a condition maps to a documented preset bundle and
# carries cited evidence plus the limits of that evidence. No condition
# may claim a numeric filter the project data cannot support.
# ----------------------------------------------------------------------

def test_cardiovascular_condition_carries_evidence_and_limitation():
    condition = get_condition("cardiovascular")
    assert condition.preset_id == "low_sodium"
    evidence = " ".join(condition.evidence_notes)
    # The meta-analysis figures, as reported: red meat, fat, salt.
    assert "OR 1.51" in evidence
    assert "OR 1.76" in evidence
    assert "OR 1.25" in evidence
    limitations = " ".join(condition.limitations)
    assert "no sodium, saturated-fat or cholesterol values" in limitations
    assert "no numeric filter on those nutrients is applied or claimed" in (
        limitations)
    assert "not a treatment claim" in limitations
    assert any("UPTH" in source for source in condition.sources)


def test_kidney_and_hypertension_map_to_documented_presets():
    kidney = get_condition("kidney")
    assert kidney.preset_id == "low_protein"
    assert "low-protein" in kidney.preset_mapping_note
    assert "UPTH" in kidney.preset_mapping_note
    hypertension = get_condition("hypertension")
    assert hypertension.preset_id == "low_sodium"
    assert "UPTH" in hypertension.preset_mapping_note
    assert any("no numeric sodium filter is applied" in limitation
               for limitation in hypertension.limitations)


def test_diabetes_condition_states_no_gi_filter():
    condition = get_condition("diabetes")
    assert condition.preset_id == "standard"
    evidence = " ".join(condition.evidence_notes)
    assert "33.00" in evidence  # lowest measured GI, UNTH test meals
    assert "85%" in evidence  # IMSUTH legume share of protein
    limitations = " ".join(condition.limitations)
    assert "no GI, carbohydrate or calorie filter is applied or claimed" in (
        limitations)


def test_every_condition_has_limitations_and_sources():
    for condition in CONDITIONS.values():
        assert condition.limitations, condition.id
        assert condition.sources, condition.id
        assert condition.evidence_notes, condition.id


def test_unknown_condition_is_a_clear_error():
    with pytest.raises(ValueError, match="Unknown patient condition"):
        get_condition("gout")
    with pytest.raises(ValueError, match="Unknown patient condition"):
        build_condition_menu("gout")


def test_condition_menu_classifies_all_14_items_and_sums(menu):
    result = build_condition_menu("cardiovascular", menu=menu)
    assert len(result.items) == 14
    by_status = {}
    for item in result.items:
        by_status.setdefault(item.status, []).append(item)
    assert {i.dish.item_id for i in by_status["kept_as_is"]} == {
        "beans_and_yam_pottage", "okpa", "moimoi", "pap"}
    assert {i.dish.item_id for i in by_status["transformed"]} == {
        "fish", "meat"}
    assert len(by_status["confirm_with_kitchen"]) == 8
    for item in by_status["confirm_with_kitchen"]:
        assert item.recommendation is None
        assert item.alternative is None
        assert "Confirm recipe with the kitchen" in item.note
    # Totals are exactly the chosen alternatives' values, nothing else.
    chosen = [i.alternative for i in by_status["transformed"]]
    assert result.transformed_protein_g == pytest.approx(
        sum(a.protein_g for a in chosen))
    assert result.transformed_cost_ngn == pytest.approx(
        sum(a.cost_ngn for a in chosen))
    assert result.requires_dietitian_signoff is True
    assert "support dietary management of cardiovascular disease" in (
        result.framing)
    assert "not a prescription and not a served menu" in result.framing
    assert result.evidence_notes == result.condition.evidence_notes
    assert result.limitations == result.condition.limitations


def test_condition_menu_gluten_exclusion_removes_seitan(menu):
    result = build_condition_menu(
        "cardiovascular", avoid_allergens=("gluten",), menu=menu)
    for item in result.items:
        if item.alternative is not None:
            assert item.alternative.protein_id != "seitan"
        if item.recommendation is not None:
            assert all(a.protein_id != "seitan"
                       for a in item.recommendation.alternatives)
            seitan_rejections = [
                r for r in item.recommendation.rejected
                if r.protein_id == "seitan"]
            assert seitan_rejections, (
                "seitan must be rejected with reasons, not silently dropped")


def test_condition_menu_kidney_respects_the_protein_cap(menu):
    result = build_condition_menu("kidney", menu=menu)
    assert result.preset.protein_cap_g_per_meal == 20.0
    transformed = [i for i in result.items if i.status == "transformed"]
    assert transformed, "kidney bundle should still diversify fish and meat"
    for item in transformed:
        assert item.alternative is not None
        assert item.alternative.protein_g <= 20.0


def test_no_condition_claims_a_numeric_nutrient_filter_it_cannot_support():
    # The honesty contract, pinned: no condition text may claim a sodium,
    # fat, cholesterol or glycaemic filter/threshold (the project data
    # holds no such values), and every condition must state a limitation
    # in negative terms - what it does NOT do.
    forbidden_claims = (
        "filters candidates by", "ranked by sodium", "ranked by glycaemic",
        "sodium threshold", "fat threshold", "cholesterol threshold",
        "gi threshold", "maximum sodium of", "sodium limit of",
    )
    for condition in CONDITIONS.values():
        text = " ".join(
            condition.evidence_notes + condition.limitations
            + (condition.preset_mapping_note,)).lower()
        for claim in forbidden_claims:
            assert claim not in text, (condition.id, claim)
        limitations = " ".join(condition.limitations).lower()
        assert "no " in limitations or "not " in limitations, condition.id


def test_hospital_page_condition_view_renders():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(PAGE), default_timeout=60).run()
    assert not at.exception
    at.selectbox(key="patient_condition").set_value("cardiovascular").run()
    assert not at.exception
    texts = (
        [t.value for t in at.title]
        + [t.value for t in at.subheader]
        + [t.value for t in at.markdown]
        + [t.value for t in at.info]
        + [t.value for t in at.caption]
        + [t.value.to_string() for t in at.dataframe]
    )
    joined = "\n".join(texts)
    assert "support dietary management of cardiovascular disease" in joined
    assert "Confirm recipe with the kitchen" in joined
    # Product rule (user): limitation notes stay in the data layer and are
    # no longer rendered on the page.
    assert "no sodium, saturated-fat or cholesterol values" not in joined


# ----------------------------------------------------------------------
# Display rule: the product UI never names its data sources. Provenance
# stays in the module's source fields and the evidence pages; everything
# the Hospital page renders passes through display_text() first.
# ----------------------------------------------------------------------

BANNED_DISPLAY_TOKENS = (
    "WAFCT", "USDA", "WFP", "NBS", "Maduforo", "Pakistan Journal of Nutrition",
    "Batubo", "Keshinro", "Journal of", "UPTH", "Daily Trust",
    "Frontiers in Nutrition", "SIWES", "FoodData Central",
)


def _assert_display_clean(text: str) -> None:
    shown = display_text(text)
    for token in BANNED_DISPLAY_TOKENS:
        assert token not in shown, (token, shown)


def test_display_text_strips_sources_but_keeps_evidence():
    _assert_display_clean(MENU_SOURCE)
    assert "2016" in display_text(MENU_SOURCE)
    for preset in THERAPEUTIC_PRESETS.values():
        _assert_display_clean(preset.label)
        _assert_display_clean(preset.source)
        for note in preset.notes:
            _assert_display_clean(note)
    # The preset labels keep their clinical content, minus the citation.
    assert display_text(THERAPEUTIC_PRESETS["high_protein"].label) == (
        "High protein (1.5-2.0 g/kg/day)")
    for condition in CONDITIONS.values():
        _assert_display_clean(condition.preset_mapping_note)
        for note in condition.evidence_notes:
            _assert_display_clean(note)
        for limitation in condition.limitations:
            _assert_display_clean(limitation)
    # The meta-analysis figures survive; only the citation is removed.
    cardio = get_condition("cardiovascular")
    shown_evidence = display_text(" ".join(cardio.evidence_notes))
    assert "OR 1.51" in shown_evidence
    assert "OR 1.76" in shown_evidence
    assert "OR 1.25" in shown_evidence
    # Price bases keep their honesty content (derived, floor, verify).
    for price in load_protein_prices().values():
        _assert_display_clean(price.price_basis)
    egusi_basis = display_text(load_protein_prices()["egusi"].price_basis)
    assert "modelled" in egusi_basis and "floor value" in egusi_basis
    # Baselines: "no cited value" becomes "no verified value available".
    fish = build_baseline("fish", 100.0)
    _assert_display_clean(fish.note)
    assert "No verified baseline available" in display_text(fish.note)
    chicken = build_baseline("chicken", 100.0)
    _assert_display_clean(chicken.note)


def test_display_text_keeps_recommendation_notes_clean(menu):
    for dish_id in ("fish", "meat"):
        result = recommend_for_dish(dish_id, menu=menu)
        for note in result.notes:
            _assert_display_clean(note)
        for alt in result.alternatives:
            _assert_display_clean(alt.price_basis)
            for reason in alt.reasons:
                _assert_display_clean(reason)
        comparison = build_comparison(result)
        assert comparison is not None
        for note in comparison.notes:
            _assert_display_clean(note)
    fish_comparison = build_comparison(recommend_for_dish("fish", menu=menu))
    assert fish_comparison is not None
    assert "no verified values are available" in display_text(
        " ".join(fish_comparison.notes))
    condition_menu = build_condition_menu("cardiovascular", menu=menu)
    for note in condition_menu.notes:
        _assert_display_clean(note)
    for item in condition_menu.items:
        _assert_display_clean(item.note)


def _rendered_text(at) -> str:
    parts: list[str] = []
    for name in ("title", "header", "subheader", "markdown", "text",
                 "caption", "warning", "info", "error", "success"):
        for element in getattr(at, name, []):
            parts.append(str(element.value))
    for element in getattr(at, "dataframe", []):
        parts.append(element.value.to_string())
    for element in getattr(at, "metric", []):
        parts.append(f"{element.label} {element.value}")
    return "\n".join(parts)


def test_hospital_page_never_renders_source_names():
    from streamlit.testing.v1 import AppTest

    # Documented-menu mode (default landing state).
    at = AppTest.from_file(str(PAGE), default_timeout=60).run()
    assert not at.exception
    shown = _rendered_text(at)
    assert "Hospital food service" in shown  # the page actually rendered
    for token in BANNED_DISPLAY_TOKENS:
        assert token not in shown, token
    # Condition view.
    at.selectbox(key="patient_condition").set_value("cardiovascular").run()
    assert not at.exception
    shown = _rendered_text(at)
    assert "support dietary management of cardiovascular disease" in shown
    for token in BANNED_DISPLAY_TOKENS:
        assert token not in shown, token
    # Any-dish mode with a typed dish and ranked alternatives.
    at_any = AppTest.from_file(str(PAGE), default_timeout=60).run()
    assert not at_any.exception
    at_any.radio[0].set_value("Any dish (type your own)").run()
    assert not at_any.exception
    at_any.text_input[0].set_value("Grilled beef skewers").run()
    assert not at_any.exception
    shown = _rendered_text(at_any)
    assert "Recommended additional options" in shown
    for token in BANNED_DISPLAY_TOKENS:
        assert token not in shown, token


# ----------------------------------------------------------------------
# Feedback email: the CSV row is the record; email delivery is a
# best-effort copy to the team inbox and is reported honestly.
# ----------------------------------------------------------------------

def _feedback_fields(**overrides):
    fields = {
        "dish": "Fish",
        "alternative": "Awara (soy curd / tofu)",
        "preset": "standard",
        "availability": "available",
        "practicality": "practical",
        "cost_realistic": "partly",
        "acceptability": "accepted",
        "comment": "",
    }
    fields.update(overrides)
    return fields


def test_feedback_email_success_and_failure_paths():
    row = {field: "" for field in FEEDBACK_FIELDS}
    row.update(_feedback_fields())
    seen = {}

    def ok_post(url, payload):
        seen["url"] = url
        seen["payload"] = payload
        return 200

    assert email_hospital_feedback(row, http_post=ok_post) is True
    assert seen["url"] == (
        "https://formsubmit.co/ajax/inuwamuhammad930@gmail.com")
    assert "Fish" in seen["payload"]["message"]
    assert email_hospital_feedback(row, http_post=lambda url, payload: 500) is False

    def dead_network(url, payload):
        raise ConnectionError("offline")

    assert email_hospital_feedback(row, http_post=dead_network) is False


def test_submit_hospital_feedback_saves_row_regardless_of_email(tmp_path):
    target = tmp_path / "hospital_feedback.csv"
    row, emailed = submit_hospital_feedback(
        target, http_post=lambda url, payload: 200, **_feedback_fields())
    assert emailed is True
    assert row["dish"] == "Fish"

    def dead_network(url, payload):
        raise ConnectionError("offline")

    _row2, emailed2 = submit_hospital_feedback(
        target, http_post=dead_network,
        **_feedback_fields(dish="Meat"))
    assert emailed2 is False  # reported honestly, row still saved
    with target.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [r["dish"] for r in rows] == ["Fish", "Meat"]
