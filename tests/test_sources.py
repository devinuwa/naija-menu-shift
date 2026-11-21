"""Collected quotes stay outside the verified recipe loader."""
from pathlib import Path

import pytest

from menushift.engine import load_dataset
from menushift.sources import collected_quote_gaps, load_market_prices, load_nutrition_quotes

ROOT = Path(__file__).resolve().parents[1]


def test_collected_quotes_do_not_open_verified_mode():
    prices = load_market_prices(ROOT / "data" / "sources")
    nutrients = load_nutrition_quotes(ROOT / "data" / "sources")
    assert any(row["item"].startswith("Soybeans") for row in prices)
    assert any("Beef" in row["item"] for row in prices)
    assert any("moisture" in row["source"].lower() for row in nutrients)
    assert any(row["food_item"].startswith("Reference: Beef") for row in nutrients)
    gaps = collected_quote_gaps()
    assert any("ISO price date" in gap for gap in gaps)
    assert any("does not create protein" in gap for gap in gaps)
    assert any("allergen" in gap.lower() for gap in gaps)
    with pytest.raises(ValueError, match="incomplete"):
        load_dataset(ROOT / "data" / "verified", demo=False)


def test_missing_quote_file_is_explicit(tmp_path):
    with pytest.raises(FileNotFoundError, match="missing"):
        load_market_prices(tmp_path)
