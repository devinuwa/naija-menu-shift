"""The studio price book uses later NBS averages and does not reopen demo ranking."""
from pathlib import Path

from menushift.engine import load_dataset
from menushift.official_prices import preparation_methods, working_market_table

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "sources"


def _row(item: str) -> dict[str, str]:
    matches = [row for row in working_market_table(SOURCES) if row["item"] == item]
    assert len(matches) == 1
    return matches[0]


def test_later_nbs_averages_replace_rounded_workbook_figures():
    beef = _row("Beef boneless raw")
    onions = _row("Onions fresh")
    oil = _row("Vegetable oil")
    kerosene = _row("Household kerosene")
    assert beef["price_ngn"] == "7171.41"
    assert beef["workbook_price_ngn"] == "7171"
    assert beef["period"] == "2026-05"
    assert onions["price_ngn"] == "1180.01"
    assert onions["workbook_price_ngn"] == "1164"
    assert oil["price_ngn"] == "3263.50"
    assert oil["unit"] == "75 cl"
    assert kerosene["price_ngn"] == "2971.94"
    assert kerosene["workbook_price_ngn"] == "2977"
    assert "SYNTHETIC" not in " ".join(beef.values()).upper()


def test_cooking_gas_uses_cylinder_refills_not_the_workbook_per_kg():
    table = working_market_table(SOURCES)
    gas = [row for row in table if row["item"].startswith("Cooking gas")]
    assert [row["price_ngn"] for row in gas] == ["8706.93", "22382.20"]
    assert {row["workbook_price_ngn"] for row in gas} == {"1620"}
    assert all(row["comparable_ngn_per_kg"] == "" for row in gas)


def test_unmatched_workbook_rows_stay_and_soy_is_not_awara():
    pepper = _row("Pepper (Fresh / Chili)")
    soy = _row("Soybeans (Raw)")
    salt = _row("Iodized Table Salt")
    assert pepper["basis"] == "Workbook quote"
    assert pepper["price_ngn"] == "1178"
    assert "May 2026" in pepper["limitation"]
    assert soy["price_ngn"] == "644"
    assert "not a price for purchased awara" in soy["limitation"]
    assert salt["comparable_ngn_per_kg"] == "350.00"


def test_four_awara_methods_keep_modelled_rows_out_of_verified_mode():
    methods = preparation_methods(SOURCES)
    names = [row["food_item"] for row in methods]
    assert sum(name.startswith("Method") for name in names) == 4
    assert names[-1].startswith("Reference: Beef")
    modelled = {row["food_item"] for row in methods if row["measurement"] == "Moisture recalculation"}
    assert any(name.startswith("Method 2") for name in modelled)
    assert any(name.startswith("Method 3") for name in modelled)
    firm = next(row for row in methods if row["food_item"].startswith("Method 1"))
    assert firm["measurement"] == "Published reference"
    assert firm["protein_g"] == "17.3"


def test_sourced_prices_do_not_open_verified_ranking_or_the_demo_app():
    try:
        load_dataset(ROOT / "data" / "verified", demo=False)
    except ValueError as exc:
        assert "incomplete" in str(exc)
    else:
        raise AssertionError("verified mode must stay closed")
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "data/demo" not in app
    assert "load_dataset" not in app
