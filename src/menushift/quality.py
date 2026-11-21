"""Dataset audit reports used before anyone calls a demonstration 'verified'.

These checks are structural; food science, sourcing and allergen safety always
require a qualified human review. No network calls, no hidden fallback data.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from math import isfinite
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .engine import Dataset


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    record: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def audit_dataset(data: Dataset, *, as_of: date | None = None) -> list[Finding]:
    """Warnings about evidence maturity; never implies clinical or food safety certification."""
    today = as_of or datetime.now(UTC).date()
    findings: list[Finding] = []
    for ing in data.ingredients:
        ident = ing.get("ingredient_id", "<unknown>")
        price_date = ing.get("price_date", "")
        if price_date == "unknown":
            findings.append(Finding("warning", "MISSING_PRICE_DATE", ident,
                                    "Workbook quote has no documented date; not a current quotation"))
        else:
            try:
                days = (today - date.fromisoformat(price_date)).days
                if days > 30:
                    findings.append(Finding("warning", "STALE_PRICE", ident,
                                            f"Price quote is {days} days old; reconfirm locally"))
                if days < 0:
                    findings.append(Finding("warning", "FUTURE_DATE", ident,
                                            "Price quote is dated in the future"))
            except ValueError:
                findings.append(Finding("error", "INVALID_DATE", ident, "Price date is invalid"))
        if ing.get("is_animal") == "false" and ing.get("animal_origin_reviewed") != "true" and not data.demo:
            findings.append(Finding("warning", "ORIGIN_UNREVIEWED", ident,
                                    "Plant-only origin needs a reviewed declaration"))
        if "no nutrient row" in ing.get("nutrition_source", "").lower():
            findings.append(Finding("warning", "NUTRIENT_UNAVAILABLE", ident,
                                    "A zero placeholder is not measured zero nutrient content"))
        if not ing.get("allergens", "").strip():
            findings.append(Finding("warning", "UNREVIEWED_ALLERGENS", ident,
                                    "Allergen field is blank; absence is not evidence of allergen safety"))
        for field in ("price_source", "nutrition_source"):
            if ing.get(field, "").upper().startswith("SYNTHETIC"):
                findings.append(Finding("info", "SYNTHETIC_INPUT", ident, f"{field} is synthetic"))
    for op in data.options:
        if op.get("group") == "plant":
            findings.append(Finding("info", "SENSORY_UNTESTED", op.get("option_id", ""),
                                    "No sensory/texture validation is encoded; do not claim acceptance"))
    if data.demo:
        findings.append(Finding("warning", "DEMO_ONLY", "dataset",
                                "All computed outputs are demonstration values, not research evidence"))
    return findings


def numeric_health(values: dict[str, float]) -> None:
    """Simple defense-in-depth check for intermediate calculations."""
    if any(not isfinite(x) for x in values.values()):
        raise ValueError("Non-finite intermediate value; cannot compute a trustworthy recommendation")
