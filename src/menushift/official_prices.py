"""Workbook quotes with later 2026 NBS averages applied where a release matches.

The studio uses this table. It does not fill data/verified and it does not price a
serving: purchase grams, finished weight, and preparation time are still unmeasured.
"""
from __future__ import annotations

import csv
from pathlib import Path

from .pricing import quote_ngn_per_kg
from .sources import load_market_prices, load_nutrition_quotes, sources_dir

WORKBOOK_LIMITS: dict[str, str] = {
    "Soybeans (Raw)": (
        "Mansa Markets exchange benchmark for raw soybeans. Not an NBS food-watch row "
        "and not a price for purchased awara."
    ),
    "Pepper (Fresh / Chili)": (
        "Not listed in the May 2026 Selected Food Price Watch table retrieved on 14 November 2026. "
        "The workbook figure is kept."
    ),
    "Seasoning Cubes": (
        "Retail pack price from the workbook. The package label was not reviewed for animal ingredients "
        "or allergens. A blank is not a clearance."
    ),
    "Iodized Table Salt": "Retail pack price from the workbook. No NBS row was matched for this pack.",
    "Local Grinding / Milling": (
        "Informal vendor note per 1 kg batch. Not an NBS price and not a measured batch energy cost."
    ),
}

SERVING_GAPS: tuple[str, ...] = (
    "No purchased grams, finished serving weight, or preparation minutes are in the workbook.",
    "Raw soybean naira per kilogram is not a finished-awara price. A yield range in a note is not a measured batch.",
    "Pressed and frozen protein, iron, and zinc figures are moisture recalculations. Pressing does not create protein.",
    "Raw boneless-beef price and cooked-beef nutrients are different food states and are not combined into one serving.",
    "Vegetable oil stays priced per 75 cl. No sourced density is used to turn that bottle into naira per kilogram.",
    "Allergen and animal-ingredient review is incomplete. Seasoning cubes stay unverified.",
    "These rows do not fill data/verified. The synthetic demonstration prices are not used.",
)


def _read(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Official price file is missing: {path.name}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"{path.name} has headers but no NBS rows")
    return rows


def load_nbs_prices(folder: str | Path | None = None) -> list[dict[str, str]]:
    return _read(sources_dir(folder) / "nbs_2026.csv")


def _comparable_per_kg(price_ngn: str, unit: str) -> str:
    """Package arithmetic for mass sales only. Liquids and fuel stay blank."""
    unit_key = unit.strip().lower()
    price = float(price_ngn)
    if unit_key == "1 kg":
        return f"{price:.2f}"
    if unit_key == "500 g":
        return f"{quote_ngn_per_kg(price, 500, 'g'):.2f}"
    if unit_key == "1 pack (100 x 4g)":
        return f"{quote_ngn_per_kg(price, 400, 'g'):.2f}"
    return ""


def working_market_table(folder: str | Path | None = None) -> list[dict[str, str]]:
    """Sheet order, with a later NBS release standing in for the matching workbook row."""
    sheet = load_market_prices(folder)
    official = load_nbs_prices(folder)
    by_item: dict[str, list[dict[str, str]]] = {}
    for row in official:
        by_item.setdefault(row["workbook_item"], []).append(row)
    working: list[dict[str, str]] = []
    for row in sheet:
        replacements = by_item.get(row["item"], [])
        if replacements:
            for item in replacements:
                working.append(
                    {
                        "item": item["display_item"],
                        "category": row["category"],
                        "unit": item["unit"],
                        "price_ngn": item["price_ngn"],
                        "period": item["period"],
                        "basis": item["release"],
                        "comparable_ngn_per_kg": _comparable_per_kg(item["price_ngn"], item["unit"]),
                        "workbook_price_ngn": item["workbook_price_ngn"],
                        "source": item["source_url"],
                        "limitation": item["limitation"],
                    }
                )
            continue
        working.append(
            {
                "item": row["item"],
                "category": row["category"],
                "unit": row["standard_unit"],
                "price_ngn": row["estimated_price_ngn"],
                "period": "",
                "basis": "Workbook quote",
                "comparable_ngn_per_kg": _comparable_per_kg(
                    row["estimated_price_ngn"], row["standard_unit"]
                ),
                "workbook_price_ngn": row["estimated_price_ngn"],
                "source": row["source"],
                "limitation": WORKBOOK_LIMITS.get(
                    row["item"], "No later NBS row was matched. The workbook figure is kept."
                ),
            }
        )
    return working


def preparation_methods(folder: str | Path | None = None) -> list[dict[str, str]]:
    """Four awara states plus the cooked-beef reference, per 100 g, from the workbook."""
    methods: list[dict[str, str]] = []
    for row in load_nutrition_quotes(folder):
        source = row["source"]
        modelled = "calculated" in source.lower() or "moisture" in source.lower()
        methods.append(
            {
                "food_item": row["food_item"],
                "serving_basis": row["serving_basis"],
                "protein_g": row["protein_g"],
                "iron_mg": row["iron_mg"],
                "zinc_mg": row["zinc_mg"],
                "measurement": "Moisture recalculation" if modelled else "Published reference",
                "source": source,
                "notes": row["moisture_notes"],
            }
        )
    return methods
