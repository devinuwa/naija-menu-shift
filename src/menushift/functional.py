"""Functional properties of protein ingredients — cooking behaviour, honestly labelled.

WHY THIS MODULE EXISTS
----------------------
Whether a plant protein survives a cooking method is a functional question
before it is a nutrition question: a protein that cannot gel will not hold a
kebab together; one with poor water-holding dries out on the grill; one that
cannot emulsify will never make a shawarma sauce. This module records the four
functional properties the team screens on — solubility, water-holding,
emulsification and gelation — for every protein in the swap catalogue.

HONESTY CONTRACT
----------------
The functional levels are QUALITATIVE, literature-based descriptors of cooking
behaviour (High / Moderate / Low). They are not lab measurements and must
never be presented as measured values. Protein figures are per 100 g and cite
their dataset row; the single derived value (soy milk) is flagged as derived.
"""
from __future__ import annotations

from dataclasses import dataclass

LEVELS = ("Low", "Moderate", "High")


@dataclass(frozen=True)
class FunctionalProfile:
    """Qualitative cooking-behaviour descriptors (NOT lab measurements)."""

    solubility: str
    water_holding: str
    emulsification: str
    gelation: str

    def __post_init__(self) -> None:
        for field in ("solubility", "water_holding", "emulsification", "gelation"):
            if getattr(self, field) not in LEVELS:
                raise ValueError(f"{field} must be one of {LEVELS}")


@dataclass(frozen=True)
class ProteinFunction:
    id: str
    name: str
    protein_g_per_100g: float
    nutrition_source: str
    functional: FunctionalProfile
    kitchen_meaning: str
    is_animal_reference: bool = False


