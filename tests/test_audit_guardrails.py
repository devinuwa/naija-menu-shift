"""Regression checks for model utility, incomplete allergens and CSV integrity."""
from pathlib import Path

import pytest

from menushift.engine import Dataset, _protein_utility, evaluate, load_dataset, read_csv


@pytest.fixture
def audit_demo():
    return load_dataset(Path(__file__).resolve().parents[1] / "data" / "demo", demo=True)


def test_protein_utility_rewards_more_protein_after_threshold():
    assert _protein_utility(0, 0) == 0
    assert 0 < _protein_utility(10, 10) < _protein_utility(15, 10) < 1
    assert _protein_utility(100, 10) < 1


def test_allergen_exclusion_abstains_when_labels_are_incomplete(audit_demo):
    rows = evaluate(audit_demo, "suya", budget_ngn=10000, protein_target_g=0,
                    avoid_allergens=["sesame"])
    assert not any(row.feasible for row in rows)
    assert any("label review is incomplete" in reason
               for row in rows for reason in row.reasons)


def test_allergen_exclusion_allows_explicitly_reviewed_ingredients(audit_demo):
    ingredients = [dict(row) for row in audit_demo.ingredients]
    for ing in ingredients:
        if ing.get("allergens", "") in ("", "unknown;verify label"):
            ing["allergens"] = "none"  # illustrative label review; not cross-contact certification
    clean = Dataset(ingredients, audit_demo.dishes, audit_demo.options, audit_demo.items, demo=True)
    rows = evaluate(clean, "suya", budget_ngn=100000, protein_target_g=0,
                    avoid_allergens=["sesame"])
    assert any(row.feasible for row in rows if row.plant_only)
    assert all(row.allergen_review_complete for row in rows)


def test_unreviewed_allergen_status_disclosed_even_without_filter(audit_demo):
    rows = evaluate(audit_demo, "suya", budget_ngn=100000, protein_target_g=0)
    assert any(not row.allergen_review_complete for row in rows)


def test_duplicate_csv_header_rejected(tmp_path):
    file = tmp_path / "ingredients.csv"
    file.write_text("ingredient_id,ingredient_id\na,b\n")
    with pytest.raises(ValueError, match="duplicate CSV headers"):
        read_csv(file)


def test_extra_or_missing_csv_field_rejected(tmp_path):
    file = tmp_path / "ingredients.csv"
    file.write_text("id,name\n1,a,unexpected\n")
    with pytest.raises(ValueError, match="malformed CSV"):
        read_csv(file)
    file.write_text("id,name\n1\n")
    with pytest.raises(ValueError, match="malformed CSV"):
        read_csv(file)
