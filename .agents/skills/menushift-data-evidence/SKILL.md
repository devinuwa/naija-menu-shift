---
name: menushift-data-evidence
description: Use when researching, editing, validating, or importing ingredient prices, nutrients, recipes, allergies, or other evidence for Naija MenuShift.
---
# Evidence-backed data workflow
1. Identify the exact food form and measurement state (raw, firm tofu as purchased, cooked beef, etc.); never mix without documenting conversion.
2. Record the price with source, ISO date, geographic market, units per kilogram and supplier assumptions.
3. Record separate protein, iron and zinc source, nutrient units per 100 g and food state.
4. Record purchased weights, measured finished weights, preparation time, ingredient portions, energy/fuel/labour and any processing losses. Never infer that pressing tofu creates protein.
5. Label allergy exposures and incomplete packaged-ingredient review explicitly. A missing allergen flag does not mean safe.
6. Enter rows in all four `data/verified/*.csv` files, validate via `load_dataset(..., demo=False)` and run `audit_dataset`.
7. Supply the source log and limitations. Do not approve claims about customer taste, nutritional equivalence, or restaurant practicality without expert tests.
