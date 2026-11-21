"""No fictitious chicken/rice cost in the second, partial menu pilot."""
from pathlib import Path

import pytest

from menushift.engine import evaluate
from menushift.kitchen_optimizer import explore
from menushift.menu_pilots import DISH_LABELS, DISH_SCOPE, build_menu_pilots

SOURCES = Path(__file__).resolve().parents[1] / "data" / "sources"


def test_both_dishes_have_distinct_option_ids():
    data = build_menu_pilots(SOURCES, finished_g=100, oil_cl=1)
    assert len(data.dishes) == 2
    assert set(DISH_LABELS) == {d["dish_id"] for d in data.dishes}
    assert "PARTIAL" in DISH_SCOPE["jollof_side"]
    assert len([o for o in data.options if o["dish_id"] == "jollof_side"]) == 4
    assert all(o["group"] == "plant" for o in data.options if o["dish_id"] == "jollof_side")


def test_jollof_protein_side_is_explicitly_a_shared_calculation():
    data = build_menu_pilots(SOURCES, finished_g=100, oil_cl=1)
    suya = evaluate(data, "suya", budget_ngn=10000, protein_target_g=0)
    jollof = evaluate(data, "jollof_side", budget_ngn=10000, protein_target_g=0)
    source = {o.option_id: o for o in suya if o.plant_only}
    assert len(jollof) == 4
    for row in jollof:
        original = row.option_id.removeprefix("jollof_")
        assert row.plant_only
        assert row.cost_ngn == source[original].cost_ngn
        assert row.protein_g == source[original].protein_g


def test_second_dish_rejects_soy_allergen():
    data = build_menu_pilots(SOURCES)
    rows = evaluate(data, "jollof_side", budget_ngn=10000, protein_target_g=0, avoid_allergens=["soy"])
    assert not any(row.feasible for row in rows)


def test_equipment_constraints_apply_in_second_dish():
    result = explore(
        SOURCES, dish_id="jollof_side", budget_ngn=10000, protein_target_g=0,
        max_prep_minutes=200, equipment=frozenset({"grill"}),
        portions_g=(100,), oil_cl=1,
    )
    assert result.inspected == 4
    assert len(result.candidates) == 1
    assert result.candidates[0].evaluation.dish_id == "jollof_side"


def test_other_unimplemented_dishes_rejected():
    with pytest.raises(ValueError, match="Unsupported dish"):
        explore(
            SOURCES, dish_id="egusi", budget_ngn=10000, protein_target_g=0,
            max_prep_minutes=200, equipment=frozenset({"grill"}),
        )


def test_no_fabricated_kitchen_trials():
    path = Path(__file__).resolve().parents[1] / "data" / "evaluation" / "kitchen_trials.csv"
    assert len(path.read_text(encoding="utf-8").strip().splitlines()) == 1
