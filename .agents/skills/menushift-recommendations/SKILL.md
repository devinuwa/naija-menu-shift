---
name: menushift-recommendations
description: Use when implementing or evaluating Naija MenuShift's recommendation, NLP matching, baseline comparisons, cost, constraints, sensitivity or scoring changes.
---
# Explainable recommendation engineering
1. Preserve hard constraints first: only plant formulations, total budget, minimum estimated protein, preparation time and declared allergens.
2. Never let any score override an exclusion or substitute beef as a plant recommendation. No feasible option is a valid outcome.
3. Keep cost decomposed into purchased ingredient cost and preparation overhead; state that the ±20% shock is a scenario, not a forecast.
4. Separate experiment features (TF-IDF text match) from verified outcomes. Do not call this a learned taste predictor.
5. For every proposed model improvement, define a dataset split/test case and compare with cheapest-only, cheapest-feasible and simple lexical baselines. Report both successes and failures.
6. Add regression tests for NaN/Infinity, unknown references, out-of-range fractions, allergen restrictions, mixed animal ingredients, stale sources and ranking stability.
7. Run `pytest -q` and `ruff check src tests app.py` before committing, include an explainable model-card update if claims change.
