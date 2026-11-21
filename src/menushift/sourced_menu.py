"""Interactive suya comparison driven by the workbook and later BS averages.

Purchase grams follow the finished weight you choose and the water-loss percentages
printed on the nutrition sheet. Soy cost uses the workbook yield note. Nothing here
is written to data/verified, and pressing does not create protein: a pressed 100 g
piece simply starts from more wet curd.
"""
from __future__ import annotations

from pathlib import Path

from .engine import Dataset, validate_dataset
from .official_prices import preparation_methods, working_market_table

PRESS_LOSS = {"awara_firm": 0.0, "awara_pressed": 0.20, "awara_frozen": 0.25}
PREP_KEYS = {
    "awara_firm": "firm",
    "awara_pressed": "pressed",
    "awara_frozen": "frozen",
    "awara_fried": "fried",
}


def _lookup(table: list[dict[str, str]], item: str) -> dict[str, str]:
    for row in table:
        if row["item"] == item:
            return row
    raise ValueError(f"Sourced price table has no row for {item}")


def _date_for(period: str) -> tuple[str, str]:
    if period == "2026-05":
        return "2026-05-31", "Nigeria national average"
    if period == "2026-04":
        return "2026-04-30", "Nigeria national average"
    return "unknown", "Workbook quote: date and city not recorded"


def _ingredient(
    ingredient_id: str,
    name: str,
    *,
    animal: bool,
    price: str,
    period: str,
    source: str,
    protein: str,
    iron: str,
    zinc: str,
    nutrition_source: str,
    nutrition_state: str,
    allergens: str,
    animal_origin_reviewed: bool = True,
) -> dict[str, str]:
    price_date, region = _date_for(period)
    return {
        "ingredient_id": ingredient_id,
        "name": name,
        "is_animal": "true" if animal else "false",
        "price_ngn_per_kg": price,
        "price_date": price_date,
        "price_region": region,
        "price_source": source,
        "protein_g_per_100g": protein,
        "iron_mg_per_100g": iron,
        "zinc_mg_per_100g": zinc,
        "nutrition_source": nutrition_source,
        "nutrition_state": nutrition_state,
        "allergens": allergens,
        "animal_origin_reviewed": "true" if animal_origin_reviewed else "false",
    }


