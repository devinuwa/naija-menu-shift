"""Conservative dietary label parsing for the Naija MenuShift research prototype.

This is a declaration filter, NEVER a substitute for verified ingredient labels,
cross-contact controls, food testing or clinical/allergy advice. No LLM runs here.
"""
from __future__ import annotations

import re
from collections.abc import Sequence

KNOWN_ALLERGENS = frozenset({
    "soy", "peanut", "wheat", "milk", "egg", "sesame", "tree nut",
    "fish", "shellfish",
})
ALIASES = {
    "soya": "soy", "soybean": "soy", "soybeans": "soy", "soya bean": "soy",
    "soya beans": "soy", "soy protein": "soy",
    "groundnut": "peanut", "groundnuts": "peanut", "peanuts": "peanut",
    "groundnut oil": "peanut", "peanut oil": "peanut",
    "gluten": "wheat", "wheat gluten": "wheat", "seitan": "wheat",
    "dairy": "milk", "casein": "milk", "lactose": "milk",
    "eggs": "egg", "egg white": "egg",
    "sesame seed": "sesame", "sesame seeds": "sesame",
    "tree nuts": "tree nut", "almond": "tree nut", "cashew": "tree nut",
    "walnut": "tree nut",
    "seafood": "shellfish", "crustacean": "shellfish",
}
UNREVIEWED = frozenset({
    "unknown", "verify label", "unreviewed", "not checked", "pending",
    "?", "tbd", "not provided", "unspecified",
})


def _normalise(raw: str) -> str:
    """Restrict labels to a simple controlled vocabulary; unexpected labels are unknown."""
    return re.sub(r"\s+", " ", raw.strip().lower().replace("_", " ").replace("-", " "))


def canonical_allergen(raw: str) -> str:
    key = _normalise(raw)
    if key in KNOWN_ALLERGENS or key == "none":
        return key
    if key in UNREVIEWED or not key:
        return "unknown"
    return ALIASES.get(key, "unknown")


def read_allergen_labels(raw: str) -> tuple[frozenset[str], bool]:
    """Return (canonical labels, incomplete review). 'none' is not a safety certification."""
    parts = [p for p in raw.split(";") if p.strip()]
    if not parts:
        return frozenset(), True
    names = {canonical_allergen(p) for p in parts}
    incomplete = "unknown" in names or ("none" in names and len(names) > 1)
    return frozenset(names - {"unknown", "none"}), incomplete


def validate_exclusions(selected: Sequence[str]) -> frozenset[str]:
    """Reject unsupported exclusions instead of silently ignoring a safety requirement."""
    if isinstance(selected, str) or len(selected) > len(KNOWN_ALLERGENS):
        raise ValueError("Allergen exclusions must be a short list of known allergens")
    result: set[str] = set()
    for label in selected:
        if not isinstance(label, str) or len(label) > 60:
            raise ValueError("Invalid allergen exclusion")
        canonical = canonical_allergen(label)
        if canonical not in KNOWN_ALLERGENS:
            raise ValueError("Unsupported allergen exclusion; request label review")
        result.add(canonical)
    return frozenset(result)


def origin_reviewed(row: dict[str, str], *, demo: bool) -> bool:
    """Missing origin evidence is NOT affirmative proof of a plant-only compound product."""
    if row.get("is_animal") == "true":
        return True
    declaration = row.get("animal_origin_reviewed", "")
    if declaration == "true":
        return True
    if declaration == "false":
        return False
    return demo  # legacy synthetic test fixtures are never approved for food service
