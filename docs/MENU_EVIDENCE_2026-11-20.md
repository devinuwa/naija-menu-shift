# Menu evidence release and validation plan — 20 November 2026

**Product framing:** Naija MenuShift helps restaurants diversify menus with additional plant-based choices alongside their existing offerings. It is not a programme to remove or replace conventional dishes.\n\n## Honest scope\nNaija MenuShift now has two distinct selectable contexts:
1. **Suya**: plant-based awara/tofu method comparison, from historical price and generic nutrition references. Beef is only an imperfect raw-price / cooked-nutrition reference.
2. **Jollof with a plant-based protein side**: separate dish ID using the same sourced awara methods to demonstrate reusable constraints. **Only the proposed protein-side ingredient cost and nutrients are shown**. Rice, sauce, original chicken, full meal weights and additional kitchen costs are **not** included. This is a partial exploratory **additional accompaniment**, not a validated complete jollof recipe.

Both depend on assumptions for purchased/finished tofu yield, recipe mass, preparation time, oil and fuel. No verified cooking trials have been added, and `data/verified/` stays empty.

## Sources checked on 20 Nov 2026

| Source | What is grounded | What cannot be inferred |
|---|---|---|
| [VeggieVictory packaged Vchunks](https://veggievictory.com/product/vchunks-plant-based-meat/) | Retail offer, 150 g, ₦4,500 listed | Final cooked weight, current full ingredient/nutrient panel, restaurant cost |
| [VeggieVictory Vchunks Suya](https://veggievictory.com/product/vchunks-suya/) | Prepared suya listed at ₦2,000; described as wheat-based protein | Whether the pack and prepared menu have the same formulation, serving weight or protein per 100 g |
| [FAO/INFOODS West African Composition Table 2019](https://www.fao.org/infoods/infoods/tables-and-databases/faoinfoods-databases/en) | Regional nutrient reference with published food state and methodology | Today’s food prices; exact nutrients of the local recipe after frying, freezing or cooking |
| [USDA FoodData Central](https://fdc.nal.usda.gov/) | Generic tofu, beef and chicken nutrient food records | Local Nigerian awara or a specific Vchunks pack |
| [NBS Food Price Watch source catalogue](https://microdata.nigerianstat.gov.ng/index.php/catalog/162/related-materials) | Historical Nigerian market survey figures with publication periods | Today's actual vendor quote or per-finished-serving cost |

The staging files in `data/sources/` and `data/research/` preserve provenance. In particular `data/sources/nbs_2026.csv` documents *secondary transcription* of official historic price figures; do not misrepresent it as a live NBS API.

`data/research/vchunks_observations_2026-11-20.csv` captures the vendor-reported selling prices. Vchunks is **not** in ranked options because the product-specific numerical nutrients, allergen confirmation, processing yield and serving recipe are not documented. Wheat is explicit in the prepared suya description; soy and cross-contact need checking directly on a current pack.

## What must be collected for real validation
- **Amina:** actual local purchase quotes for tofu/awara, dry soybeans, beef, oil, spices and rice/chicken, with city, date, exact sale unit, vendor evidence and source reliability.
- **Team / chef:** actual purchased/final masses, cooking oil uptake, time, electricity/fuel cost, preparation losses, allergen label, texture/skewer observations, and blind or documented taste test results for each treatment.
- **Ibrahim/Muhammad:** compare cost per complete serving with matching raw/cooked states, record uncertainty, test no feasible cases, and benchmark any optional model against the constrained cheapest-feasible approach.
- **Complete jollof:** source and measure cooked rice/tomato-stock ingredient quantities, side protein, and original chicken baseline. A tofu-side calculation alone cannot validate a complete jollof meal.
- **Vchunks:** current packaged nutrition facts and full ingredient/allergen list, pack mass before/after hydration, how it is prepared for suya/jollof, dated local purchase price, and independent suitability check.

## Kitchen-trial form

Enter **measured, attributable observations only** in `data/evaluation/kitchen_trials.csv`. Header fields require option and dish identifiers, dated observed quantities, locality, oil added/retained, prep minutes, attributable energy and labour cost, sensory comments and the reviewer's role/evidence reference. The template contains **zero** records by design. Nothing is marked “approved” until reviewed.

## Release claims

Allowed: “two menu contexts, one complete numerical side-model reused for a second dish, evidence trail, hard constraints and truthful abstention.”

Not allowed: “two independently validated recipes,” “real-time price accuracy,” “Vchunks protein equivalence,” “fully costed jollof,” “food-safe alternatives,” “learned taste prediction,” or “commercial success” without evidence.

## Prioritized post-release work
1. Current local quotations and measured awara production/retail purchase price.
2. Complete recipe and measured jollof/chicken reference.
3. At least two reproducible kitchen trials per candidate and review of allergens.
4. Test on deployed desktop/mobile and capture screenshots.
5. Only then promote approved data to verified status with review.

The sole target is the private `Ibrahim-KIA/naija-menushift` repository. No PR or paid service is required.