def build_sourced_menu(
    folder: str | Path | None = None,
    *,
    finished_g: float = 100,
    wet_yield_kg_per_kg_dry: float = 1.75,
    prep_minutes: dict[str, float] | None = None,
    oil_cl: float = 0,
    onion_g: float = 0,
    pepper_g: float = 0,
    salt_g: float = 0,
    seasoning_g: float = 0,
) -> Dataset:
    """Build the four awara methods, plus beef as a reference, from sourced prices."""
    if finished_g <= 0 or wet_yield_kg_per_kg_dry <= 0 or oil_cl < 0:
        raise ValueError("Finished weight and soy yield must be positive; oil cannot be negative")
    if any(grams < 0 for grams in (onion_g, pepper_g, salt_g, seasoning_g)):
        raise ValueError("Spice amounts cannot be negative")
    minutes = {"firm": 60.0, "pressed": 60.0, "frozen": 60.0, "fried": 60.0}
    minutes.update(prep_minutes or {})
    if any(value <= 0 for value in minutes.values()):
        raise ValueError("Preparation minutes must be positive")

    prices = working_market_table(folder)
    methods = {row["food_item"]: row for row in preparation_methods(folder)}
    firm = next(row for name, row in methods.items() if name.startswith("Method 1"))
    fried_nutrients = next(row for name, row in methods.items() if name.startswith("Method 4"))
    beef_nutrients = next(row for name, row in methods.items() if name.startswith("Reference"))
    soy = _lookup(prices, "Soybeans (Raw)")
    milling = _lookup(prices, "Local Grinding / Milling")
    beef = _lookup(prices, "Beef boneless raw")
    onion = _lookup(prices, "Onions fresh")
    pepper = _lookup(prices, "Pepper (Fresh / Chili)")
    salt = _lookup(prices, "Iodized Table Salt")
    seasoning = _lookup(prices, "Seasoning Cubes")
    oil = _lookup(prices, "Vegetable oil")

    wet_price = (float(soy["price_ngn"]) + float(milling["price_ngn"])) / wet_yield_kg_per_kg_dry
    wet_source = (
        f"{soy['source']} plus milling {milling['source']}; "
        f"workbook yield note {wet_yield_kg_per_kg_dry:g} kg wet curd per kg dry soy"
    )
    ingredients = [
        _ingredient(
            "wet_awara",
            "Wet awara curd",
            animal=False,
            price=f"{wet_price:.4f}",
            period=soy["period"],
            source=wet_source,
            protein=firm["protein_g"],
            iron=firm["iron_mg"],
            zinc=firm["zinc_mg"],
            nutrition_source=firm["source"],
            nutrition_state="firm raw tofu reference applied to purchased wet curd",
            allergens="soy",
        ),
        _ingredient(
            "fried_awara",
            "Fried awara",
            animal=False,
            price=f"{wet_price:.4f}",
            period=soy["period"],
            source=wet_source + "; fried piece priced at the wet-curd rate because starting weight is unmeasured",
            protein=fried_nutrients["protein_g"],
            iron=fried_nutrients["iron_mg"],
            zinc=fried_nutrients["zinc_mg"],
            nutrition_source=fried_nutrients["source"],
            nutrition_state="published fried-tofu reference per 100 g finished piece",
            allergens="soy",
        ),
        _ingredient(
            "onion",
            onion["item"],
            animal=False,
            price=onion["comparable_ngn_per_kg"] or onion["price_ngn"],
            period=onion["period"],
            source=onion["source"],
            protein="0",
            iron="0",
            zinc="0",
            nutrition_source="no nutrient row in the workbook",
            nutrition_state="price only",
            allergens="unreviewed",
        ),
        _ingredient(
            "pepper",
            pepper["item"],
            animal=False,
            price=pepper["comparable_ngn_per_kg"] or pepper["price_ngn"],
            period=pepper["period"],
            source=pepper["source"],
            protein="0",
            iron="0",
            zinc="0",
            nutrition_source="no nutrient row in the workbook",
            nutrition_state="price only",
            allergens="unreviewed",
        ),
        _ingredient(
            "salt",
            salt["item"],
            animal=False,
            price=salt["comparable_ngn_per_kg"],
            period=salt["period"],
            source=salt["source"],
            protein="0",
            iron="0",
            zinc="0",
            nutrition_source="no nutrient row in the workbook",
            nutrition_state="price only",
            allergens="unreviewed",
        ),
        _ingredient(
            "seasoning",
            seasoning["item"],
            animal=False,
            price=seasoning["comparable_ngn_per_kg"],
            period=seasoning["period"],
            source=seasoning["source"],
            protein="0",
            iron="0",
            zinc="0",
            nutrition_source="no nutrient row in the workbook",
            nutrition_state="price only",
            allergens="unknown;verify label",
            animal_origin_reviewed=False,  # compound seasoning lacks verified ingredients
        ),
        _ingredient(
            "beef",
            beef["item"],
            animal=True,
            price=beef["price_ngn"],
            period=beef["period"],
            source=beef["source"],
            protein=beef_nutrients["protein_g"],
            iron=beef_nutrients["iron_mg"],
            zinc=beef_nutrients["zinc_mg"],
            nutrition_source=beef_nutrients["source"] + "; not the nutrient content of the raw priced kilogram",
            nutrition_state="cooked lean per 100 g, shown beside a raw price",
            allergens="unreviewed",
        ),
    ]
    dishes = [{
        "dish_id": "suya",
        "name": "Suya",
        "description": "Awara methods priced from the workbook and 2026 NBS averages",
    }]
    definitions = (
        ("awara_firm", "Firm awara (unpressed)", "firm raw unpressed awara", "Wet curd at the finished weight. No press loss."),
        ("awara_pressed", "Pressed awara (20% water loss)", "pressed firm chewy awara", "20% water loss from the workbook. Extra curd is purchased; protein is not created."),
        ("awara_frozen", "Frozen, thawed, pressed awara (25% water loss)", "frozen thawed pressed chewy awara", "25% water loss from the workbook. Extra curd is purchased; protein is not created."),
        ("awara_fried", "Fried awara", "fried deep-fried awara", "Fried nutrient row on the finished weight, plus the oil volume you enter."),
    )
    options: list[dict[str, str]] = []
    items: list[dict[str, str]] = []
    oil_naira = oil_cl / 75.0 * float(oil["price_ngn"])
    spices = (("onion", onion_g), ("pepper", pepper_g), ("salt", salt_g), ("seasoning", seasoning_g))
    for option_id, name, tags, note in definitions:
        if option_id == "awara_fried" and oil_cl <= 0:
            continue
        loss = PRESS_LOSS.get(option_id, 0.0)
        purchase = finished_g / (1 - loss)
        ingredient_id = "fried_awara" if option_id == "awara_fried" else "wet_awara"
        options.append({
            "option_id": option_id,
            "dish_id": "suya",
            "name": name,
            "group": "plant",
            "prep_minutes": str(minutes[PREP_KEYS[option_id]]),
            "energy_cost_ngn": "0",
            "labour_cost_ngn": "0",
            "other_cost_ngn": f"{oil_naira:.4f}" if option_id == "awara_fried" else "0",
            "finished_weight_g": str(finished_g),
            "texture_tags": tags,
            "method_notes": note,
        })
        items.append({
            "option_id": option_id,
            "ingredient_id": ingredient_id,
            "purchase_g": f"{purchase:.4f}",
            "nutrient_retention_fraction": "1",
            "item_notes": note,
        })
        for spice_id, grams in spices:
            if grams > 0:
                items.append({
                    "option_id": option_id,
                    "ingredient_id": spice_id,
                    "purchase_g": str(grams),
                    "nutrient_retention_fraction": "1",
                    "item_notes": "Amount entered for this comparison; not a measured recipe",
                })
    options.append({
        "option_id": "beef_suya",
        "dish_id": "suya",
        "name": "Beef suya reference",
        "group": "reference",
        "prep_minutes": str(minutes["firm"]),
        "energy_cost_ngn": "0",
        "labour_cost_ngn": "0",
        "other_cost_ngn": "0",
        "finished_weight_g": str(finished_g),
        "texture_tags": "beef reference",
        "method_notes": "Raw NBS price and cooked nutrient row are shown on the same gram weight. They are not one measured piece.",
    })
    items.append({
        "option_id": "beef_suya",
        "ingredient_id": "beef",
        "purchase_g": str(finished_g),
        "nutrient_retention_fraction": "1",
        "item_notes": "Same gram weight applied to a raw price and a cooked nutrient row",
    })
    data = Dataset(ingredients, dishes, options, items, demo=False)
    validate_dataset(data)
    return data
