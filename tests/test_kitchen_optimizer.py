"""Constrained recipe exploration regression tests."""
from pathlib import Path

import pytest

from menushift.kitchen_optimizer import explore

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "sources"
FULL_EQUIPMENT = frozenset({"grill", "press", "freezer", "frying_pan"})


def plan(**overrides):
    settings = {
        "budget_ngn": 2000.0,
        "protein_target_g": 10.0,
        "max_prep_minutes": 200.0,
        "equipment": FULL_EQUIPMENT,
        "portions_g": (100, 140, 180),
        "oil_cl": 1.0,
        "prep_minutes": {"firm": 35, "pressed": 48, "frozen": 110, "fried": 65},
    }
    settings.update(overrides)
    return explore(SOURCES, **settings)


def test_generates_distinct_portion_and_method_candidates():
    result = plan()
    assert result.inspected == 12  # four methods times three portions
    assert result.skipped_equipment == 0
    assert len({c.identifier for c in result.candidates}) == 12
    assert all(c.evaluation.plant_only for c in result.candidates)
    assert all(c.ingredient_lines for c in result.candidates)


def test_all_objectives_respect_hard_constraints():
    result = plan()
    assert result.eligible
    for objective in ("budget", "protein", "kitchen", "balanced"):
        choice = result.best(objective)
        assert choice is not None and choice.eligible
        assert choice.evaluation.cost_ngn <= 2000
        assert choice.evaluation.protein_g >= 10
        assert choice.evaluation.prep_minutes <= 200
    assert result.best("budget").evaluation.cost_ngn <= result.best("protein").evaluation.cost_ngn
    assert result.best("protein").evaluation.protein_g >= result.best("budget").evaluation.protein_g


def test_equipment_filters_are_strict():
    result = plan(equipment=frozenset({"grill"}))
    assert result.skipped_equipment == 9
    assert all(c.evaluation.option_id == "awara_firm" for c in result.candidates)
    result = plan(equipment=frozenset())
    assert result.inspected == 12
    assert result.skipped_equipment == 12
    assert not result.eligible


def test_allergen_exclusions_fail_closed():
    result = plan(avoid_allergens=("soy",))
    assert not result.eligible
    result = plan(avoid_allergens=("peanut",), seasoning_g=5)
    assert not result.eligible  # unknown seasoning labels; do not claim safe


def test_insufficient_budget_abstains_without_substituting_beef():
    result = plan(budget_ngn=1)
    assert result.best("balanced") is None
    assert not result.eligible


def test_price_shock_changes_estimated_cost_not_protein():
    baseline = plan(price_shock=0)
    raised = plan(price_shock=0.2)
    base_by_id = {c.identifier: c for c in baseline.candidates}
    high_by_id = {c.identifier: c for c in raised.candidates}
    assert set(base_by_id) == set(high_by_id)
    for key, original in base_by_id.items():
        a, b = original.evaluation, high_by_id[key].evaluation
        assert b.cost_ngn >= a.cost_ngn
        assert b.protein_g == a.protein_g


def test_frontier_members_are_nondominated():
    result = plan()
    frontier = result.frontier
    assert frontier
    assert {c.identifier for c in frontier} <= {c.identifier for c in result.eligible}
    for item in frontier:
        for other in result.eligible:
            if other is item:
                continue
            a, b = item.evaluation, other.evaluation
            assert not (
                b.cost_ngn <= a.cost_ngn and b.prep_minutes <= a.prep_minutes
                and b.protein_g >= a.protein_g
                and (b.cost_ngn < a.cost_ngn or b.prep_minutes < a.prep_minutes
                     or b.protein_g > a.protein_g)
            )


def test_invalid_inputs_rejected():
    for kwargs in (
        {"budget_ngn": float("nan")},
        {"protein_target_g": -1},
        {"wet_yield_kg_per_kg_dry": 0},
        {"equipment": frozenset({"teleporter"})},
        {"portions_g": (100, 100)},
        {"portions_g": (10,)},
        {"oil_cl": -1},
        {"price_shock": 0.5},
    ):
        with pytest.raises(ValueError):
            plan(**kwargs)


def test_unknown_objective_rejected():
    with pytest.raises(ValueError, match="objective"):
        plan().best("taste-guaranteed")
