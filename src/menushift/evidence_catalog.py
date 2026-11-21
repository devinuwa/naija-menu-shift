"""Read-only food evidence catalog: reference data never implies an approved recipe."""
from __future__ import annotations

import csv
import math
import re
from datetime import date
from pathlib import Path

CURATED = Path(__file__).resolve().parents[2] / "data" / "curated"
NUTRIENT_COLUMNS = (
    "reference_id", "source", "source_url", "food_name", "food_state",
    "protein_g_per_100g", "iron_mg_per_100g", "zinc_mg_per_100g",
    "energy_kcal_per_100g", "source_method", "status",
    "local_recipe_approved", "notes",
)
PRICE_COLUMNS = (
    "month", "state", "commodity", "original_unit", "currency", "pricetype",
    "priceflag", "sample_count", "market_count",
    "median_ngn_per_reported_unit", "median_ngn_per_kg",
    "first_observation", "last_observation", "source_url", "status", "limitations",
)


def _read(path: Path, expected: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(expected):
            raise ValueError("Missing or duplicate source columns")
        rows = list(reader)
    if not rows or len(rows) > 1000:
        raise ValueError("Empty or overlarge curated evidence set")
    if any(None in row or any(value is None or "\x00" in value for value in row.values()) for row in rows):
        raise ValueError("Malformed source record")
    return rows


def _number(value: str, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}: invalid number") from exc
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{label}: invalid number")
    return number


def load_nutrition_references(folder: Path = CURATED) -> list[dict[str, str]]:
    """Reference values per 100g edible portion; never approved local recipe results."""
    rows = _read(folder / "nutrition_references.csv", NUTRIENT_COLUMNS)
    seen = set()
    for row in rows:
        key = row["reference_id"]
        if not key or key in seen or not key.startswith(("USDA:", "WAFCT2019:")):
            raise ValueError("Invalid or duplicate nutrition source ID")
        seen.add(key)
        if row["status"] != "published_reference" or row["local_recipe_approved"] != "no":
            raise ValueError("Published references must not claim kitchen approval")
        if not row["source_url"].startswith("https://") or not row["food_state"] or not row["source_method"]:
            raise ValueError("Missing source, food state or source method")
        for column in ("protein_g_per_100g", "iron_mg_per_100g", "zinc_mg_per_100g", "energy_kcal_per_100g"):
            _number(row[column], column)
    return rows


def load_wfp_price_snapshots(folder: Path = CURATED) -> list[dict[str, str]]:
    """Historical state/market aggregates; NEVER live or nationwide retail prices."""
    rows = _read(folder / "wfp_market_snapshots.csv", PRICE_COLUMNS)
    seen = set()
    for row in rows:
        key = (row["month"], row["state"], row["commodity"], row["original_unit"], row["priceflag"])
        if key in seen:
            raise ValueError("Duplicate price snapshot")
        seen.add(key)
        if row["status"] != "historical_market_aggregate" or row["priceflag"] != "aggregate":
            raise ValueError("WFP aggregate classification lost")
        if row["currency"] != "NGN" or row["pricetype"] != "Retail":
            raise ValueError("Only NGN retail snapshots allowed")
        if row["source_url"] != "https://data.humdata.org/dataset/wfp-food-prices-for-nigeria":
            raise ValueError("Unknown price source")
        if not re.fullmatch(r"\d{4}-\d{2}", row["month"]):
            raise ValueError("Invalid observation month")
        first = date.fromisoformat(row["first_observation"])
        last = date.fromisoformat(row["last_observation"])
        if first > last or first.strftime("%Y-%m") != row["month"] or last.strftime("%Y-%m") != row["month"]:
            raise ValueError("Price date mismatch")
        n = _number(row["sample_count"], "sample")
        markets = _number(row["market_count"], "markets")
        if n < 1 or markets < 1 or markets > n:
            raise ValueError("Invalid survey coverage")
        package_price = _number(row["median_ngn_per_reported_unit"], "package")
        if package_price <= 0:
            raise ValueError("Invalid price")
        mass = re.fullmatch(r"(?:(\d+(?:\.\d+)?)\s*)?(KG|G)", row["original_unit"], re.IGNORECASE)
        per_kg = row["median_ngn_per_kg"]
        if mass:
            weight = float(mass.group(1) or "1") * (1 if mass.group(2).upper() == "KG" else .001)
            if not per_kg or abs(_number(per_kg, "normalized price") - round(package_price / weight, 2)) > .03:
                raise ValueError("Incorrect mass-unit conversion")
        elif per_kg:
            raise ValueError("Non-mass unit must not have an inferred kg price")
    return rows
