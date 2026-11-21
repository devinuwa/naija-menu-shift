# Research, provenance and validation checklist

## Amina's data assignment

- [ ] Confirm problem statement with a restaurant/food operator; capture the decision they would actually make.
- [ ] Find **dated** minimum, typical and maximum beef/tofu/seasoning/oil unit prices in a specified Nigerian market, with seller/document/source and collection date.
- [ ] Find protein (g), iron (mg) and zinc (mg) per 100 g for each ingredient from a documented food composition table; record edible portion, firm/soft tofu type, and raw/cooked/processed state.
- [ ] Confirm **purchase quantities** for each preparation; separately measure post-press/post-thaw/fried product **finished serving mass**, cooking losses and oil uptake.
- [ ] Estimate energy/fuel + time/labour separately per serving; note assumed appliance power/time or actual metering.
- [ ] Review calculations, pricing, limitations, hidden animal ingredients and allergens.
- [ ] Ask a restaurant operator and a food scientist/chef to score kitchen feasibility; preserve consent and do not publish private quotations.

## Data entry

`data/verified/*.csv` contain only headers. Copy the schema and enter actual sourced rows. **Do not copy synthetic data into verified mode.** The loader rejects incomplete rows and demo markers, but it cannot independently prove a URL or quoted number is genuine. Human review is required.

| Field | Evidence needed |
|---|---|
| `price_ngn_per_kg` | NGN for 1 kg equivalent; for oil or other measured volumes record conversion method outside CSV |
| `price_date`, `price_region`, `price_source` | ISO 8601 date, physical location, specific supplier/document and link/ID |
| `protein_g_per_100g`, `iron_mg_per_100g`, `zinc_mg_per_100g` | Published food-composition value for exact food form; do not mix raw beef and cooked tofu |
| `nutrition_source`, `nutrition_state` | Specific table/page/entry, product state; note missing analytes as unavailable, never zero by default |
| `purchase_g` | Actual purchased edible ingredient amount **per serving** |
| `nutrient_retention_fraction` | Experimental retention **assumption**, not evidence; 1.0 is not a guarantee of zero loss |
| `finished_weight_g` | Output serving mass from measurement, not an arbitrary yield |
| `energy_cost_ngn`, `labour_cost_ngn`, `other_cost_ngn` | Recorded per-serving cost assumption/estimate; explain calculation |

> Current nutrient model uses one retention fraction per ingredient for all three nutrients. This is a simplifying limitation, not a scientifically sound substitute for analyte-specific, preparation-specific retention measurements. Do not cite the synthetic demo as validated analysis.

## Starting sources to examine (not ingested/verified in this repository)

- [FAO/INFOODS West African Food Composition Table](https://www.fao.org/food-composition/tables-and-databases/detail/food-composition-tables/en) — composition estimates; confirm exact food entry and state.
- [Nigeria National Bureau of Statistics Selected Food Price Watch](https://microdata.nigerianstat.gov.ng/index.php/catalog/162) — selected price context, not tofu supplier quotes.
- [Nigerian Embassy cuisine publication](https://nigerianembassythehague.nl/wp-content/uploads/2023/11/Netherlands-Food-Cuisine-Culture-Final-print-version_compressed.pdf) — dish context, not validation of substitutions.
- [NICO Nigerian cuisine overview](https://nico.gov.ng/cuisines-in-nigeria/) — background dishes and variants.

## Evaluation protocol

Create a small, pre-registered test matrix, e.g. budget lower than any plant option; protein target beyond available options; normal feasible budget; short preparation-time limit; 20% price rise switches ranking; a tofu method with missing price; an animal-based ingredient sneaking into a plant option. Record expected, actual, source, reviewer and any discrepancies.

Compare **A)** cheapest unconstrained option, **B)** cheapest *feasible* option, and **C)** structured recommendation plus experimental text similarity. If C is not demonstrably better on meaningful metrics, report that finding and improve the method rather than calling it AI success.

## Food safety and culinary limitations

- Tofu, groundnuts and wheat may be allergens. Ingredient labeling and cross-contamination must be reviewed in the real kitchen.
- Perishable tofu requires appropriate storage and handling; frozen-thawed processing creates a separate energy/cold-storage burden.
- Skewer integrity, chew, smoke, sensory acceptance and consumer demand are **untested** without a real tasting or chef assessment.
- Protein content is not protein quality, digestibility, bioavailability or nutritional equivalence.
