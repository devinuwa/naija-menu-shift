"""Partial second menu pilot; shared food data, no invented chicken/rice figures."""
from __future__ import annotations

from pathlib import Path

from .engine import Dataset, validate_dataset
from .sourced_menu import build_sourced_menu

DISH_LABELS = {
    "suya": "Suya — awara methods",
    "jollof_side": "Jollof rice — plant-protein accompaniment (partial)",
}
DISH_SCOPE = {
    "suya": "Ingredient estimates; complete kitchen costs and cooking yields are not measured.",
    "jollof_side": (
        "PARTIAL ONLY: estimates refer to the proposed plant-protein side. Rice, "
        "sauce, original chicken reference and whole-meal nutrition are not included."
    ),
}


def build_menu_pilots(folder: str | Path | None = None, **kwargs) -> Dataset:
    """Re-use awara candidates for an exploratory jollof accompaniment.

    The separate dish ID proves reusable constraints; it does not constitute
    a validated recipe transformation or a complete finished meal.
    """
    base = build_sourced_menu(folder, **kwargs)
    dishes = [dict(d) for d in base.dishes] + [{
        "dish_id": "jollof_side",
        "name": "Jollof with plant-based protein accompaniment",
        "description": DISH_SCOPE["jollof_side"],
    }]
    options = [dict(o) for o in base.options]
    items = [dict(i) for i in base.items]
    for old in base.options:
        if old["group"] != "plant":
            continue
        new_id = "jollof_" + old["option_id"]
        clone = dict(old)
        clone.update(
            option_id=new_id,
            dish_id="jollof_side",
            name=old["name"] + " as a jollof protein side",
            method_notes=DISH_SCOPE["jollof_side"] + " " + old["method_notes"],
        )
        options.append(clone)
        for line in base.items:
            if line["option_id"] == old["option_id"]:
                row = dict(line)
                row["option_id"] = new_id
                row["item_notes"] = "Protein side only; no full-meal measurement. " + line.get("item_notes", "")
                items.append(row)
    data = Dataset(
        ingredients=[dict(i) for i in base.ingredients],
        dishes=dishes,
        options=options,
        items=items,
        demo=False,
    )
    validate_dataset(data)
    return data
