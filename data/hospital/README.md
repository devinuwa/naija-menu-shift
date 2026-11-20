# Hospital food-service data — provenance and limits

This folder supports `src/menushift/hospital.py` and `pages/3_Hospital_Menu.py`:
decision support for diversifying a hospital menu with additional plant-protein
options. Nothing here is a served menu, a clinical guideline, or a food-safety
certification. Every transformation output requires dietitian sign-off before
service.

## unth_menu.csv — the menu

The 14 items are the most frequently consumed foods sampled from the menu of
the **therapeutic diet kitchen at the University of Nigeria Teaching Hospital
(UNTH), Ituku/Ozalla, Enugu**, as published in:

> Maduforo et al., "Evaluation of Diets Served to Cancer Patients in Oncology
> Ward of University of Nigeria Teaching Hospital, Ituku/Ozalla, Enugu State,"
> *Pakistan Journal of Nutrition* 15(2):104–111, 2016.

Limits that must travel with this data:

- It is a **high-calorie, high-protein therapeutic (oncology) diet kitchen
  menu**, not UNTH's general ward menu.
- The study does **not** split items into breakfast/lunch/dinner, and no menu
  cycle length is published. Neither is recorded here.
- The menu is from **2016**; whether it is still in use is **unverified**.
- Only two items carry a documented animal protein: **fish** and **meat**
  (type unspecified). **Stew** and the three soups are listed without stated
  contents — this dataset never assigns them a protein.
- Moi-moi, okpa, beans-and-yam pottage and pap are already plant-based as
  documented; they are evidence the kitchen already serves plant proteins,
  not transformation targets.
- No published national patient menu exists for Nigerian government hospitals,
  and no other federal teaching hospital in the team's research published a
  full menu chart. This is the best available evidence, and it is partial.

## protein_prices.csv — prices, prep times, roles

- Prices reuse the project's verified swap-database records (WFP Nigeria 2026
  retail medians, NBS, and team market records). Rows whose price is modelled
  or proxied carry `price_derived=true` and the derivation in `price_basis`.
  Prices are planning estimates for comparison, **not supplier quotes**, and
  most are undated listings (`price_date=unknown`) — the engine surfaces that
  as an explicit warning rather than letting it pass silently.
- `prep_minutes` are **planning estimates, not measured kitchen times**; the
  basis column says what each estimate assumes.
- `role`: `candidate` proteins are ranked as alternatives; `dawadawa` is an
  `adjunct` (a seasoning used at 5–10 g per serving — never portioned as a
  main protein); `beef` is a `reference` used only to cost the UNTH "meat"
  item for comparison. There is **no fish price or protein-density row** in
  the project data (the UNTH study reports fish only as a relative protein
  density index, 851.28%), so the fish dish has no costed original — the
  module says so instead of estimating one.
- Allergen labels use the engine's controlled vocabulary (`soy`, `wheat` for
  gluten — seitan IS wheat gluten). `none` means "no declared allergen on the
  reviewed label"; it is not a cross-contact certification.
- All candidate rows are single-ingredient plant foods whose identity is the
  cited dataset row; that is the basis for `animal_origin_reviewed=true` when
  the engine dataset is built.
- Portion model: purchased grams = served grams and nutrient retention = 1.0.
  No yield, cooking-loss or retention measurements exist for these hospital
  portions; both are optimistic planning simplifications, stated here so they
  are never mistaken for measurements.
- Iron and zinc are **not recorded** for these proteins in this module. The
  engine dataset carries explicit "no nutrient row" markers so totals report
  them as missing data, never as measured zeros presented as fact.

## Therapeutic presets (in hospital.py)

Preset definitions come from a University of Port Harcourt Teaching Hospital
(UPTH) dietetics placement report (SIWES, Oct 2024) describing modified diets:

- High protein: 1.5–2.0 g/kg body weight/day (accident, malnourished,
  post-surgical, burns patients).
- Low protein: 20–60 g/day (kidney disease, liver disease, phenylketonuria).
- Low sodium: little added salt, high-sodium foods minimised (heart disease,
  hypertension, oedema, kidney failure).

The module converts daily ranges to per-meal figures by dividing by three
meals (the documented Nigerian hospital pattern) and, for the high-protein
preset, assumes a 70 kg reference adult. Both conversions are arithmetic on
the cited ranges, labelled as assumptions wherever they are shown — they are
not clinical guidance. The low-sodium preset applies **no numeric filter**:
the engine's datasets contain no sodium values, so the module states that
limitation instead of inventing one.

## Patient conditions (in hospital.py)

On top of the presets, the module carries a CONDITIONS registry: each
condition maps to one of the documented presets above and attaches the
team's cited evidence together with the limits of that evidence.
Conditions change constraints and attach evidence — they are not clinical
rules and never turn an output into a prescription.

- **Cardiovascular disease** → the low-sodium preset's posture (UPTH
  places heart-related diseases under the low-sodium diet) plus the
  standard protein floor; allergen gates unchanged. Evidence notes quote
  a West African meta-analysis of dietary factors and hypertension
  (Batubo et al., *Journal of Hypertension*: red meat OR 1.51, 95% CI
  1.04–2.18; dietary fat OR 1.76; salt OR 1.25; fruit and vegetables
  protective), a Lagos survey (n=2,244), and a supervised plant-based
  lifestyle-medicine programme evaluation (NYC Bellevue, *Frontiers in
  Nutrition* 2023). The project data has **no sodium, saturated-fat or
  cholesterol values**, so no numeric filter on those nutrients is
  applied or claimed; UPTH's low-calorie element for cardiovascular
  patients is likewise not applied, because no per-serving calorie
  values exist here. Both limits travel with every output.
- **Hypertension** → the low-sodium preset, per the UPTH definitions,
  with the same meta-analysis evidence and Nigeria's 2023 national
  survey (hypertension in 22.9% of adults, 6.4% controlled) as context.
- **Kidney disease** → the low-protein preset, per the UPTH definitions.
  The mapping applies the protein-quantity element only; the data holds
  no other nutrient values for these proteins, so nothing else is
  filtered or claimed.
- **Diabetes** → the standard gates, with evidence notes from the team's
  patient-menu research: UNTH diabetic test meals (meat, beans and corn
  pottage with spinach lowest at GI 33.00 / GL 4.76; meat and okro soup
  with fermented cassava dough highest at GI 74.50 / GL 21.59; pap with
  okpa plant-based), the IMSUTH inpatient diabetic diet (85% of protein
  from legumes), and a Jos beans-and-acha regimen with poor glycaemic
  control as a caution. The data has **no glycaemic, carbohydrate or
  calorie values per candidate**, so no GI filter is applied or claimed.

`build_condition_menu()` composes a draft menu for a condition from the
14 documented items: already-plant items kept as documented (4), the two
documented-animal items diversified under the condition's bundle (2),
and the remaining items classified "confirm recipe with the kitchen" (8)
— never silently transformed. Totals are summed over the diversified
dishes' chosen alternatives only, because those are the only items with
cited per-serving values; no whole-menu total is shown. Every draft
carries the framing "draft menu to support dietary management of
[condition] — decision support for the dietitian, not a prescription and
not a served menu" and requires dietitian sign-off.