PROTEIN_FUNCTIONS: tuple[ProteinFunction, ...] = (
    ProteinFunction(
        id="soy_chunks",
        name="Soy chunks (TVP)",
        protein_g_per_100g=41.71,
        nutrition_source="USDA FoodData Central SR Legacy, FDC 174268 'Meat extender'",
        functional=FunctionalProfile("Low", "High", "Low", "Low"),
        kitchen_meaning=(
            "Dry chunks absorb 2-3x their weight in seasoned water, then grill, "
            "fry or stew like meat - the kebab and shawarma workhorse."
        ),
    ),
    ProteinFunction(
        id="awara",
        name="Awara (soy curd / tofu)",
        protein_g_per_100g=17.27,
        nutrition_source="USDA FoodData Central SR Legacy, FDC 172475 'Tofu, raw, firm'",
        functional=FunctionalProfile("Low", "Moderate", "Low", "High"),
        kitchen_meaning=(
            "Awara is itself a set protein gel: it slices, presses and holds "
            "its shape on the grill or in the fryer."
        ),
    ),
    ProteinFunction(
        id="soy_milk",
        name="Soy milk base",
        protein_g_per_100g=2.7,
        nutrition_source="Derived estimate from soybean composition - no direct WAFCT/USDA row; flagged derived",
        functional=FunctionalProfile("High", "Moderate", "High", "Low"),
        kitchen_meaning=(
            "Emulsifies oil into a creamy sauce - the shawarma garlic-sauce base "
            "that replaces egg. (Water-holding is nominal: this is a liquid.)"
        ),
    ),
    ProteinFunction(
        id="egusi",
        name="Egusi (melon seed)",
        protein_g_per_100g=19.5,
        nutrition_source="FAO/INFOODS WAFCT 2019, food 06_035 (melon seed)",
        functional=FunctionalProfile("Moderate", "Moderate", "High", "Moderate"),
        kitchen_meaning=(
            "Ground egusi emulsifies and thickens the soup itself - the base "
            "carries protein, not just the pieces floating in it."
        ),
    ),
    ProteinFunction(
        id="bambara",
        name="Bambara groundnut",
        protein_g_per_100g=19.5,
        nutrition_source="FAO/INFOODS WAFCT 2019, food 03_001 (bambara groundnut)",
        functional=FunctionalProfile("Moderate", "High", "Moderate", "High"),
        kitchen_meaning=(
            "Boils soft like beans and binds when mashed - it sets in okpa-style "
            "wraps and holds a pie filling together."
        ),
    ),
    ProteinFunction(
        id="mushrooms",
        name="Mushrooms",
        protein_g_per_100g=3.09,
        nutrition_source="USDA FoodData Central SR Legacy, FDC 169376 (white mushroom, UV-exposed)",
        functional=FunctionalProfile("Low", "Low", "Low", "Low"),
        kitchen_meaning=(
            "Flavour and chew, not structure or protein - pair with soy or beans "
            "for protein; mushrooms release water in the pan, so sear hot and dry."
        ),
    ),
    ProteinFunction(
        id="dawadawa",
        name="Dawadawa / soumbala (fermented locust bean)",
        protein_g_per_100g=33.1,
        nutrition_source="FAO/INFOODS WAFCT 2019, food 03_042 (dawadawa/soumbala)",
        functional=FunctionalProfile("Moderate", "Low", "Low", "Low"),
        kitchen_meaning=(
            "A fermented umami seasoning: crumble it into the base so plant "
            "dishes never taste empty - flavour first, the protein is a bonus."
        ),
    ),
    ProteinFunction(
        id="seitan",
        name="Seitan (wheat gluten)",
        protein_g_per_100g=25.0,
        nutrition_source=(
            "USDA FoodData Central SR Legacy, FDC 172449 (wheat gluten, prepared); "
            "dry vital wheat gluten is 75.2 g/100 g (FDC 168147) before hydration"
        ),
        functional=FunctionalProfile("Low", "High", "Low", "High"),
        kitchen_meaning=(
            "The chewiest, most meat-like plant protein: the gluten network "
            "itself is the structure. Simmer it in a dawadawa-rich broth and "
            "finish with yaji for a suya-style bite. ALLERGEN: seitan IS gluten "
            "- it must be excluded wherever gluten is excluded, no exceptions."
        ),
    ),
    ProteinFunction(
        id="chicken",
        name="Chicken (animal reference)",
        protein_g_per_100g=23.0,
        nutrition_source="FAO/INFOODS WAFCT 2019, food 07_033 (chicken)",
        functional=FunctionalProfile("Low", "Moderate", "Moderate", "Moderate"),
        kitchen_meaning=(
            "The benchmark: what kebab and shawarma protein costs and tastes "
            "like today - swaps are judged against it, never recommended as a plant option."
        ),
        is_animal_reference=True,
    ),
    ProteinFunction(
        id="beef",
        name="Beef (animal reference)",
        protein_g_per_100g=20.3,
        nutrition_source="FAO/INFOODS WAFCT 2019, food 07_023 (beef)",
        functional=FunctionalProfile("Low", "Moderate", "Moderate", "Moderate"),
        kitchen_meaning=(
            "The red-meat benchmark for cost and protein comparison - a "
            "reference, never a plant-based recommendation."
        ),
        is_animal_reference=True,
    ),
)

_BY_ID = {entry.id: entry for entry in PROTEIN_FUNCTIONS}


def get_protein_function(protein_id: str) -> ProteinFunction:
    """Look up one protein's functional profile; unknown ids fail loudly."""
    try:
        return _BY_ID[protein_id]
    except KeyError:
        raise ValueError(f"Unknown protein id: {protein_id!r}") from None


def plant_proteins() -> tuple[ProteinFunction, ...]:
    """The swap catalogue only - animal references are benchmarks, not options."""
    return tuple(e for e in PROTEIN_FUNCTIONS if not e.is_animal_reference)


def functional_summary(protein_id: str) -> str:
    """One-line chip text for UI surfaces, e.g. 'Gelation High · Water-holding Moderate · ...'."""
    f = get_protein_function(protein_id).functional
    return (
        f"Gelation {f.gelation} · Water-holding {f.water_holding} · "
        f"Emulsification {f.emulsification} · Solubility {f.solubility}"
    )
