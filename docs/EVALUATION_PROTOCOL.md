# Model and business-evidence evaluation protocol

**Status: design only. There is no measured model uplift or Nigerian restaurant acceptance yet.**

## Research questions
1. Can every recommended plant alternative pass hard budget, estimated protein, preparation-time and declared-allergen checks?
2. Does NLP-assisted scoring yield more useful rankings than cheapest feasible alone on a small **independently labeled** set of chef/restaurant scenarios?
3. How stable are recommendations at −20%, baseline and +20% ingredient price scenarios?

## Proposed benchmark (do not report as achieved)
- Record at least 10 varied scenarios: tight/wide budget; high/low protein target; peanut exclusion; soy exclusion; short prep time; conflicting constraints; and a no-feasible case.
- Have a reviewer score candidate substitutions on relevance and practical feasibility **without seeing the model rank**.
- Report hard-constraint pass rate, ranking relevance at top 1 and top 3, number of abstentions and cost differences. Include confidence limitations and failed scenarios.
- Compare `cheapest unconstrained`, `cheapest feasible`, `keyword preference`, and `TF-IDF hybrid ranking` on the same cases. Do not claim statistically significant advantages from a tiny, hand-picked dataset.
- Freeze one evaluation set before tuning the weights; document changes openly.

## Nutrition and processing
- Confirm edible serving mass, source nutrient state, and recipe mass conservation. A water-loss concentration effect must not be represented as creating total protein.
- Protein, iron and zinc sums are provisional, not a nutrient quality or absorption guarantee.
- Verify pressing, freezing, frying and grilling protocols (energy, oil, loss, storage). Collect sensory feedback in separate records, not fabricated numeric scores.

## Synthetic benchmark notes (13 November 2026)

**Status: recorded on `data/demo/` only.** Every naira amount and nutrient below is fictional. This is not a chef review, not a taste result, and not a statistically significant model comparison. Weights were left at 45% cost, 25% estimated protein, 15% preparation time, and 15% text. The frozen cases did not justify retuning: one case shows a tiny TF-IDF margin, and another shows TF-IDF failing to follow a clear keyword match.

| Case | Constraints | Cheapest feasible | Keyword hybrid | TF-IDF hybrid | What happened |
|---|---|---|---|---|---|
| Normal serving | ₦1,500, 10 g, 120 min, "chewy smoky grilled" | plain marinated tofu (₦495) | pressed tofu (score 0.77050) | pressed tofu (score 0.67094) | Both text methods change the winner. The TF-IDF lead over plain tofu is about 0.002 score points. |
| Crispy fried preference | ₦5,000, 5 g, 180 min, "crispy fried" | plain marinated tofu (₦495) | fried tofu (score 0.88459) | plain marinated tofu (score 0.77628) | Methods disagree. Keyword overlap selects fried tofu. TF-IDF similarity is too small (text term 0.035) to overturn the cheaper option. |
| Short preparation window | ₦5,000, 5 g, 40 min, "chewy smoky grilled" | plain marinated tofu | plain marinated tofu | plain marinated tofu | Only one plant option is eligible. Text cannot change the winner. |
| No feasible plant option | ₦1, 10 g, 120 min | none | abstain | abstain | Every ranker abstains. Beef (illustrative ₦1,213) stays a reference. |

Soy exclusion on the same demo rows also makes every ranker abstain, because each plant recipe records soy. Repeating the same inputs reproduces the same order.

## Go / no-go
If data are insufficient or all options violate constraints, show no feasible option. If restaurant reviews reject a treatment, label it experimental and revisit the pilot dish/ingredient rather than forcing a winner.
