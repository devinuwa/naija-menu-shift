# Data integration — evidence gates and field guide

**14 November 2026 | State: interactive comparison from sourced prices; verified servings still closed**

The Streamlit studio compares the four awara methods with the workbook and the later 2026 NBS averages. It does not load `data/demo/`. Finished grams, the soy-yield note, minutes, oil, and spices are on-screen controls because the workbook has no measured serving. `data/verified/` stays empty.

## What is available and what is missing

| Input | Available | Needed before entering verified mode |
|---|---|---|
| Soybean benchmark | Market-price observation | Local seller quote AND either purchased finished tofu price or **measured** soy-to-tofu batch yield |
| Beef benchmark | NBS boneless beef per kg | Raw purchased quantity and actual cooked serving yield |
| Oil, onion, salt, seasoning | Package- or volume-price observations | Date, location, exact edible mass / oil uptake, labelled plant-only status; oil density if converting L → kg |
| Four tofu methods | Published generic nutritional profiles + moisture-loss assumptions | Actual recipe weights, measured retained solids/output mass, time, labour, heat/cold-chain costs |
| Protein, iron, zinc | Published *generic* food records | Exact local awara type, edible/preparation state and preparation-specific nutrient-retention uncertainty |
| Taste/skewer stability | Expert concerns, not laboratory evidence | Independent kitchen trial, dated feedback and preparation notes |
| Allergens | Some declared demo labels | Confirmed labels for every ingredient; unknown means do not certify suitability |

## Safe ingestion procedure

1. Keep original sheet unmodified and preserve dated links/price-region/source context.
2. Normalize **mass-based** package prices with `menushift.pricing.quote_ngn_per_kg`. Volume-based prices require a measured/sourced density if the recipe is recorded by mass. Do not count liquid fuel as a food ingredient.
3. If manufacturing awara rather than purchasing it, measure dry-soy kg and finished-tofu kg per **batch**, plus coagulant, energy, labour and miscellaneous batch costs. Use `tofu_manufacturing_cost_ngn_per_kg`, and attach the observation record. This produces a batch estimate, not a retail quote.
4. Record actual **purchased grams per portion**, measured finished serving grams and nutrient retention assumptions per recipe. For beef, pair the correct raw/cooked food state and measure cooking yield. Pressing removes water; it does not produce additional total protein.
5. Fill all four `data/verified/*.csv` tables with complete dated records. No fabricated zeros, source dates, labels, amounts, or prices.
6. Run `python -m pytest -q` and exercise all default, low-budget, high-protein, allergen, and ±20% scenarios.
7. Amina/food expert signs off the values, Ibrahim verifies full per-serving arithmetic, Muhammad compares rankings, and a restaurant operator reviews practical suitability.
8. Only after this evidence review is complete use Streamlit's research-data mode. Even then, a calculation is **not** a nutrition or food-safety certification.

## Recommendation evaluation protocol

- `data/evaluation/reviewer_cases.csv` has intentionally **zero** approved observations.
- An independent chef/restaurant reviewer records case ID, pseudonymous identifier (no email), role, date, evidence reference, scenario, approved preference and best option (`NONE` for no feasible option).
- Record these **before** tuning ranking weights to avoid cherry-picking.
- Run `python scripts/benchmark_reviews.py data/evaluation/reviewer_cases.csv` after verified input data and reviewer approvals are complete.
- The script returns agreement counts for cheapest feasible, lexical and TF-IDF. Do not claim uplift or quality until a representative labelled sample is collected.
- Test fixtures in `tests/test_review_benchmark.py` are synthetic, never real restaurant evidence.

## How to read the results

Use the four-step owner workflow: choose dish, set constraints, view eligible options, understand the explanation. Technical source tables and rankings are in secondary tabs. Never interpret `eligible` as allergen-free, delicious, nutritionally equivalent to beef or approved for sale.
