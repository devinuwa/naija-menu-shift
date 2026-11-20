"""Hospital food-service mode: diversify a documented hospital menu.

The menu is the only peer-reviewed extraction of a real Nigerian hospital
kitchen menu the team could find: the therapeutic diet kitchen at UNTH Enugu
(Maduforo et al., Pakistan Journal of Nutrition 15(2):104-111, 2016). Only two
of its 14 items carry a documented animal protein - fish and meat. This module
runs those two dishes through the existing recommendation engine
(``menushift.engine.evaluate``) with hospital constraint presets and returns
ranked plant-protein alternatives for a dietitian to review.

The same machinery also powers an ANY-DISH mode (``suggest_for_any_dish``):
hospital staff type any dish they serve, name the animal protein and portion
in it today and the cooking method, and get the same gated ranking. Original
-side baselines are shown only where the project data carries a cited value
(beef and chicken protein; beef price) - never invented for fish, goat or egg.

THIS IS DECISION SUPPORT, NOT A SERVED MENU AND NOT CLINICAL GUIDANCE.
Every output carries ``requires_dietitian_signoff=True``. Prices and prep
times are planning estimates with their provenance recorded in
``data/hospital/protein_prices.csv``; see ``data/hospital/README.md`` for the
full honesty contract (2016 menu, currency unverified, derived prices flagged,
no invented dishes, no invented menu cycle, no meal split).

A CONDITIONS registry maps a patient's condition (cardiovascular,
hypertension, kidney, diabetes) to one of the documented presets and
attaches the team's cited evidence together with its limits;
``build_condition_menu`` composes a draft condition menu from the 14
documented items. Conditions change constraints and attach evidence -
they never turn the output into a prescription.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .engine import Dataset, evaluate, read_csv, validate_dataset
from .functional import (
    FunctionalProfile,
    ProteinFunction,
    get_protein_function,
    plant_proteins,
)

ROOT = Path(__file__).resolve().parents[2]
HOSPITAL_DATA = ROOT / "data" / "hospital"
MENU_PATH = HOSPITAL_DATA / "unth_menu.csv"
PRICES_PATH = HOSPITAL_DATA / "protein_prices.csv"
DEFAULT_FEEDBACK_PATH = ROOT / "data" / "evidence_intake" / "hospital_feedback.csv"

MENU_SOURCE = (
    "Maduforo et al., Pakistan Journal of Nutrition 15(2):104-111, 2016 - "
    "therapeutic diet kitchen menu, UNTH Enugu (oncology high-calorie "
    "high-protein diet); menu year 2016, current use unverified"
)
UPTH_SOURCE = (
    "UPTH dietetics placement report (SIWES, Oct 2024) - modified-diet definitions"
)
PORTIONS_G = (100, 150, 200)
DEFAULT_BUDGET_NGN = 1500.0
DEFAULT_FLOOR_G = 20.0
DEFAULT_MAX_PREP_MINUTES = 180.0
SIGNOFF_NOTE = (
    "Decision support only - a dietitian must approve any change before it "
    "is served to patients."
)


# --------------------------------------------------------------------------
# The documented menu
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class HospitalDish:
    item_id: str
    name: str
    documented_animal_protein: str  # "" when the source names none
    protein_status: str  # documented_animal | already_plant_based | unspecified | none_documented
    already_plant_based: bool
    notes: str
    source: str


def load_unth_menu(path: str | Path | None = None) -> tuple[HospitalDish, ...]:
    """Load the 14 documented UNTH therapeutic-kitchen items, verbatim."""
    rows = read_csv(path or MENU_PATH)
    dishes = []
    for row in rows:
        dishes.append(HospitalDish(
            item_id=row["item_id"].strip(),
            name=row["name"].strip(),
            documented_animal_protein=row["documented_animal_protein"].strip(),
            protein_status=row["protein_status"].strip(),
            already_plant_based=row["already_plant_based"].strip().lower() == "true",
            notes=row["notes"].strip(),
            source=row["source"].strip(),
        ))
    return tuple(dishes)


def get_dish(menu: tuple[HospitalDish, ...], dish_ref: str) -> HospitalDish:
    """Find a menu item by item_id or display name (case-insensitive)."""
    key = dish_ref.strip().lower()
    for dish in menu:
        if dish.item_id.lower() == key or dish.name.lower() == key:
            return dish
    raise ValueError(f"Unknown hospital menu item: {dish_ref!r}")


# --------------------------------------------------------------------------
# Therapeutic presets - constraint bundles with cited sources
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class TherapeuticPreset:
    id: str
    label: str
    source: str
    protein_floor_g: float | None  # None -> caller/default floor applies
    protein_cap_g_per_meal: float | None  # enforced by this module, with reasons
    notes: tuple[str, ...]


THERAPEUTIC_PRESETS: dict[str, TherapeuticPreset] = {
    "standard": TherapeuticPreset(
        id="standard",
        label="Standard (no therapeutic modification)",
        source="No therapeutic modification selected.",
        protein_floor_g=None,
        protein_cap_g_per_meal=None,
        notes=(
            ("The protein floor here is a working tool parameter for the "
             "dietitian to set - it is not a clinical guideline."),
        ),
    ),
    "high_protein": TherapeuticPreset(
        id="high_protein",
        label="High protein (UPTH: 1.5-2.0 g/kg/day)",
        source=UPTH_SOURCE,
        protein_floor_g=35.0,
        protein_cap_g_per_meal=None,
        notes=(
            ("Arithmetic on the cited range, not clinical guidance: 1.5 g/kg "
             "at a 70 kg reference adult = 105 g/day; over 3 meals (the "
             "documented Nigerian hospital pattern) the per-meal floor is 35 g. "
             "The dietitian sets the real target for each patient."),
        ),
    ),
    "low_protein": TherapeuticPreset(
        id="low_protein",
        label="Low protein (UPTH: 20-60 g/day - kidney/liver)",
        source=UPTH_SOURCE,
        protein_floor_g=0.0,
        protein_cap_g_per_meal=20.0,
        notes=(
            ("Arithmetic on the cited range, not clinical guidance: the cap "
             "uses the upper bound, 60 g/day over 3 meals = 20 g per meal. "
             "Portions above the cap are excluded with the reason shown."),
        ),
    ),
    "low_sodium": TherapeuticPreset(
        id="low_sodium",
        label="Low sodium (UPTH: heart, hypertension, oedema, kidney failure)",
        source=UPTH_SOURCE,
        protein_floor_g=None,
        protein_cap_g_per_meal=None,
        notes=(
            ("LIMITATION: the engine's datasets contain no sodium values, so "
             "this preset applies no numeric sodium filter and invents none. "
             "Candidates are unprocessed single ingredients with no added salt "
             "in this model; actual sodium depends on kitchen preparation and "
             "must be confirmed by the dietitian."),
        ),
    ),
}


def get_preset(preset_id: str) -> TherapeuticPreset:
    try:
        return THERAPEUTIC_PRESETS[preset_id]
    except KeyError:
        raise ValueError(f"Unknown therapeutic preset: {preset_id!r}") from None


# --------------------------------------------------------------------------
# Engine dataset built from the functional catalogue + hospital price table
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class ProteinPrice:
    protein_id: str
    role: str  # candidate | adjunct | reference
    price_ngn_per_kg: float
    price_derived: bool
    price_date: str
    price_basis: str
    prep_minutes: float
    allergens: str


def load_protein_prices(path: str | Path | None = None) -> dict[str, ProteinPrice]:
    rows = read_csv(path or PRICES_PATH)
    prices = {}
    for row in rows:
        entry = ProteinPrice(
            protein_id=row["protein_id"].strip(),
            role=row["role"].strip(),
            price_ngn_per_kg=float(row["price_ngn_per_kg"]),
            price_derived=row["price_derived"].strip().lower() == "true",
            price_date=row["price_date"].strip(),
            price_basis=row["price_basis"].strip(),
            prep_minutes=float(row["prep_minutes"]),
            allergens=row["allergens"].strip(),
        )
        prices[entry.protein_id] = entry
    return prices


def _dish_dataset_id(dish: HospitalDish) -> str:
    return f"unth_{dish.item_id}"


def _candidate_ingredient_rows(
    prices: dict[str, ProteinPrice],
) -> tuple[list[dict[str, str]], list[ProteinFunction]]:
    """Engine ingredient rows for the ranked plant candidates.

    Dawadawa is excluded by role: it is a seasoning used at 5-10 g per
    serving, not a main protein portion, so it is never a ranked candidate.
    """
    candidates = [p for p in plant_proteins() if prices[p.id].role == "candidate"]
    rows: list[dict[str, str]] = []
    for protein in candidates:
        price = prices[protein.id]
        rows.append({
            "ingredient_id": protein.id,
            "name": protein.name,
            "is_animal": "false",
            "price_ngn_per_kg": str(price.price_ngn_per_kg),
            "protein_g_per_100g": str(protein.protein_g_per_100g),
            "iron_mg_per_100g": "0",
            "zinc_mg_per_100g": "0",
            "price_source": price.price_basis,
            "price_date": price.price_date,
            "price_region": "Nigeria (see price basis)",
            "nutrition_source": (
                f"{protein.nutrition_source}; protein row only - "
                "no nutrient row for iron/zinc in the hospital module"
            ),
            "nutrition_state": "as purchased (planning model)",
            "allergens": price.allergens,
            # Single-ingredient plant foods; identity is the cited dataset row.
            "animal_origin_reviewed": "true",
        })
    return rows, candidates


def _beef_ingredient_row(prices: dict[str, ProteinPrice]) -> dict[str, str]:
    beef = get_protein_function("beef")
    beef_price = prices["beef"]
    return {
        "ingredient_id": "beef",
        "name": beef.name,
        "is_animal": "true",
        "price_ngn_per_kg": str(beef_price.price_ngn_per_kg),
        "protein_g_per_100g": str(beef.protein_g_per_100g),
        "iron_mg_per_100g": "0",
        "zinc_mg_per_100g": "0",
        "price_source": beef_price.price_basis,
        "price_date": beef_price.price_date,
        "price_region": "Nigeria (see price basis)",
        "nutrition_source": (
            f"{beef.nutrition_source}; protein row only - "
            "no nutrient row for iron/zinc in the hospital module"
        ),
        "nutrition_state": "as purchased (planning model)",
        "allergens": beef_price.allergens,
        "animal_origin_reviewed": "true",
    }


def _candidate_option_rows(
    dish_id: str,
    candidates: list[ProteinFunction],
    prices: dict[str, ProteinPrice],
    portions: tuple[float, ...],
    method_notes: str,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    options: list[dict[str, str]] = []
    items: list[dict[str, str]] = []
    for protein in candidates:
        price = prices[protein.id]
        for portion in portions:
            option_id = f"{dish_id}_{protein.id}_{portion:g}g"
            options.append({
                "option_id": option_id,
                "dish_id": dish_id,
                "name": f"{protein.name} - {portion:g} g portion",
                "group": "plant",
                "energy_cost_ngn": "0",
                "labour_cost_ngn": "0",
                "other_cost_ngn": "0",
                "prep_minutes": str(price.prep_minutes),
                "finished_weight_g": str(portion),
                "texture_tags": "",
                "method_notes": method_notes,
            })
            items.append({
                "option_id": option_id,
                "ingredient_id": protein.id,
                "purchase_g": str(portion),
                "nutrient_retention_fraction": "1",
            })
    return options, items


def build_hospital_dataset(
    menu: tuple[HospitalDish, ...] | None = None,
    prices: dict[str, ProteinPrice] | None = None,
) -> Dataset:
    """Build an engine Dataset for the two transformable UNTH dishes.

    Candidates are the plant proteins from ``functional.py`` at 100/150/200 g
    planning portions. Dawadawa is excluded from candidates by role: it is a
    seasoning used at 5-10 g per serving, not a main protein portion. The meat
    dish also gets a beef *reference* option (comparison only, never a plant
    recommendation); the fish dish gets none, because no cited fish price or
    protein-density row exists in the project data.
    """
    menu = menu or load_unth_menu()
    prices = prices or load_protein_prices()
    transformable = [d for d in menu if d.protein_status == "documented_animal"]
    ingredients, candidates = _candidate_ingredient_rows(prices)
    ingredients.append(_beef_ingredient_row(prices))
    beef_price = prices["beef"]

    dishes: list[dict[str, str]] = []
    options: list[dict[str, str]] = []
    items: list[dict[str, str]] = []
    for dish in transformable:
        dish_id = _dish_dataset_id(dish)
        dishes.append({"dish_id": dish_id, "name": dish.name})
        dish_options, dish_items = _candidate_option_rows(
            dish_id, candidates, prices, PORTIONS_G,
            "Hospital planning model: single-protein portion",
        )
        options.extend(dish_options)
        items.extend(dish_items)
        if dish.documented_animal_protein == "meat":
            for portion in PORTIONS_G:
                option_id = f"{dish_id}_beef_{portion}g"
                options.append({
                    "option_id": option_id,
                    "dish_id": dish_id,
                    "name": f"Meat as documented (beef reference) - {portion} g portion",
                    "group": "reference",
                    "energy_cost_ngn": "0",
                    "labour_cost_ngn": "0",
                    "other_cost_ngn": "0",
                    "prep_minutes": str(beef_price.prep_minutes),
                    "finished_weight_g": str(portion),
                    "texture_tags": "",
                    "method_notes": "Comparison reference only - never a plant recommendation",
                })
                items.append({
                    "option_id": option_id,
                    "ingredient_id": "beef",
                    "purchase_g": str(portion),
                    "nutrient_retention_fraction": "1",
                })
    data = Dataset(ingredients=ingredients, dishes=dishes, options=options,
                   items=items, demo=False, verified_input=False)
    validate_dataset(data)
    return data


ANY_DISH_DATASET_ID = "any_dish_custom"


def build_any_dish_dataset(
    prices: dict[str, ProteinPrice] | None = None,
    portions: tuple[float, ...] = PORTIONS_G,
) -> Dataset:
    """Build an engine Dataset for one staff-entered dish (any-dish mode).

    Same candidate catalogue, prices and planning portions as the UNTH
    dataset; the dish itself is whatever the kitchen typed. No reference
    option is built: original-side baselines come from ``build_baseline``,
    which only uses cited catalogue values.
    """
    prices = prices or load_protein_prices()
    ingredients, candidates = _candidate_ingredient_rows(prices)
    options, items = _candidate_option_rows(
        ANY_DISH_DATASET_ID, candidates, prices, portions,
        "Hospital any-dish planning model: single-protein portion",
    )
    data = Dataset(
        ingredients=ingredients,
        dishes=[{"dish_id": ANY_DISH_DATASET_ID,
                 "name": "Custom dish (hospital any-dish mode)"}],
        options=options, items=items, demo=False, verified_input=False,
    )
    validate_dataset(data)
    return data


# --------------------------------------------------------------------------
# Method-survival screen - the product's rule table, reused
# --------------------------------------------------------------------------
# The requirements for grill / fry / boil / soup are the same rule table the
# product's transform engine uses (METHOD_REQUIREMENTS in the HackSprout
# transform studio): per cooking method, which functional properties matter
# and the minimum level, each with its food-science reason. Steam is added
# here in the same style for hospital steaming. The functional profiles are
# QUALITATIVE literature-based descriptors (see functional.py), so this is a
# rule-based screening model over qualitative data - not a lab-validated
# simulation - and its reasoning is shown wherever its output is used.

_LEVEL_NUM = {"Low": 0, "Moderate": 1, "High": 2}
_LEVEL_NAME = {0: "Low", 1: "Moderate", 2: "High"}
_PROPERTY_LABEL = {
    "solubility": "solubility",
    "water_holding": "water-holding",
    "emulsification": "emulsification",
    "gelation": "gelation",
}


@dataclass(frozen=True)
class PropertyThreshold:
    property: str  # key on FunctionalProfile
    min_level: int | None = None
    max_level: int | None = None


@dataclass(frozen=True)
class MethodRequirement:
    label: str
    alternatives: tuple[PropertyThreshold, ...]  # passes if ANY is met
    reason: str


METHOD_REQUIREMENTS: dict[str, tuple[MethodRequirement, ...]] = {
    "grill": (
        MethodRequirement(
            "Structure on the skewer",
            (PropertyThreshold("gelation", min_level=1),
             PropertyThreshold("water_holding", min_level=2)),
            ("over open heat a piece must hold together on the skewer - it "
             "needs a set gel structure (gelation >= Moderate) or exceptional "
             "water-holding (High) that keeps the formed piece intact"),
        ),
        MethodRequirement(
            "Stays juicy under dry heat",
            (PropertyThreshold("water_holding", min_level=1),),
            ("grilling drives moisture off the surface, so water-holding of "
             "at least Moderate keeps the piece from drying into leather"),
        ),
    ),
    "fry": (
        MethodRequirement(
            "Holds shape in hot oil",
            (PropertyThreshold("gelation", min_level=1),
             PropertyThreshold("water_holding", min_level=2)),
            ("a fried piece must arrive pre-formed or set in the pan - "
             "gelation >= Moderate gives batter adhesion and structure; very "
             "high water-holding marks a hydrated, formed chunk that fries "
             "as one piece"),
        ),
        MethodRequirement(
            "Moist inside, crisp outside",
            (PropertyThreshold("water_holding", min_level=1),),
            ("water-holding of at least Moderate lets the surface crisp "
             "while the inside stays moist instead of hollowing out"),
        ),
    ),
    "boil": (
        MethodRequirement(
            "Does not disintegrate in the pot",
            (PropertyThreshold("gelation", min_level=1),
             PropertyThreshold("water_holding", min_level=2)),
            ("boiling agitates and leaches - the protein must be a set gel "
             "(gelation >= Moderate) or a formed, highly water-holding piece "
             "to come out of the pot as pieces, not cloud"),
        ),
        MethodRequirement(
            "Does not dissolve away",
            (PropertyThreshold("solubility", max_level=1),
             PropertyThreshold("emulsification", min_level=2)),
            ("a highly soluble protein disperses into the cooking liquid; "
             "that is only acceptable when it is there to emulsify the dish "
             "(emulsification High), not when pieces are expected"),
        ),
    ),
    "soup": (
        MethodRequirement(
            "Gives the soup body, or holds as pieces",
            (PropertyThreshold("emulsification", min_level=1),
             PropertyThreshold("gelation", min_level=1),
             PropertyThreshold("water_holding", min_level=2)),
            ("a soup protein must either emulsify and thicken the broth, "
             "set into pieces that hold in hot liquid, or arrive as a formed "
             "water-holding chunk - otherwise the soup is water with "
             "flavouring"),
        ),
        MethodRequirement(
            "Does not dissolve away",
            (PropertyThreshold("solubility", max_level=1),
             PropertyThreshold("emulsification", min_level=1)),
            ("in a served soup the protein should still be identifiable - "
             "high solubility is acceptable only when the protein's job is "
             "to emulsify the broth itself"),
        ),
    ),
    "steam": (
        MethodRequirement(
            "Holds together in moist heat",
            (PropertyThreshold("gelation", min_level=1),
             PropertyThreshold("water_holding", min_level=2)),
            ("steaming surrounds the piece with condensing moisture - it "
             "must be a set gel (gelation >= Moderate) or a formed, highly "
             "water-holding piece, or it slumps and breaks apart in the "
             "steamer"),
        ),
        MethodRequirement(
            "Does not dissolve away",
            (PropertyThreshold("solubility", max_level=1),
             PropertyThreshold("emulsification", min_level=2)),
            ("condensing steam leaches soluble protein away as drip; a "
             "highly soluble protein is acceptable only when its job is to "
             "emulsify the dish itself (emulsification High)"),
        ),
    ),
}

COOKING_METHODS = tuple(METHOD_REQUIREMENTS)
METHOD_LABELS = {
    "grill": "Grill",
    "fry": "Fry",
    "boil": "Boil",
    "soup": "Soup / stew pot",
    "steam": "Steam",
}


def _describe_threshold(threshold: PropertyThreshold) -> str:
    label = _PROPERTY_LABEL[threshold.property]
    if threshold.max_level is not None and threshold.min_level is None:
        return f"{label} <= {_LEVEL_NAME[threshold.max_level]}"
    return f"{label} >= {_LEVEL_NAME[threshold.min_level or 0]}"


def predict_method_survival(
    profile: FunctionalProfile, method: str,
) -> tuple[bool, tuple[str, ...]]:
    """Screen one functional profile against a cooking method's requirements.

    Rule-based screening over qualitative descriptors - see the section
    header. Returns (survives, one reasoning line per requirement).
    """
    if method not in METHOD_REQUIREMENTS:
        raise ValueError(f"Unknown cooking method: {method!r}")
    reasons: list[str] = []
    survives = True
    for req in METHOD_REQUIREMENTS[method]:
        met = None
        for alt in req.alternatives:
            level = _LEVEL_NUM[getattr(profile, alt.property)]
            if level >= (alt.min_level or 0) and level <= (
                alt.max_level if alt.max_level is not None else 2
            ):
                met = alt
                break
        if met is not None:
            level = getattr(profile, met.property)
            reasons.append(
                f"{req.label}: {_PROPERTY_LABEL[met.property]} is {level} "
                f"- {req.reason}."
            )
        else:
            survives = False
            needed = " or ".join(
                _describe_threshold(a) for a in req.alternatives)
            actual = ", ".join(
                f"{_PROPERTY_LABEL[a.property]} {getattr(profile, a.property)}"
                for a in req.alternatives)
            reasons.append(
                f"{req.label}: FAILED - needs {needed}, because {req.reason}; "
                f"this protein has {actual}."
            )
    return survives, tuple(reasons)


# --------------------------------------------------------------------------
# Recommendations
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class HospitalAlternative:
    protein_id: str
    name: str
    portion_g: float
    protein_g: float
    cost_ngn: float
    prep_minutes: float
    allergens: tuple[str, ...]
    functional: FunctionalProfile
    kitchen_meaning: str
    score: float | None
    reasons: tuple[str, ...]
    price_basis: str
    price_derived: bool
    nutrition_source: str


@dataclass(frozen=True)
class RejectedAlternative:
    protein_id: str
    name: str
    portion_g: float
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class HospitalReference:
    """The dish as documented, costed from the beef reference (meat dish only)."""

    name: str
    portion_g: float
    protein_g: float
    cost_ngn: float
    prep_minutes: float
    note: str


@dataclass(frozen=True)
class HospitalRecommendation:
    dish: HospitalDish
    preset: TherapeuticPreset
    status: str  # ok | already_plant_based | protein_unspecified | no_documented_animal_protein
    alternatives: tuple[HospitalAlternative, ...]
    rejected: tuple[RejectedAlternative, ...]
    reference: HospitalReference | None
    notes: tuple[str, ...]
    evidence_warnings: tuple[str, ...]
    requires_dietitian_signoff: bool = True
    signoff_note: str = SIGNOFF_NOTE


def _collect_alternatives(
    evaluations,
    prices: dict[str, ProteinPrice],
    *,
    cap: float | None,
    preset: TherapeuticPreset,
    method: str | None,
) -> tuple[
    list[HospitalAlternative],
    dict[str, RejectedAlternative],
    list[str],
]:
    """Split engine evaluations into ranked alternatives + rejected.

    The engine's hard gates (budget, protein floor, prep time, fail-closed
    allergen exclusions) run first; this layer adds the preset's per-meal
    protein cap and, when a cooking method is given, the method-survival
    screen. A score never argues a gated-out candidate back in.
    """
    alternatives: list[HospitalAlternative] = []
    rejected_by_protein: dict[str, RejectedAlternative] = {}
    warnings: list[str] = []
    for ev in evaluations:
        warnings.extend(ev.evidence_warnings)
        if not ev.plant_only:
            continue
        protein_id = next(
            pid for pid in prices
            if pid != "beef" and f"_{pid}_" in ev.option_id
        )
        price = prices[protein_id]
        profile = get_protein_function(protein_id)
        reasons = list(ev.reasons)
        feasible = ev.feasible
        if feasible and cap is not None and ev.protein_g > cap:
            feasible = False
            reasons.append(
                f"Exceeds the preset's per-meal protein cap of {cap:g} g "
                f"(preset: {preset.label})"
            )
        if feasible and method is not None:
            survives, survival_reasons = predict_method_survival(
                profile.functional, method)
            reasons.extend(survival_reasons)
            if not survives:
                feasible = False
        if feasible:
            alternatives.append(HospitalAlternative(
                protein_id=protein_id,
                name=profile.name,
                portion_g=ev.finished_g,
                protein_g=ev.protein_g,
                cost_ngn=ev.cost_ngn,
                prep_minutes=ev.prep_minutes,
                allergens=ev.allergens,
                functional=profile.functional,
                kitchen_meaning=profile.kitchen_meaning,
                score=ev.score,
                reasons=tuple(reasons),
                price_basis=price.price_basis,
                price_derived=price.price_derived,
                nutrition_source=profile.nutrition_source,
            ))
        else:
            # Keep the largest-portion attempt per protein: it is the
            # closest the protein gets, so its reasons are the honest summary.
            current = rejected_by_protein.get(protein_id)
            if current is None or ev.finished_g >= current.portion_g:
                rejected_by_protein[protein_id] = RejectedAlternative(
                    protein_id=protein_id,
                    name=profile.name,
                    portion_g=ev.finished_g,
                    reasons=tuple(reasons),
                )
    return alternatives, rejected_by_protein, warnings


def recommend_for_dish(
    dish_ref: str,
    *,
    preset_id: str = "standard",
    avoid_allergens: tuple[str, ...] = (),
    budget_ngn: float = DEFAULT_BUDGET_NGN,
    protein_floor_g: float | None = None,
    max_prep_minutes: float = DEFAULT_MAX_PREP_MINUTES,
    menu: tuple[HospitalDish, ...] | None = None,
    prices: dict[str, ProteinPrice] | None = None,
    dataset: Dataset | None = None,
) -> HospitalRecommendation:
    """Rank plant alternatives for one documented UNTH dish.

    Dishes whose protein the source does not document (stew, the soups) and
    dishes that are already plant-based are never transformed: the result
    says so, with the reason, instead of inventing a starting point.
    """
    menu = menu or load_unth_menu()
    prices = prices or load_protein_prices()
    dish = get_dish(menu, dish_ref)
    preset = get_preset(preset_id)
    base_notes = [f"Menu source: {MENU_SOURCE}.", f"Preset source: {preset.source}"]
    base_notes.extend(preset.notes)

    if dish.already_plant_based:
        return HospitalRecommendation(
            dish=dish, preset=preset, status="already_plant_based",
            alternatives=(), rejected=(), reference=None,
            notes=tuple(base_notes + [
                (f"{dish.name} is already plant-based on the documented menu - "
                 "it is a swap-in the kitchen already serves, not a "
                 "transformation target."),
            ]),
            evidence_warnings=(),
        )
    if dish.protein_status == "unspecified":
        return HospitalRecommendation(
            dish=dish, preset=preset, status="protein_unspecified",
            alternatives=(), rejected=(), reference=None,
            notes=tuple(base_notes + [
                (f"The source does not state what protein is in {dish.name}, so "
                 "this tool will not invent one in order to transform it. "
                 "Confirm the recipe with the kitchen first."),
            ]),
            evidence_warnings=(),
        )
    if dish.protein_status != "documented_animal":
        return HospitalRecommendation(
            dish=dish, preset=preset, status="no_documented_animal_protein",
            alternatives=(), rejected=(), reference=None,
            notes=tuple(base_notes + [
                (f"No animal protein is documented for {dish.name} in the "
                 "source, so there is nothing documented to diversify from."),
            ]),
            evidence_warnings=(),
        )

    floor = protein_floor_g
    if floor is None:
        floor = preset.protein_floor_g
    if floor is None:
        floor = DEFAULT_FLOOR_G
    dataset = dataset or build_hospital_dataset(menu, prices)
    dish_id = _dish_dataset_id(dish)
    evaluations = evaluate(
        dataset, dish_id,
        budget_ngn=budget_ngn, protein_target_g=floor,
        max_prep_minutes=max_prep_minutes,
        avoid_allergens=tuple(avoid_allergens),
        preference="", text_method="none",
    )

    alternatives, rejected_by_protein, warnings = _collect_alternatives(
        evaluations, prices, cap=preset.protein_cap_g_per_meal,
        preset=preset, method=None,
    )
    non_plant = [ev for ev in evaluations if not ev.plant_only]
    reference_eval = None
    if non_plant:
        reference_eval = non_plant[0]
        if alternatives:
            for ev in non_plant:
                if ev.finished_g == alternatives[0].portion_g:
                    reference_eval = ev
                    break

    reference = None
    if reference_eval is not None:
        reference = HospitalReference(
            name="Meat as documented (beef reference)",
            portion_g=reference_eval.finished_g,
            protein_g=reference_eval.protein_g,
            cost_ngn=reference_eval.cost_ngn,
            prep_minutes=reference_eval.prep_minutes,
            note=(
                "The source does not specify the type of meat; beef is the "
                "project catalogue's documented reference benchmark. "
                "Comparison only - never a recommendation."
            ),
        )
    notes = list(base_notes)
    notes.append(
        "Dawadawa (fermented locust bean) is not ranked as a main protein: "
        "it is a seasoning used at 5-10 g per serving. Its role here is the "
        "flavour base that keeps a diversified dish tasting like itself."
    )
    if dish.documented_animal_protein == "fish":
        notes.append(
            "No costed original is shown for fish: the project data has no "
            "cited fish price or protein-per-100 g row (the UNTH study "
            "reports fish only as a relative protein-density index), so the "
            "tool shows the alternatives without inventing a baseline."
        )
    if not alternatives:
        notes.append(
            "No plant alternative passes every hard constraint under this "
            "preset. That is a valid result: loosen a constraint with the "
            "dietitian, or keep the dish as documented."
        )
    return HospitalRecommendation(
        dish=dish, preset=preset, status="ok",
        alternatives=tuple(alternatives),
        rejected=tuple(rejected_by_protein.values()),
        reference=reference,
        notes=tuple(notes),
        evidence_warnings=tuple(dict.fromkeys(warnings)),
    )


# --------------------------------------------------------------------------
# Original vs modified comparison (built FROM a recommendation - no recompute)
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class DishComparison:
    dish_name: str
    alternative_name: str
    original_name: str
    portion_g: float
    original_protein_g: float | None
    alternative_protein_g: float
    original_cost_ngn: float | None
    alternative_cost_ngn: float
    original_prep_minutes: float | None
    alternative_prep_minutes: float
    original_functional: FunctionalProfile | None
    alternative_functional: FunctionalProfile
    original_allergens: tuple[str, ...] | None
    alternative_allergens: tuple[str, ...]
    # No cited calorie (kcal) row exists in the project data for both sides,
    # so calories stay None and callers must omit the row - never estimate.
    original_calories_kcal: float | None = None
    alternative_calories_kcal: float | None = None
    notes: tuple[str, ...] = ()


def build_comparison(recommendation: HospitalRecommendation) -> DishComparison | None:
    """Side-by-side of the recommended alternative vs the dish as documented.

    Every alternative-side number is copied from the recommendation result
    itself, so the comparison can never drift from the ranking. Original-side
    values are None where the project data has no cited value (fish).
    """
    if recommendation.status != "ok" or not recommendation.alternatives:
        return None
    alt = recommendation.alternatives[0]
    ref = recommendation.reference
    notes = []
    if ref is None:
        notes.append(
            "Original-side protein, cost and prep are not shown: no cited "
            "values exist in the project data for this dish."
        )
    else:
        notes.append(ref.note)
    return DishComparison(
        dish_name=recommendation.dish.name,
        alternative_name=alt.name,
        original_name=ref.name if ref else "As documented (no cited values)",
        portion_g=alt.portion_g,
        original_protein_g=ref.protein_g if ref else None,
        alternative_protein_g=alt.protein_g,
        original_cost_ngn=ref.cost_ngn if ref else None,
        alternative_cost_ngn=alt.cost_ngn,
        original_prep_minutes=ref.prep_minutes if ref else None,
        alternative_prep_minutes=alt.prep_minutes,
        original_functional=get_protein_function("beef").functional if ref else None,
        alternative_functional=alt.functional,
        original_allergens=() if ref else None,
        alternative_allergens=alt.allergens,
        notes=tuple(notes),
    )


# --------------------------------------------------------------------------
# Any-dish mode - staff type any dish, the same gates rank the alternatives
# --------------------------------------------------------------------------

CURRENT_PROTEIN_IDS = ("beef", "chicken", "fish", "goat", "egg", "unspecified")
CURRENT_PROTEIN_LABELS = {
    "beef": "Beef",
    "chicken": "Chicken",
    "fish": "Fish",
    "goat": "Goat meat",
    "egg": "Egg",
    "unspecified": "Not sure / unspecified",
}


@dataclass(frozen=True)
class ProteinBaseline:
    """The dish as the kitchen serves it today - cited values only.

    Any field the project data cannot cite stays None and is shown as
    "no cited value", never estimated.
    """

    protein_id: str
    label: str
    portion_g: float
    protein_g: float | None
    cost_ngn: float | None
    prep_minutes: float | None
    protein_source: str | None
    price_basis: str | None
    note: str


def build_baseline(
    current_protein: str,
    portion_g: float,
    prices: dict[str, ProteinPrice] | None = None,
) -> ProteinBaseline:
    """Cost the entered animal protein from cited catalogue values only.

    Beef: protein (WAFCT 07_023, via functional.py) and the WFP price row.
    Chicken: protein (WAFCT 07_033, via functional.py) - but no cited
    chicken price row exists anywhere in the project data, so the cost
    stays None. Fish, goat, egg and unspecified have no cited baseline at
    all; the alternatives are then ranked against the preset's floor.
    """
    if current_protein not in CURRENT_PROTEIN_IDS:
        raise ValueError(f"Unknown current protein: {current_protein!r}")
    prices = prices or load_protein_prices()
    label = CURRENT_PROTEIN_LABELS[current_protein]
    if current_protein == "beef":
        profile = get_protein_function("beef")
        price = prices["beef"]
        return ProteinBaseline(
            protein_id="beef",
            label=label,
            portion_g=portion_g,
            protein_g=round(
                profile.protein_g_per_100g * portion_g / 100.0, 2),
            cost_ngn=round(price.price_ngn_per_kg * portion_g / 1000.0, 2),
            prep_minutes=price.prep_minutes,
            protein_source=profile.nutrition_source,
            price_basis=price.price_basis,
            note=(
                "Beef is the project catalogue's documented reference "
                "benchmark. Comparison only - never a recommendation."
            ),
        )
    if current_protein == "chicken":
        profile = get_protein_function("chicken")
        return ProteinBaseline(
            protein_id="chicken",
            label=label,
            portion_g=portion_g,
            protein_g=round(
                profile.protein_g_per_100g * portion_g / 100.0, 2),
            cost_ngn=None,
            prep_minutes=None,
            protein_source=profile.nutrition_source,
            price_basis=None,
            note=(
                "Protein from the cited WAFCT row in the catalogue. No "
                "cited chicken price row exists in the project data, so "
                "the original-side cost is shown as no cited value rather "
                "than estimated."
            ),
        )
    if current_protein == "fish":
        note = (
            "No cited baseline in project data for fish: the project data "
            "has no cited fish protein-per-100 g or price row (the UNTH "
            "study reports fish only as a relative protein-density index), "
            "so the original side is not shown and the alternatives are "
            "ranked against the preset's protein floor."
        )
    elif current_protein == "unspecified":
        note = (
            "The current protein was not specified, so there is no "
            "original-side baseline; the alternatives are ranked against "
            "the preset's protein floor."
        )
    else:
        note = (
            f"No cited baseline in project data for {label.lower()}: no "
            "cited protein-per-100 g or price row exists for it, so the "
            "original side is not shown and the alternatives are ranked "
            "against the preset's protein floor."
        )
    return ProteinBaseline(
        protein_id=current_protein,
        label=label,
        portion_g=portion_g,
        protein_g=None,
        cost_ngn=None,
        prep_minutes=None,
        protein_source=None,
        price_basis=None,
        note=note,
    )


@dataclass(frozen=True)
class AnyDishSuggestion:
    dish_name: str
    current_protein: str
    method: str
    preset: TherapeuticPreset
    status: str  # ok
    alternatives: tuple[HospitalAlternative, ...]
    rejected: tuple[RejectedAlternative, ...]
    baseline: ProteinBaseline
    notes: tuple[str, ...]
    evidence_warnings: tuple[str, ...]
    requires_dietitian_signoff: bool = True
    signoff_note: str = SIGNOFF_NOTE


def suggest_for_any_dish(
    dish_name: str,
    *,
    current_protein: str = "unspecified",
    portion_g: float = 100.0,
    method: str = "soup",
    preset_id: str = "standard",
    avoid_allergens: tuple[str, ...] = (),
    budget_ngn: float = DEFAULT_BUDGET_NGN,
    protein_floor_g: float | None = None,
    max_prep_minutes: float = DEFAULT_MAX_PREP_MINUTES,
    prices: dict[str, ProteinPrice] | None = None,
    dataset: Dataset | None = None,
) -> AnyDishSuggestion:
    """Rank plant alternatives for ANY dish a hospital kitchen serves.

    The dish is staff-entered, not from the documented UNTH menu. It runs
    through the same engine gates as the UNTH flow (hard constraints,
    fail-closed allergen exclusions, protein floor, scoring, reasoning)
    plus the preset cap and the method-survival screen for the dish's
    cooking method. Dawadawa stays adjunct-only, never a ranked main.
    """
    name = dish_name.strip()
    if not name:
        raise ValueError(
            "Dish name is required - type the dish the kitchen serves today.")
    if len(name) > 200:
        raise ValueError("Dish name is limited to 200 characters")
    if current_protein not in CURRENT_PROTEIN_IDS:
        raise ValueError(f"Unknown current protein: {current_protein!r}")
    if method not in METHOD_REQUIREMENTS:
        raise ValueError(f"Unknown cooking method: {method!r}")
    if not (10.0 <= portion_g <= 500.0):
        raise ValueError("Portion must be between 10 g and 500 g")
    prices = prices or load_protein_prices()
    preset = get_preset(preset_id)
    floor = protein_floor_g
    if floor is None:
        floor = preset.protein_floor_g
    if floor is None:
        floor = DEFAULT_FLOOR_G
    portions = tuple(sorted(set(PORTIONS_G) | {float(portion_g)}))
    dataset = dataset or build_any_dish_dataset(prices, portions)
    evaluations = evaluate(
        dataset, ANY_DISH_DATASET_ID,
        budget_ngn=budget_ngn, protein_target_g=floor,
        max_prep_minutes=max_prep_minutes,
        avoid_allergens=tuple(avoid_allergens),
        preference="", text_method="none",
    )
    alternatives, rejected_by_protein, warnings = _collect_alternatives(
        evaluations, prices, cap=preset.protein_cap_g_per_meal,
        preset=preset, method=method,
    )
    baseline = build_baseline(current_protein, float(portion_g), prices)
    notes = [
        (f"Any-dish mode: '{name}' was entered by kitchen staff - it is "
         "not from the documented UNTH menu. The starting point is the "
         "protein, portion and cooking method entered here."),
        f"Preset source: {preset.source}",
        *preset.notes,
        (f"Method screen: the {METHOD_LABELS[method].lower()} requirements "
         "from the product's method-survival rule table - rule-based "
         "screening over qualitative functional descriptors, not a "
         "lab-validated simulation."),
        baseline.note,
        ("Dawadawa (fermented locust bean) is not ranked as a main "
         "protein: it is a seasoning used at 5-10 g per serving. Its role "
         "here is the flavour base that keeps a diversified dish tasting "
         "like itself."),
    ]
    if not alternatives:
        notes.append(
            "No plant alternative passes every hard constraint under this "
            "preset. That is a valid result: loosen a constraint with the "
            "dietitian, or keep the dish as served today."
        )
    return AnyDishSuggestion(
        dish_name=name,
        current_protein=current_protein,
        method=method,
        preset=preset,
        status="ok",
        alternatives=tuple(alternatives),
        rejected=tuple(rejected_by_protein.values()),
        baseline=baseline,
        notes=tuple(notes),
        evidence_warnings=tuple(dict.fromkeys(warnings)),
    )


def build_any_dish_comparison(
    suggestion: AnyDishSuggestion,
) -> DishComparison | None:
    """Side-by-side for any-dish mode, built FROM the suggestion itself.

    Alternative-side numbers are copied from the top-ranked alternative.
    Original-side protein and cost are the cited baseline values scaled to
    the alternative's portion (both are per-100 g / per-kg catalogue
    values, so the scaling is arithmetic on cited values, not a new
    estimate); they stay None where no cited baseline exists.
    """
    if not suggestion.alternatives:
        return None
    alt = suggestion.alternatives[0]
    baseline = suggestion.baseline
    factor = alt.portion_g / baseline.portion_g
    notes = [baseline.note]
    if baseline.protein_g is not None or baseline.cost_ngn is not None:
        notes.append(
            f"Original side is shown on the same {alt.portion_g:g} g "
            f"portion basis as the alternative, scaled from the "
            f"{baseline.portion_g:g} g portion entered."
        )
    else:
        notes.append(
            "Original-side protein, cost and prep are not shown: no cited "
            "values exist in the project data for this protein."
        )
    original_functional = None
    original_allergens: tuple[str, ...] | None = None
    if baseline.protein_id in ("beef", "chicken"):
        original_functional = get_protein_function(
            baseline.protein_id).functional
    if baseline.protein_id == "beef":
        original_allergens = ()
    return DishComparison(
        dish_name=suggestion.dish_name,
        alternative_name=alt.name,
        original_name=f"{baseline.label} as entered (original)",
        portion_g=alt.portion_g,
        original_protein_g=(
            round(baseline.protein_g * factor, 2)
            if baseline.protein_g is not None else None),
        alternative_protein_g=alt.protein_g,
        original_cost_ngn=(
            round(baseline.cost_ngn * factor, 2)
            if baseline.cost_ngn is not None else None),
        alternative_cost_ngn=alt.cost_ngn,
        original_prep_minutes=baseline.prep_minutes,
        alternative_prep_minutes=alt.prep_minutes,
        original_functional=original_functional,
        alternative_functional=alt.functional,
        original_allergens=original_allergens,
        alternative_allergens=alt.allergens,
        notes=tuple(notes),
    )


# --------------------------------------------------------------------------
# The plant-protein dataset, listed from its single source of truth
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class PlantProteinRow:
    protein_id: str
    name: str
    role: str  # candidate | adjunct
    protein_g_per_100g: float
    nutrition_source: str
    price_ngn_per_kg: float
    price_derived: bool
    price_basis: str
    allergens: tuple[str, ...]
    functional: FunctionalProfile
    kitchen_meaning: str


def _parse_allergen_labels(raw: str) -> tuple[str, ...]:
    cleaned = raw.strip().lower()
    if cleaned in ("", "none"):
        return ()
    return tuple(
        part.strip() for part in cleaned.replace(";", ",").split(",")
        if part.strip())


def plant_protein_dataset(
    prices: dict[str, ProteinPrice] | None = None,
) -> tuple[PlantProteinRow, ...]:
    """All 8 plant proteins with their cited values, for display.

    Rendered from functional.py (protein + functional profile + nutrition
    source) and data/hospital/protein_prices.csv (price + basis + role +
    allergens) - the same rows the engine ranks, never a hand-typed copy.
    """
    prices = prices or load_protein_prices()
    rows = []
    for protein in plant_proteins():
        price = prices[protein.id]
        rows.append(PlantProteinRow(
            protein_id=protein.id,
            name=protein.name,
            role=price.role,
            protein_g_per_100g=protein.protein_g_per_100g,
            nutrition_source=protein.nutrition_source,
            price_ngn_per_kg=price.price_ngn_per_kg,
            price_derived=price.price_derived,
            price_basis=price.price_basis,
            allergens=_parse_allergen_labels(price.allergens),
            functional=protein.functional,
            kitchen_meaning=protein.kitchen_meaning,
        ))
    return tuple(rows)


# --------------------------------------------------------------------------
# Patient conditions - a condition maps to a documented preset bundle and
# carries the team's cited evidence plus the limits of that evidence.
# Conditions change constraints and attach evidence; they are not clinical
# rules and they never turn an output into a prescription.
# --------------------------------------------------------------------------

META_ANALYSIS_SOURCE = (
    "Batubo et al., Dietary factors and hypertension risk in West Africa "
    "(systematic review/meta-analysis, Journal of Hypertension; "
    "TETFund-funded) - as reported in the team's hospital research notes"
)
BELLEVUE_SOURCE = (
    "NYC Health + Hospitals / Bellevue plant-based lifestyle medicine "
    "programme evaluation (Frontiers in Nutrition, 2023) - as reported "
    "in the team's hospital research notes"
)
LAGOS_SURVEY_SOURCE = (
    "Lagos population survey of meat consumption and hypertension "
    "prevalence (n=2,244) - as reported in the team's hospital research "
    "notes"
)
NIGERIA_SURVEY_SOURCE = (
    "Nigeria 2023 national hypertension survey (>24,000 adults, reported "
    "by Federal Ministry of Health officials) - as reported in the "
    "team's hospital research notes"
)
KESHINRO_SOURCE = (
    "Keshinro, glycaemic-response study of meals served to type-2 "
    "diabetic patients at UNTH Enugu (South African Journal of Clinical "
    "Nutrition) - as reported in the team's patient-menu research notes"
)
IMSUTH_SOURCE = (
    "Thesis evaluating the inpatient diabetic diet at IMSUTH Orlu - as "
    "reported in the team's patient-menu research notes"
)
JOS_ACHA_SOURCE = (
    "Beans-and-acha diabetic regimen study, Jos tertiary centre "
    "(Nigerian Journal of Family Practice) - as reported in the team's "
    "patient-menu research notes"
)

_META_ANALYSIS_NOTE = (
    "West African meta-analysis (Batubo et al.): red meat consumption "
    "was associated with higher hypertension odds (OR 1.51, 95% CI "
    "1.04-2.18); dietary fat OR 1.76; salt OR 1.25; fruit and vegetables "
    "were protective. These are associations reported by that review, "
    "quoted as context for the dietitian - not measurements of this menu."
)


@dataclass(frozen=True)
class PatientCondition:
    """A patient condition, mapped to one documented therapeutic preset.

    The mapping and every evidence note come from the team's cited
    sources only. Where the project data holds no values for the
    nutrients a condition's diet usually manages (sodium, fat,
    glycaemic measures), the condition says so as a limitation instead
    of applying - or claiming - a numeric filter.
    """

    id: str
    label: str
    preset_id: str  # an existing THERAPEUTIC_PRESETS key: the bundle applied
    preset_mapping_note: str
    evidence_notes: tuple[str, ...]
    limitations: tuple[str, ...]
    sources: tuple[str, ...]


CONDITIONS: dict[str, PatientCondition] = {
    "cardiovascular": PatientCondition(
        id="cardiovascular",
        label="Cardiovascular disease",
        preset_id="low_sodium",
        preset_mapping_note=(
            "Cardiovascular maps to the low-sodium preset bundle: UPTH's "
            "modified-diet definitions place heart-related diseases under "
            "the low-sodium diet (little added salt, high-sodium foods "
            "minimised). The preset leaves the protein floor at the "
            "standard tool floor, and the allergen gates are unchanged."
        ),
        evidence_notes=(
            _META_ANALYSIS_NOTE,
            ("Lagos population survey (n=2,244): daily meat consumption "
             "was associated with higher hypertension prevalence (38.6% "
             "vs 28% in rare consumers), and the authors concluded that "
             "avoiding red meat and increasing vegetables may reduce "
             "hypertension burden."),
            ("Programme evidence: NYC Health + Hospitals' plant-based "
             "lifestyle-medicine programme, which enrols adults with "
             "heart disease, hypertension and high cholesterol, reported "
             "significant improvements in weight, HbA1c and diastolic "
             "blood pressure at six months in a peer-reviewed evaluation "
             "of 173 patients. That is evidence about a supervised "
             "clinical programme, not about this menu draft."),
            ("UPTH's definitions also list a low-calorie diet for "
             "cardiovascular patients. That element is NOT applied here: "
             "the project data has no per-serving calorie values for "
             "these dishes or candidates, so nothing about calories is "
             "computed or claimed."),
        ),
        limitations=(
            ("LIMITATION: the project data has no sodium, saturated-fat "
             "or cholesterol values for any dish or candidate, so no "
             "numeric filter on those nutrients is applied or claimed. "
             "The bundle's numeric gates are the standard protein floor, "
             "the budget cap, prep time and the allergen exclusions - "
             "nothing else."),
            ("The low-sodium element is the UPTH diet posture - little "
             "added salt, high-sodium foods minimised - a "
             "kitchen-preparation instruction for the dietitian and "
             "kitchen to apply, not a computed property of these "
             "rankings. All ranked candidates are unprocessed single "
             "ingredients as modelled; the sodium and fat in the dish "
             "actually served depend on preparation (added salt, cooking "
             "oil) and must be confirmed by the dietitian for each "
             "patient."),
            ("The evidence notes are context for the dietitian, not a "
             "treatment claim: this draft does not claim to treat, "
             "manage or improve any patient's condition."),
        ),
        sources=(UPTH_SOURCE, META_ANALYSIS_SOURCE, LAGOS_SURVEY_SOURCE,
                 BELLEVUE_SOURCE),
    ),
    "hypertension": PatientCondition(
        id="hypertension",
        label="Hypertension",
        preset_id="low_sodium",
        preset_mapping_note=(
            "Hypertension maps to the existing low-sodium preset: UPTH's "
            "modified-diet definitions list hypertension under the "
            "low-sodium diet (little added salt, high-sodium foods "
            "minimised)."
        ),
        evidence_notes=(
            _META_ANALYSIS_NOTE,
            ("Nigeria's 2023 national survey (>24,000 adults) found "
             "hypertension in 22.9% of adults, with only 6.4% "
             "controlled - the context in which a hospital kitchen's "
             "salt posture matters."),
        ),
        limitations=(
            ("LIMITATION: the project data has no sodium values for any "
             "dish or candidate, so no numeric sodium filter is applied "
             "or claimed. The low-sodium element is the UPTH diet "
             "posture - a kitchen-preparation instruction, not a "
             "computed property of these rankings - and the dietitian "
             "confirms suitability for each patient."),
        ),
        sources=(UPTH_SOURCE, META_ANALYSIS_SOURCE, NIGERIA_SURVEY_SOURCE),
    ),
    "kidney": PatientCondition(
        id="kidney",
        label="Kidney disease",
        preset_id="low_protein",
        preset_mapping_note=(
            "Kidney maps to the existing low-protein preset: UPTH's "
            "modified-diet definitions list kidney disease under the "
            "low-protein diet (20-60 g/day), applied here through the "
            "preset's per-meal protein cap of 20 g."
        ),
        evidence_notes=(
            ("UPTH dietetics (placement report, Oct 2024): a low-protein "
             "diet of 20-60 g/day is given for kidney disease, liver "
             "disease and phenylketonuria. The preset's per-meal cap is "
             "arithmetic on that cited range (upper bound over three "
             "meals), labelled as such - not a clinical guideline."),
        ),
        limitations=(
            ("LIMITATION: this mapping applies the protein-quantity "
             "element of the UPTH definition only. Beyond protein "
             "quantity, this tool assesses nothing else for kidney "
             "diets: the project data holds no other nutrient values "
             "for these proteins, so no other filter is applied or "
             "claimed, and suitability for each patient is the "
             "dietitian's decision."),
        ),
        sources=(UPTH_SOURCE,),
    ),
    "diabetes": PatientCondition(
        id="diabetes",
        label="Diabetes",
        preset_id="standard",
        preset_mapping_note=(
            "Diabetes maps to the standard gates. UPTH's definitions "
            "list a low-calorie diet for diabetic patients, but the "
            "project data has no per-serving calorie values for these "
            "dishes or candidates, so no calorie filter can be applied "
            "or claimed; carbohydrate and glycaemic management remain "
            "the dietitian's prescription for each patient."
        ),
        evidence_notes=(
            ("UNTH glycaemic-response study (Keshinro): three meals "
             "served to type-2 diabetic patients were compared - meat, "
             "beans and corn pottage with spinach had the lowest "
             "glycaemic index and load (GI 33.00 / GL 4.76); meat and "
             "okro soup with fermented cassava dough had the highest "
             "(GI 74.50 / GL 21.59); the third test meal, pap with "
             "bambara nut pudding (okpa), was plant-based. These were "
             "study test meals reflecting commonly consumed meals at "
             "UNTH, not a printed ward menu chart."),
            ("IMSUTH Orlu inpatient diabetic diet (thesis): 85% of the "
             "protein was sourced from legumes, with akara balls and "
             "okpa named in the diabetic therapeutic diet."),
            ("Jos tertiary centre (Nigerian Journal of Family Practice): "
             "type-2 diabetes patients restricted to a beans-and-acha "
             "diet had poor glycaemic control (42 patients) - a caution "
             "from the same evidence base that a narrow legume-only "
             "prescription is not adequate management on its own."),
        ),
        limitations=(
            ("LIMITATION: the engine holds no glycaemic index/load, "
             "carbohydrate or calorie values per candidate, so no GI, "
             "carbohydrate or calorie filter is applied or claimed. The "
             "only numeric gates are the standard protein floor, the "
             "budget cap, prep time and the allergen exclusions."),
        ),
        sources=(KESHINRO_SOURCE, IMSUTH_SOURCE, JOS_ACHA_SOURCE),
    ),
}

CONDITION_IDS = tuple(CONDITIONS)


def get_condition(condition_id: str) -> PatientCondition:
    try:
        return CONDITIONS[condition_id]
    except KeyError:
        raise ValueError(f"Unknown patient condition: {condition_id!r}") from None


def condition_framing(condition: PatientCondition) -> str:
    """The framing sentence every condition output must carry."""
    return (
        f"Draft menu to support dietary management of "
        f"{condition.label.lower()} - decision support for the "
        f"dietitian, not a prescription and not a served menu."
    )


# --------------------------------------------------------------------------
# Condition menu - the documented menu composed under a condition's bundle
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class ConditionMenuItem:
    dish: HospitalDish
    # kept_as_is | transformed | no_eligible_alternative | confirm_with_kitchen
    status: str
    recommendation: HospitalRecommendation | None
    alternative: HospitalAlternative | None  # top-ranked, when transformed
    note: str


@dataclass(frozen=True)
class ConditionMenu:
    condition: PatientCondition
    preset: TherapeuticPreset
    framing: str
    items: tuple[ConditionMenuItem, ...]
    evidence_notes: tuple[str, ...]
    limitations: tuple[str, ...]
    sources: tuple[str, ...]
    notes: tuple[str, ...]
    # Totals cover ONLY the diversified dishes' chosen alternatives -
    # the only items with cited per-serving values. See totals_note.
    transformed_protein_g: float | None
    transformed_cost_ngn: float | None
    totals_note: str
    requires_dietitian_signoff: bool = True
    signoff_note: str = SIGNOFF_NOTE


def build_condition_menu(
    condition_id: str,
    *,
    avoid_allergens: tuple[str, ...] = (),
    budget_ngn: float = DEFAULT_BUDGET_NGN,
    menu: tuple[HospitalDish, ...] | None = None,
    prices: dict[str, ProteinPrice] | None = None,
    dataset: Dataset | None = None,
) -> ConditionMenu:
    """Compose a draft menu for a condition from the 14 documented items.

    Already-plant items are kept as documented. The two items with a
    documented animal protein (fish, meat) are diversified under the
    condition's preset bundle, each carrying its full recommendation.
    Every other item is classified "confirm recipe with the kitchen" -
    the source does not document its protein, so it is never silently
    transformed. Totals are summed over the diversified dishes' chosen
    alternatives only, because those are the only items with cited
    per-serving values; no whole-menu total is shown.
    """
    condition = get_condition(condition_id)
    preset = get_preset(condition.preset_id)
    menu = menu or load_unth_menu()
    prices = prices or load_protein_prices()

    items: list[ConditionMenuItem] = []
    for dish in menu:
        if dish.already_plant_based:
            items.append(ConditionMenuItem(
                dish=dish, status="kept_as_is", recommendation=None,
                alternative=None,
                note=(
                    f"{dish.name} is already plant-based on the documented "
                    "menu - kept as documented. It is evidence the kitchen "
                    "already serves plant proteins, not a transformation "
                    "target."
                ),
            ))
        elif dish.protein_status == "documented_animal":
            recommendation = recommend_for_dish(
                dish.item_id, preset_id=condition.preset_id,
                avoid_allergens=tuple(avoid_allergens),
                budget_ngn=budget_ngn, menu=menu, prices=prices,
                dataset=dataset,
            )
            if recommendation.alternatives:
                top = recommendation.alternatives[0]
                items.append(ConditionMenuItem(
                    dish=dish, status="transformed",
                    recommendation=recommendation, alternative=top,
                    note=(
                        f"Top-ranked additional option under the "
                        f"{condition.label} bundle: {top.name} - "
                        f"{top.portion_g:g} g portion, {top.protein_g:g} g "
                        f"protein, estimated NGN {top.cost_ngn:,.2f}. The "
                        "full ranking and the rejected options, with "
                        "reasons, are in the recommendation."
                    ),
                ))
            else:
                items.append(ConditionMenuItem(
                    dish=dish, status="no_eligible_alternative",
                    recommendation=recommendation, alternative=None,
                    note=(
                        "No plant alternative passes every hard constraint "
                        "under this condition's bundle, so the dish stays "
                        "as documented and the dietitian decides. The "
                        "rejected options, with reasons, are in the "
                        "recommendation."
                    ),
                ))
        else:
            items.append(ConditionMenuItem(
                dish=dish, status="confirm_with_kitchen",
                recommendation=None, alternative=None,
                note=(
                    "Confirm recipe with the kitchen: the source does not "
                    f"document the protein or full recipe of {dish.name}, "
                    "so this tool never assigns it one and never "
                    "transforms it silently."
                ),
            ))

    chosen = [item.alternative for item in items
              if item.status == "transformed" and item.alternative is not None]
    if chosen:
        transformed_protein_g: float | None = round(
            sum(alt.protein_g for alt in chosen), 2)
        transformed_cost_ngn: float | None = round(
            sum(alt.cost_ngn for alt in chosen), 2)
        totals_note = (
            "Totals cover only the diversified dishes' chosen "
            "alternatives - the only items with cited per-serving "
            "protein and cost values. Kept-as-documented and "
            "confirm-with-the-kitchen items carry no cited per-serving "
            "values in the project data, so no whole-menu total is "
            "shown rather than estimated."
        )
    else:
        transformed_protein_g = None
        transformed_cost_ngn = None
        totals_note = (
            "No totals are shown: no dish was diversified under this "
            "condition's bundle and constraints, so there are no chosen "
            "alternatives to sum."
        )

    notes = [
        f"Menu source: {MENU_SOURCE}.",
        f"Condition bundle: {condition.preset_mapping_note}",
        f"Preset source: {preset.source}",
        *preset.notes,
        ("Dawadawa (fermented locust bean) is not ranked as a main "
         "protein: it is a seasoning used at 5-10 g per serving. Its role "
         "here is the flavour base that keeps a diversified dish tasting "
         "like itself."),
    ]
    return ConditionMenu(
        condition=condition,
        preset=preset,
        framing=condition_framing(condition),
        items=tuple(items),
        evidence_notes=condition.evidence_notes,
        limitations=condition.limitations,
        sources=condition.sources,
        notes=tuple(notes),
        transformed_protein_g=transformed_protein_g,
        transformed_cost_ngn=transformed_cost_ngn,
        totals_note=totals_note,
    )


# --------------------------------------------------------------------------
# Kitchen feedback intake (append-only; the app does NOT learn automatically)
# --------------------------------------------------------------------------

FEEDBACK_FIELDS = (
    "submitted_at", "dish", "alternative", "preset",
    "availability", "practicality", "cost_realistic", "acceptability",
    "comment", "review_status",
)
AVAILABILITY_VALUES = ("available", "hard to find", "unavailable")
PRACTICALITY_VALUES = ("practical", "some difficulty", "not practical")
COST_REALISTIC_VALUES = ("yes", "partly", "no")
ACCEPTABILITY_VALUES = ("accepted", "mixed", "rejected")


def append_hospital_feedback(
    path: str | Path | None = None,
    *,
    dish: str,
    alternative: str,
    preset: str,
    availability: str,
    practicality: str,
    cost_realistic: str,
    acceptability: str,
    comment: str = "",
) -> dict[str, str]:
    """Append one kitchen-feedback row, creating the CSV (with header) if absent.

    Submissions are stored for team review and used to improve the data and
    recommendations manually. Nothing about this is automatic learning.
    """
    checks = (
        ("availability", availability, AVAILABILITY_VALUES),
        ("practicality", practicality, PRACTICALITY_VALUES),
        ("cost_realistic", cost_realistic, COST_REALISTIC_VALUES),
        ("acceptability", acceptability, ACCEPTABILITY_VALUES),
    )
    for field, value, allowed in checks:
        if value not in allowed:
            raise ValueError(f"{field} must be one of {allowed}: {value!r}")
    if len(comment) > 2000:
        raise ValueError("Comment cannot exceed 2000 characters")
    target = Path(path) if path is not None else DEFAULT_FEEDBACK_PATH
    row = {
        "submitted_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "dish": dish,
        "alternative": alternative,
        "preset": preset,
        "availability": availability,
        "practicality": practicality,
        "cost_realistic": cost_realistic,
        "acceptability": acceptability,
        "comment": comment,
        "review_status": "pending",
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    needs_header = not target.exists() or target.stat().st_size == 0
    with target.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(FEEDBACK_FIELDS))
        if needs_header:
            writer.writeheader()
        writer.writerow(row)
    return row
