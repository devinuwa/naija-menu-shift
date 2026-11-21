"""Sourced interactive menu uses NBS and workbook figures, not placeholder prices."""
from pathlib import Path

import pytest

from menushift.engine import evaluate
from menushift.sourced_menu import build_sourced_menu

SOURCES = Path(__file__).resolve().parents[1] / "data" / "sources"


def _plants(**kwargs):
    data = build_sourced_menu(SOURCES, **kwargs)
    rows = evaluate(data, "suya", budget_ngn=500, protein_target_g=0, max_prep_minutes=300, preference="")
    return [row for row in rows if row.plant_only], [row for row in rows if not row.plant_only]


def test_hundred_gram_portion_uses_nbs_soy_price_and_sheet_water_loss():
    plants, beef = _plants(finished_g=100, wet_yield_kg_per_kg_dry=1.75, oil_cl=0)
    by_id = {row.option_id: row for row in plants}
    assert set(by_id) == {"awara_firm", "awara_pressed", "awara_frozen"}
    wet = (644 + 150) / 1.75
    assert by_id["awara_firm"].cost_ngn == pytest.approx(wet * 0.1, abs=0.02)
    assert by_id["awara_firm"].protein_g == pytest.approx(17.3, abs=0.01)
    assert by_id["awara_pressed"].cost_ngn == pytest.approx(wet * 0.125, abs=0.02)
    assert by_id["awara_pressed"].protein_g == pytest.approx(17.3 / 0.8, abs=0.02)
    assert by_id["awara_frozen"].protein_g > by_id["awara_pressed"].protein_g
    assert beef[0].cost_ngn == pytest.approx(7171.41 * 0.1, abs=0.02)
    assert all("2400" not in source for row in plants for source in row.sources)


def test_constraints_and_oil_change_the_result():
    data = build_sourced_menu(SOURCES, finished_g=100, oil_cl=0)
    blocked = evaluate(data, "suya", budget_ngn=20, protein_target_g=10, max_prep_minutes=180)
    assert all(not row.feasible for row in blocked if row.plant_only)
    soy_free = evaluate(data, "suya", budget_ngn=500, protein_target_g=10, avoid_allergens=["soy"])
    assert all(not row.feasible for row in soy_free if row.plant_only)
    high = evaluate(data, "suya", budget_ngn=500, protein_target_g=20, max_prep_minutes=180)
    feasible = {row.option_id for row in high if row.feasible}
    assert "awara_firm" not in feasible
    assert "awara_pressed" in feasible
    with_oil = build_sourced_menu(SOURCES, oil_cl=10)
    fried = next(row for row in evaluate(with_oil, "suya", budget_ngn=5000, protein_target_g=0) if row.option_id == "awara_fried")
    firm = next(row for row in evaluate(with_oil, "suya", budget_ngn=5000, protein_target_g=0) if row.option_id == "awara_firm")
    assert fried.cost_ngn == pytest.approx(firm.cost_ngn + 10 / 75 * 3263.50, abs=0.05)
    assert fried.protein_g == pytest.approx(18.8, abs=0.01)


def test_verified_files_stay_empty():
    verified = Path(__file__).resolve().parents[1] / "data" / "verified"
    for name in ("ingredients.csv", "dishes.csv", "options.csv", "option_items.csv"):
        lines = (verified / name).read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
