# Naija MenuShift — menu diversification brief

**Challenge:** Hack the Fork Nigeria 2026, Challenge 2 — AI for Plant-Based Menu Innovation.

**Positioning:** Help Nigerian restaurants and caterers **diversify their existing menus** with additional plant-based choices. Current animal-based dishes can remain available; the product supports choice, not compulsory replacement.

**Problem hypothesis:** Exploring extra dishes or accompaniments is difficult when local ingredient costs, nutritional references, portion yields, available equipment, allergens and culinary practicality are uncertain. Buyer interviews are needed to verify this hypothesis.

**Solution hypothesis:** An evidence-aware recipe exploration and decision-support tool can screen optional menu additions against the restaurant's budget, estimated protein, time, equipment and dietary requirements, explain trade-offs, and identify what needs kitchen testing.

**Current scope:** The primary pilot compares four awara/tofu preparation methods suitable for exploring a plant-based suya offering. Conventional beef suya stays as a context/reference. The second menu context explores a **tofu protein accompaniment to jollof**, not a fully costed or validated jollof meal. Vchunks is recorded as a sourced commercial example, not an approved numeric candidate.

**Data status:** The live studios use historical prices and published food-composition references together with unmeasured cooking and serving assumptions. The read-only Evidence Library presents **15 curated FAO/USDA nutrient records** and **28 WFP price snapshots for Borno and Yobe in October–November 2026**, separated from the recipe engine. No live nationwide prices, customer taste scores or measured kitchen trials are claimed.

## What the product can demonstrate

- Select a menu context, budget, protein threshold, preparation time and available kitchen equipment.
- Exclude candidates that fail hard constraints, including user-specified ingredient restrictions.
- Compare eligible candidates by estimated cost, protein, time, and experimental text preferences.
- Present budget-first, protein-first, kitchen-first and balanced options, including a Pareto trade-off view.
- Inspect price-source and food-state caveats, historical survey scope and unvalidated preparation inputs.
- Return **no eligible recommendation** when the evidence or constraints cannot support one.

## Success measures to validate, not yet achieved

- Record local dated quotations and actual ingredient purchasing units for each candidate.
- Weigh purchased and finished portions; measure preparation time, fuel, oil and labour.
- Match each real menu ingredient to the correct composition food state and food-specific allergen label.
- Compare restaurant-reviewed choices against the cheapest feasible baseline, keyword scores and TF-IDF.
- Demonstrate that an additional menu option can be prepared consistently and that operators find the recommendations useful.

**Out of scope at present:** guaranteed health outcomes, proven nutritional equivalence, food-safety certification, live national market prices, measured environmental impact, general generative-AI recipe creation, and commercial traction claims.

Further detail: `docs/DATASET_INTAKE_AND_DIVERSIFICATION_2026-11-20.md`.
