"""Collected market and nutrition quotes that are not yet a verified recipe dataset.

The CSVs are a local copy of Amina's workbook sheets. Later NBS averages live in
`nbs_2026.csv` and are applied by `official_prices.working_market_table`. Neither file
fills `data/verified`: there is still no per-serving recipe, and moisture-adjusted
nutrient rows are notes rather than scored protein.
"""
from __future__ import annotations

import csv
from pathlib import Path

SOURCE_GAPS: tuple[str, ...] = (
    "No ISO price date is recorded. A few notes mention April/May 2026, which is not a quote date for every row.",
    "No city or market region is recorded. Figures mix national averages, retail pages, and one informal milling note.",
    "No purchase grams, finished serving weight, preparation minutes, or energy/labour split per serving.",
    "Allergen labels and animal-ingredient review are missing. A blank is not a safety clearance. Seasoning cubes are unverified.",
    "Pressed and frozen protein, iron, and zinc figures are moisture-density recalculations. Scoring does not use them, and pressing does not create protein.",
    "Oil, onion, pepper, salt, seasoning cubes, and fuel have prices but no protein, iron, or zinc rows.",
    "These quotes do not fill data/verified and cannot run research mode.",
)


def sources_dir(root: str | Path | None = None) -> Path:
    if root is None:
        return Path(__file__).resolve().parents[2] / "data" / "sources"
    return Path(root)


def _read(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Collected quote file is missing: {path.name}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"{path.name} has headers but no quote rows")
    return rows


def load_market_prices(folder: str | Path | None = None) -> list[dict[str, str]]:
    return _read(sources_dir(folder) / "market_prices.csv")


def load_nutrition_quotes(folder: str | Path | None = None) -> list[dict[str, str]]:
    return _read(sources_dir(folder) / "nutrition_per_100g.csv")


def collected_quote_gaps() -> tuple[str, ...]:
    """Fixed limitations. Presence of a spreadsheet number does not close any gap."""
    return SOURCE_GAPS
