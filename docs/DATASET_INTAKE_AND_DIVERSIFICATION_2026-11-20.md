# Muhammad dataset intake & menu diversification — 20 November 2026

## Positioning endorsed by the team
**Naija MenuShift helps restaurants diversify existing menus, adding suitable plant-based options without removing conventional choices.** Avoid "meat replacement" language in customer-facing work or presentations. This is a decision-support and research prototype, not an approved recipe marketplace.

## Files received and provenance
Original: Muhammad's [MenuShift Datasets Pack.zip](https://drive.google.com/file/d/1NHcCMyE3Es_kGtp-Rt5IB8Wjvyaw1WEi/view), 9.6 MB, SHA-256 `2847e89b085e4e056fca17ccc6db7aadfcc4c03c90117c7bc68cc0d81e1a716c`.

The original ZIP is **not** committed to GitHub. `data/curated/source_manifest.json` records source contents, source links and ingestion decisions.

## What was integrated, without silently altering recommendations
- **FAO/INFOODS WAFCT 2019:** 11 selected regional nutrient references per 100 g edible portion, with exact food IDs, names, raw/boiled/grilled state, protein, iron, zinc and kcal. Calculated food states retain `source_method` information.
- **USDA SR Legacy:** 4 generic food-composition references, including specific tofu and chicken FDC IDs and a generic “Meat extender.” **Generic Meat extender (41.71 g protein/100 g) is NOT Vchunks or any particular branded product.**
- **WFP Nigeria food prices:** 28 October/November 2026 monthly **state/commodity medians** derived from available market rows in **Borno and Yobe**. Every source row is already flagged `aggregate`; we retain this status, sample/market counts, dates, retail/NGN type, original unit and source. Only mass-unit observations receive ₦/kg normalisation. Oil sold per litre has **no** inferred ₦/kg.
- **NBS May 2026:** original report remains source evidence; existing `data/sources/nbs_2026.csv` is unchanged. Its national/zone/state averages are not new seller quotes.

New files: `data/curated/nutrition_references.csv`, `data/curated/wfp_market_snapshots.csv` and `src/menushift/evidence_catalog.py`. The new **Evidence Library** Streamlit page allows source exploration. All numeric recipe rankings and food costs still use their prior source tables and explicitly unmeasured assumptions.

## Sources intentionally not activated
- **HESTIA (2026-04-30, CC BY 4.0):** environmental comparisons need relevant product, country, year, functional unit and life-cycle boundary matching. No savings claims are calculated.
- **Open Food Facts (ODbL):** the submitted Nigeria subset includes many incomplete records. Combining it with a database can raise attribution/share-alike obligations. Verify exact branded pack, allergens and licence compliance before importing or using. [Official reuse guidance](https://support.openfoodfacts.org/help/en-gb/12-api-data-reuse/94-are-there-conditions-to-use-the-api).
- **Vchunks:** remains an attributable competitor example, not eligible for numeric recommendation without verified pack nutrition and measured cooking yield.

## Data quality and operational limits
1. WAFCT and USDA reference values are not measurements of local purchased awara, an experimental recipe or a final dish. Raw and boiled protein per 100 g should not be conflated.
2. A WFP November 2026 Borno price must never appear as a nationwide or Abuja/Zaria current price. Records in this extraction have source flag `aggregate`, not independently observed shop invoices.
3. Published NBS figures are historical benchmarks. A product needs dated supplier quotes in its actual city with exact package units.
4. A numeric formula passing a budget/protein threshold does not prove taste, cooking safety, demand or retailer acceptance.
5. The empty `data/verified/` tables and kitchen-trial template remain evidence gates.

## Practical integration steps after this release
- **Amina:** exact product-level nutrition and allergen labels, dated local supplier quotes and measured purchased/finished portions, plus source approval.
- **Muhammad:** use the source catalog for matching candidates and defensible citations, but do **not** auto-copy references into verified recipe data; maintain a benchmark against cheapest feasible.
- **Ibrahim/team:** collect chef trials (time, oil uptake, yields, fuel/labour and sensory observations), and validate whether the extra menu choices are commercially useful.

Only after specialist review should specific new menu formulations be enabled in the recommendation engine. No public-availability, model-accuracy, environmental-impact or meal-safety guarantee is implied.

## External primary sources
- [FAO/INFOODS WAFCT 2019](https://www.fao.org/infoods/infoods/tables-and-databases/faoinfoods-databases/en)
- [USDA FoodData Central](https://fdc.nal.usda.gov/)
- [WFP Nigeria food price data](https://data.humdata.org/dataset/wfp-food-prices-for-nigeria)
- [NBS Selected Food Price Watch](https://microdata.nigerianstat.gov.ng/index.php/catalog/162)
- [HESTIA](https://registry.opendata.aws/hestia/)
- [Open Food Facts licence](https://support.openfoodfacts.org/help/en-gb/12-api-data-reuse/94-are-there-conditions-to-use-the-api)
