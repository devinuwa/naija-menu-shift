"""Constrained formulation exploration for the Kitchen Intelligence Studio.

This is a deterministic, explainable search over approved ingredient identities,
provisional preparation methods and *hypothetical* portion sizes. It does not
predict taste or invent ingredients, measurements or kitchen validation.

Do not describe an optimization output as a certified recipe or a trained AI model.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from .engine import Evaluation, evaluate
from .menu_pilots import DISH_LABELS, build_menu_pilots

EQUIPMENT_REQUIREMENTS = {
    "awara_firm": frozenset({"grill"}),
    "awara_pressed": frozenset({"grill", "press"}),
    "awara_frozen": frozenset({"grill", "press", "freezer"}),
    "awara_fried": frozenset({"grill", "frying_pan"}),
}

METHOD_LABELS = {
    "awara_firm": "Firm awara",
    "awara_pressed": "Pressed awara",
    "awara_frozen": "Frozen–thawed awara",
    "awara_fried": "Fried awara",
}
PREFERRED_OBJECTIVES = ("budget", "protein", "kitchen", "balanced")
INVENTORY_ITEMS = {
    "awara": "Fresh awara / tofu",
    "onion": "Onions",
    "pepper": "Fresh pepper",
    "salt": "Salt",
    "seasoning": "Seasoning (label review outstanding)",
    "oil": "Vegetable oil",
}
SOURCE_TO_INVENTORY = {
    "wet_awara": "awara", "fried_awara": "awara",
    "onion": "onion", "pepper": "pepper", "salt": "salt", "seasoning": "seasoning",
}


@dataclass(frozen=True)
class IngredientLine:
    ingredient_id: str
    name: str
    purchase_g: float
    estimated_cost_ngn: float
    estimated_protein_g: float
    source: str
    nutrition_source: str
    nutrition_state: str
    allergen_labels: str


@dataclass(frozen=True)
class RecipeCandidate:
    identifier: str
    method: str
    portion_g: float
    evaluation: Evaluation
    ingredient_lines: tuple[IngredientLine, ...]
    required_equipment: frozenset[str]
    required_inventory: frozenset[str] = frozenset()
    oil_cl: float = 0.0

    @property
    def eligible(self) -> bool:
        return self.evaluation.feasible


@dataclass(frozen=True)
class Exploration:
    candidates: tuple[RecipeCandidate, ...]
    skipped_equipment: int
    inspected: int
    skipped_ingredients: int = 0
    skipped_unverified_yaji: int = 0

    @property
    def eligible(self) -> tuple[RecipeCandidate, ...]:
        return tuple(item for item in self.candidates if item.eligible)

    @property
    def frontier(self) -> tuple[RecipeCandidate, ...]:
        """Pareto-front: minimize estimated cost/time while maximizing estimated protein."""
        feasible = self.eligible
        keep = []
        for item in feasible:
            value = item.evaluation
            if any(
                other is not item
                and other.evaluation.cost_ngn <= value.cost_ngn
                and other.evaluation.prep_minutes <= value.prep_minutes
                and other.evaluation.protein_g >= value.protein_g
                and (
                    other.evaluation.cost_ngn < value.cost_ngn
                    or other.evaluation.prep_minutes < value.prep_minutes
                    or other.evaluation.protein_g > value.protein_g
                )
                for other in feasible
            ):
                continue
            keep.append(item)
        return tuple(keep)

    def best(self, objective: str) -> RecipeCandidate | None:
        eligible = self.eligible
        if objective not in PREFERRED_OBJECTIVES:
            raise ValueError("Unknown formulation objective")
        if not eligible:
            return None
        if objective == "budget":
            return min(eligible, key=lambda x: (x.evaluation.cost_ngn, -x.evaluation.protein_g))
        if objective == "protein":
            return min(eligible, key=lambda x: (-x.evaluation.protein_g, x.evaluation.cost_ngn))
        if objective == "kitchen":
            return min(eligible, key=lambda x: (x.evaluation.prep_minutes, x.evaluation.cost_ngn))
        return max(eligible, key=lambda x: (x.evaluation.score or 0, -x.evaluation.cost_ngn))


def explore(
    sources: str | Path,
    *,
    budget_ngn: float,
    dish_id: str = "suya",
    protein_target_g: float,
    max_prep_minutes: float,
    equipment: frozenset[str],
    available_ingredients: frozenset[str] | None = None,
    portions_g: tuple[int, ...] = (80, 100, 120, 140, 160, 180, 200),
    preference: str = "",
    avoid_allergens: tuple[str, ...] = (),
    wet_yield_kg_per_kg_dry: float = 1.75,
    oil_cl: float = 1.0,
    price_shock: float = 0.0,
    prep_minutes: dict[str, float] | None = None,
    onion_g: float = 0,
    pepper_g: float = 0,
    salt_g: float = 0,
    seasoning_g: float = 0,
) -> Exploration:
    """Explore feasible methods x portion sizes without editing sourced inputs.

    Existing project data are research estimates; dry-soy-to-awara yield,
    oil absorption, processing costs, cooking time and nutrition retention
    still need actual kitchen measurements.
    """
    if dish_id not in DISH_LABELS:
        raise ValueError("Unsupported dish; use a documented pilot")
    amounts = (budget_ngn, protein_target_g, max_prep_minutes, wet_yield_kg_per_kg_dry, oil_cl,
               price_shock, onion_g, pepper_g, salt_g, seasoning_g)
    if any(not math.isfinite(float(n)) for n in amounts):
        raise ValueError("All numeric inputs must be finite")
    if not budget_ngn > 0 or protein_target_g < 0 or max_prep_minutes <= 0:
        raise ValueError("Budget and preparation time must be positive and protein target nonnegative")
    if not 0 < wet_yield_kg_per_kg_dry <= 10:
        raise ValueError("Wet-curd yield must be a positive plausible research assumption")
    if oil_cl < 0 or any(x < 0 for x in (onion_g, pepper_g, salt_g, seasoning_g)):
        raise ValueError("Ingredient inputs cannot be negative")
    if not -0.2 <= price_shock <= 0.2:
        raise ValueError("Price scenario must be between -20% and +20%")
    if len(preference) > 200:
        raise ValueError("Preference cannot exceed 200 characters")
    if not portions_g or len(portions_g) > 20 or len(set(portions_g)) != len(portions_g):
        raise ValueError("Provide one to twenty distinct portion sizes")
    if any(not isinstance(n, int) or n < 50 or n > 400 for n in portions_g):
        raise ValueError("Portions must be whole grams between 50 and 400")

    allowed = set().union(*EQUIPMENT_REQUIREMENTS.values())
    if not set(equipment) <= allowed:
        raise ValueError("Unsupported kitchen equipment")
    if available_ingredients is not None:
        unknown = set(available_ingredients) - set(INVENTORY_ITEMS)
        if unknown:
            raise ValueError(f"Unknown inventory item(s): {', '.join(sorted(unknown))}")

    found: list[RecipeCandidate] = []
    skipped = 0
    skipped_ingredients = 0
    skipped_unverified_yaji = 0
    inspected = 0
    for portion in sorted(portions_g):
        data = build_menu_pilots(
            sources, finished_g=float(portion),
            wet_yield_kg_per_kg_dry=wet_yield_kg_per_kg_dry,
            prep_minutes=prep_minutes,
            oil_cl=oil_cl, onion_g=onion_g, pepper_g=pepper_g,
            salt_g=salt_g, seasoning_g=seasoning_g,
        )
        ingredients = {row["ingredient_id"]: row for row in data.ingredients}
        recipe_items: dict[str, list[IngredientLine]] = {}
        for line in data.items:
            ingredient = ingredients[line["ingredient_id"]]
            recipe_items.setdefault(line["option_id"], []).append(
                IngredientLine(
                    ingredient_id=ingredient["ingredient_id"],
                    name=ingredient["name"],
                    purchase_g=round(float(line["purchase_g"]), 2),
                    estimated_cost_ngn=round(
                        float(line["purchase_g"]) * float(ingredient["price_ngn_per_kg"])
                        / 1000 * (1 + price_shock), 2
                    ),
                    estimated_protein_g=round(
                        float(line["purchase_g"]) * float(ingredient["protein_g_per_100g"])
                        / 100 * float(line["nutrient_retention_fraction"]), 2
                    ),
                    source=ingredient["price_source"],
                    nutrition_source=ingredient["nutrition_source"],
                    nutrition_state=ingredient["nutrition_state"],
                    allergen_labels=ingredient.get("allergens", ""),
                )
            )
        evaluated = evaluate(
            data, dish_id, budget_ngn=budget_ngn, protein_target_g=protein_target_g,
            max_prep_minutes=max_prep_minutes, preference=preference,
            avoid_allergens=avoid_allergens, price_shock=price_shock,
        )
        for result in evaluated:
            if not result.plant_only:
                continue
            inspected += 1
            method_id = result.option_id.removeprefix("jollof_")
            requirement = EQUIPMENT_REQUIREMENTS[method_id]
            if not requirement.issubset(equipment):
                skipped += 1
                continue
            # An ingredient with no inventory mapping keeps its own ID as a
            # required item: it can never be confirmed in stock, so stock
            # filtering fails closed instead of silently ignoring it.
            required_inventory = {
                SOURCE_TO_INVENTORY.get(line.ingredient_id, line.ingredient_id)
                for line in recipe_items.get(result.option_id, [])
            }
            if method_id == "awara_fried":
                required_inventory.add("oil")
            if available_ingredients is not None and not required_inventory.issubset(available_ingredients):
                skipped_ingredients += 1
                continue
            # Standard Nigerian suya yaji frequently contains groundnut/peanut,
            # but this dataset lacks a verified yaji ingredient and label.
            # A "peanut-free suya" recommendation cannot be established. The
            # pilot dishes share these awara preparations, so the unverified
            # yaji exclusion applies to every dish built from them.
            if "peanut" in {a.lower() for a in avoid_allergens}:
                skipped_unverified_yaji += 1
                continue
            found.append(RecipeCandidate(
                identifier=f"{result.option_id}@{portion}g",
                method=METHOD_LABELS[method_id],
                portion_g=float(portion),
                evaluation=result,
                ingredient_lines=tuple(recipe_items.get(result.option_id, [])),
                required_equipment=requirement,
                required_inventory=frozenset(required_inventory),
                oil_cl=oil_cl if method_id == "awara_fried" else 0.0,
            ))
    return Exploration(
        candidates=tuple(found), skipped_equipment=skipped, inspected=inspected,
        skipped_ingredients=skipped_ingredients,
        skipped_unverified_yaji=skipped_unverified_yaji,
    )
