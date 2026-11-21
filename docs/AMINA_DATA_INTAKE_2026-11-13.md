# Amina research intake — 13 November 2026

Source spreadsheet: https://docs.google.com/spreadsheets/d/1hs6y8OQfaEFRoJvjXuwQ6K42mV8q2csZleoK4KkT5Fo/edit

**Status: research/staging, not yet verified production data.** The source workbook was read without alteration. Market Prices (10 items) and Nutrition per 100g (5 records) have been transcribed into the adjacent CSV files. Do not copy to `data/verified/` or claim a real price/nutrition ranking until the following checks pass.

## What the submission supplies
- Ten price/cost observations: raw soybeans, boneless beef, vegetable oil, onions, fresh pepper, seasoning cubes, iodized salt, kerosene, cooking gas and milling.
- Five per-100g nutrition profiles: raw firm tofu, two moisture-loss calculations, fried tofu and cooked beef.
- Links or descriptive references accompanying the values. Some supplied sources are generic catalogues, news articles, retail category pages or an informal vendor estimate rather than an exact dated quote.

## External spot-checks conducted on 13 November 2026
- Mansa Markets Nigeria soybean exchange benchmark shows around NGN 643.6/kg as of 10 Nov 2026. This is a market exchange benchmark, **not** the price of purchased local awara, and cannot be used as raw tofu `price_ngn_per_kg` without measured conversion yields and manufacturing costs.
- The NBS Selected Food Price Watch for May 2026 shows boneless beef average ~NGN 7,171.41/kg. It is a national average *retail raw beef* figure, not an actual Abuja/Zaria restaurant supplier quote or cooked-beef price.
- USDA legacy FDC 172475 firm tofu provides ~17.3 g protein/100g, and FDC 172451 fried tofu ~18.8 g/100g. The exact calcium-set tofu products in those records are not confirmed equivalent to local awara or the team's fried/pressed recipe.
- Pressed 21.6 g and freeze-thawed 23.1 g protein per 100g are calculations (17.3/0.8 and 17.3/0.75), **not independent laboratory measurements**. Both assume no protein solids are lost and the stated total mass loss occurs. A 100g finished pressed portion and 100g purchased portion cannot be treated as the same purchase mass.

## Missing before the engine may use 'verified' mode
1. **Actual purchased tofu/awara price** per kg or measured local raw-soy-to-tofu yield, date, location, coagulant/water and labour/energy cost. Set an explicit origin and handling assumption.
2. **Price quote date + geography + ranges** for every ingredient. Several price entries show no source month; nominal market prices are not a supplier quotation.
3. **Normalize units:** oil in 0.75L, salt in 500g, seasoning in 100×4g, kerosene in L, LPG in kg, milling per batch. Don't divide volume prices by kilograms. Unit conversions must document density where needed.
4. **Finished serving recipe:** purchased grams of tofu, yaji, spices, oil and retained oil; measured before/after weights per method; cooking yield and quantities for beef reference. Compute cost per finished serving, not simply ₦/kg raw.
5. **Nutrients for exact food state:** local awara composition may differ from calcium-set USDA tofu, and cooked beef composition cannot be paired with raw mass without yield. Verify iron and zinc entries from exact food records and retain uncertainties.
6. **Processing costs:** fuel or electricity use per batch, refrigerating/freezing time, water/pressing, frying oil absorption, local labour and batch size. Do not count mutually exclusive fuels twice.
7. **Recipe feasibility and safety:** declared soy/peanut allergens, no hidden animal seasonings, kitchen feasibility and texture/skewer stability checks. Taste is *not measured*.
8. **Review/approval:** food researcher checks assumptions; Ibrahim runs cost and ±20% test matrix on actual serving units; Muhammad benchmarks recommender. Then copy approved rows into `data/verified/` through a reviewed PR.

## Recommended calculation model
- Purchase cost = sum(quantity consumed or purchased for one serving × quote in matching units); process and fixed costs explicitly separated.
- Nutrient per finished serving = sum(purchased edible ingredient mass × exact starting-state nutrients / 100 × analyte-specific retention, if known); measured finished weight governs per-100g *display density*.
- When nutrient retention is unknown, disclose estimate/uncertainty instead of asserting precision. The prototype currently uses one retention factor for all analytes, a limitation.
- Keep beef strictly as comparison baseline, never a candidate plant-based recommendation.

## Source trace
This import is an exact-research-data capture in `data/research/`, **not** approval of the values for official recommendations. The source spreadsheet remains unchanged.
