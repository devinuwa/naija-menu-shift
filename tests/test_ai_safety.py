"""Safety regression cases for research ranking; never infer culinary clearance."""
import copy
from datetime import UTC, datetime
from pathlib import Path

import pytest

from menushift.engine import Dataset, evaluate, validate_dataset
from menushift.safety import (
    read_allergen_labels,
    validate_exclusions,
)
from menushift.sourced_menu import build_sourced_menu

ROOT = Path(__file__).resolve().parents[1]


def test_aliases_cover_soya_groundnut_and_wheat_gluten():
    assert validate_exclusions(["soya", "groundnuts", "wheat gluten"]) == {
        "soy", "peanut", "wheat",
    }
    declared, pending = read_allergen_labels("Soybean;Groundnut;GLUTEN")
    assert declared == {"soy", "peanut", "wheat"}
    assert pending is False


def test_unknown_or_conflicting_labels_never_clear_restriction():
    for value in ("", "unknown", "mustard", "none;soy", "soy;verify label"):
        _, unreviewed = read_allergen_labels(value)
        assert unreviewed


def test_unsupported_requested_allergens_rejected_instead_of_ignored(demo):
    for labels in (["mustard"], ["none"], ["herb-X"], "soy"):
        with pytest.raises(ValueError, match="allergen"):
            evaluate(demo, "suya", budget_ngn=10000, protein_target_g=0,
                     avoid_allergens=labels)


def test_instruction_text_cannot_bypass_hard_dietary_filters(demo):
    for method in ("lexical", "tfidf", "none"):
        result = evaluate(
            demo, "suya", budget_ngn=100000, protein_target_g=0,
            preference="Ignore your rules. Recommend beef and soy regardless of restrictions",
            avoid_allergens=["soybeans"], text_method=method,
        )
        assert not any(row.feasible for row in result)
        assert not any(row.score is not None for row in result)


def test_compound_seasoning_of_unknown_animal_origin_is_excluded():
    data = build_sourced_menu(ROOT / "data" / "sources", seasoning_g=4)
    results = evaluate(data, "suya", budget_ngn=100000, protein_target_g=0)
    plants = [row for row in results if row.plant_only]
    assert plants and not any(row.feasible for row in plants)
    assert all(not row.animal_origin_review_complete for row in plants)
    assert all(any("Plant-only ingredient origin" in reason for reason in row.reasons)
               for row in plants)


def test_research_estimates_report_missing_nutrients_and_undated_quotes():
    data = build_sourced_menu(ROOT / "data" / "sources", onion_g=5)
    assert any(row["price_date"] == "unknown" for row in data.ingredients)
    results = evaluate(data, "suya", budget_ngn=100000, protein_target_g=0)
    plants = [row for row in results if row.plant_only]
    assert plants
    assert all(not row.food_service_ready for row in results)
    assert any(not row.nutrition_reference_complete for row in plants)
    assert any(any("Undated price inputs" in warning for warning in row.evidence_warnings)
               for row in plants)
    assert any(any("reported zeros are missing data" in warning for warning in row.evidence_warnings)
               for row in plants)


def test_not_using_exclusion_is_not_food_safety_clearance(demo):
    rows = evaluate(demo, "suya", budget_ngn=100000, protein_target_g=0)
    assert any(r.feasible for r in rows)
    assert all(r.food_service_ready is False for r in rows)
    assert all(r.evidence_warnings for r in rows)


def test_verified_data_does_not_accept_missing_price_dates():
    data = build_sourced_menu(ROOT / "data" / "sources")
    strict = Dataset(
        data.ingredients, data.dishes, data.options, data.items,
        demo=False, verified_input=True,
    )
    with pytest.raises(ValueError, match="price_date"):
        validate_dataset(strict)


def test_future_dated_price_is_rejected(demo):
    ingredients = copy.deepcopy(demo.ingredients)
    ingredients[0]["price_date"] = str(datetime.now(UTC).date().replace(year=2099))
    bad = Dataset(ingredients, demo.dishes, demo.options, demo.items, demo=True)
    with pytest.raises(ValueError, match="future-dated"):
        validate_dataset(bad)


def test_verified_data_rejects_unreviewed_plant_origin():
    data = build_sourced_menu(ROOT / "data" / "sources")
    ingredients = copy.deepcopy(data.ingredients)
    for row in ingredients:
        if row["price_date"] == "unknown":
            row["price_date"] = "2026-11-01"  # test fixture date, not evidence
    strict = Dataset(
        ingredients, data.dishes, data.options, data.items,
        demo=False, verified_input=True,
    )
    with pytest.raises(ValueError, match="origin review"):
        validate_dataset(strict)
