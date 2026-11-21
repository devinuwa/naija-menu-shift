# Engineering handoff: generic design, formulas and AI experiment

## Core data relations

- `dishes.csv`: one record for each Nigerian menu dish.
- `ingredients.csv`: each edible purchased ingredient's attributes, prices, nutrition and sources.
- `options.csv`: candidate transformations and preparation methods, **per-serving** time and overhead costs; reference options are kept separate from plant-only recommendations.
- `option_items.csv`: the composition of each candidate option in **purchase grams per serving** with an assumed retention factor.

Add dishes/variants with rows—not new `if dish == 'suya'` branches.

## Cost model

`ingredient_cost_per_serving = Σ(purchase_grams_i × price_NGN_per_kg_i / 1000)`

`total_cost_per_serving = ingredient_cost + energy_cost + labour_cost + other_cost`

`price_sensitivity = Σ(purchase_grams_i × quoted_price_i / 1000 × (1 + shock)) + fixed_other_costs`

Default shock set = −20%, 0%, +20%. Price perturbation applies to all purchased ingredients, not to labour/fuel overheads. That simplified stress test is **not a market forecast**.

## Nutrient approximation

`estimated_nutrient_per_serving = Σ(purchase_g_i × nutrient_per_100g_i / 100 × retention_fraction_i)`

The current retention field applies to all nutrients; this is **oversimplified** and must be disclosed. Unlike concentrations per 100 g, estimated **total grams of protein in an original ingredient amount do not increase just because water is pressed out**. Input weight, finished serving weight and food state must remain separate.

## Ranking

1. Filter to `group=plant`; beef is `group=reference`.
2. Apply numeric hard constraints: budget, minimum estimated protein, maximum preparation time.
3. If none passes, show `no feasible option`.
4. For feasible options, rank by: 45% remaining budget margin, 25% reaching target, 15% prep time, 15% experimental TF-IDF similarity to preparation preference. Coefficients are provisional and **not learned or validated**.
5. Show a cheapest-only baseline and the complete reasons/source strings.

The TF-IDF component is genuine text-based vector matching but **is not proof of a successful AI innovation**. Muhammad should benchmark it versus simple keyword matching, cheapest-feasible ranking and, if authorised, a richer ingredient-substitution model. The judges should see clear evidence that the method helps the restaurant decision.

## Engineering acceptance

- Unit tests for all constraints, no-option behavior, ingredient provenance, plant-only guard, multi-dish generic support and shock sensitivity.
- Streamlit has a conspicuous demo warning and does not silently fallback from verified to demo.
- No API secrets or personal contact details in git history.
- Documentation explains provenance and current limitations.
- CI runs automated tests on PRs.
