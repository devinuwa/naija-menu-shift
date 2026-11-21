"""Explicit conversion rules for researched food prices and tofu production costs.

The Amina workbook includes packages sold by mass and by volume. These helpers
never equate litres with kilograms or raw soybeans with finished tofu.
"""
from __future__ import annotations

import math


def _positive(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and greater than zero")
    return value


def quote_ngn_per_kg(
    price_ngn: float,
    quantity: float,
    unit: str,
    *,
    density_kg_per_litre: float | None = None,
) -> float:
    """Return comparable ₦/kg using a *documented* package mass or density.

    Package examples: 500 g of salt, 400 g of seasoning or 0.75 L of oil.
    For liquids a real density measurement/source must be supplied explicitly.
    Fuel and labour costs should not be entered as food ingredient prices.
    """
    price = _positive(price_ngn, "price_ngn")
    size = _positive(quantity, "quantity")
    unit = unit.strip().lower()
    if unit in {"kg", "kilogram", "kilograms"}:
        mass_kg = size
    elif unit in {"g", "gram", "grams"}:
        mass_kg = size / 1000.0
    elif unit in {"l", "litre", "liter", "litres", "liters"}:
        if density_kg_per_litre is None:
            raise ValueError("Liquid price conversion requires a sourced density_kg_per_litre")
        mass_kg = size * _positive(density_kg_per_litre, "density_kg_per_litre")
    elif unit in {"ml", "millilitre", "milliliter"}:
        if density_kg_per_litre is None:
            raise ValueError("Liquid price conversion requires a sourced density_kg_per_litre")
        mass_kg = size / 1000.0 * _positive(density_kg_per_litre, "density_kg_per_litre")
    else:
        raise ValueError("Unsupported sale unit; record actual package mass, not a generic 'pack'")
    return round(price / mass_kg, 4)


def tofu_manufacturing_cost_ngn_per_kg(
    *,
    raw_soy_price_ngn_per_kg: float,
    raw_soy_used_kg: float,
    measured_finished_tofu_kg: float,
    coagulant_cost_ngn: float,
    energy_cost_ngn: float,
    labour_cost_ngn: float,
    other_cost_ngn: float = 0.0,
) -> float:
    """Convert a measured soybean batch into an *estimated* tofu batch cost.

    A measured batch yield, and all other documented per-batch costs, are
    mandatory. In particular, a commodity soy price alone is never a tofu quote.
    """
    soy_price = _positive(raw_soy_price_ngn_per_kg, "raw_soy_price_ngn_per_kg")
    soy_kg = _positive(raw_soy_used_kg, "raw_soy_used_kg")
    tofu_kg = _positive(measured_finished_tofu_kg, "measured_finished_tofu_kg")
    components = (coagulant_cost_ngn, energy_cost_ngn, labour_cost_ngn, other_cost_ngn)
    if any(not math.isfinite(float(v)) or float(v) < 0 for v in components):
        raise ValueError("Production costs must be finite and nonnegative")
    return round((soy_price * soy_kg + sum(components)) / tofu_kg, 4)
