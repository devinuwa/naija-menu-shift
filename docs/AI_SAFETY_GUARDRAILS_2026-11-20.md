# AI and food-decision guardrails — 20 November 2026

## Scope
Naija MenuShift is an **experimental constraint-based recommender with TF-IDF/keyword preference matching**, not a hosted generative LLM. Instructions typed into the preference box are treated as *data for similarity*, not commands. The tool does not write to files, execute user prompts, or connect to paid model endpoints.

**Safety promise:** The system must never advertise a recipe as food-safe, allergy-safe, nutritionally equivalent, commercially validated, or ready to serve solely because it passes budget/protein/time filters.

## Implemented guards

| Risk | Control | Residual limitation |
|---|---|---|
| Prompted bypass of dietary or budget constraints | Hard feasibility filters run independently of TF-IDF; user text does not change those filters. Overlong preferences rejected. | NLP may still rank a textually similar but unappealing preparation; no taste model exists. |
| Allergen synonym mismatch | Canonicalises soy/soya/soybean, peanut/groundnut, wheat/gluten, dairy/milk and other known variants, and checks selected exclusions using canonical labels. | Ingredient cross-contact is not tested; there are more allergens than the supported selection list. Unsupported exclusions fail with a clear error instead of being ignored. |
| Unreviewed ingredient label | If user selects an allergen restriction and *any recipe ingredient* has unknown/missing label status, the option is excluded. | A label marked “none” only means a recorded declaration; it is not a food-safety certification. |
| Compound products with undeclared animal content | An optional per-ingredient `animal_origin_reviewed` field is explicitly **false** for unreviewed seasoning cubes. If a research recipe uses one, it cannot pass plant-only eligibility until the label is checked. A missing origin declaration on a research ingredient also excludes it. | Simple raw ingredients are treated as plant by classification; no independent manufacturing or supply-chain certification is implied. |
| Unverified nutrients shown as zero | The engine keeps existing arithmetic but records `nutrition_reference_complete=false` and a prominent warning whenever zero placeholders represent unavailable records. | An estimate may still be incomplete. Never interpret a missing nutrient as genuinely absent. |
| Fake freshness/provenance | Undated workbook quotes are recorded as `price_date=unknown`, not as an invented November day. Unknown dates are allowed for **research only**; `load_dataset(..., demo=False)` uses stricter verified-data checks. Future dates rejected. Dated inputs older than 30 days are flagged as stale. | Even a recent price quote does not prove local supplier availability or equivalence across regions. |
| Misleading “approved” ranking | UI marks numerically qualifying outcomes **provisional** and shows evidence/safety warnings. `food_service_ready` remains false for all generated outputs. | Qualified human review, measurements and compliance procedures are still required before food sale or service. |
| Invalid/unbounded data | Existing schema rejects NaN, infinity, negative values, missing references, duplicate CSV columns, impossible prices and invalid ingredient proportions. | Research data may be wrong even if numeric syntax is valid. |
| Unsupported AI claims | Ranking is described as experimental TF-IDF plus transparent weighted scoring; it must be benchmarked against cheapest-feasible and independently reviewed food decisions. | No independent restaurant dataset yet demonstrates predictive performance or real-world uplift. |

## Validation and response contract
1. **User requirement**: known selected dish, budget, protein minimum, time limit, equipment and optional allergens.
2. **Input validation**: fail clearly for unsupported allergens, invalid dates, NaN/inf, malformed ingredient data and too-long preferences.
3. **Hard filters**: plant-only declaration review, budget, estimated protein, time, equipment, canonical allergens. An excluded option must have **no recommendation score**.
4. **Experimental ranking**: order the remaining *provisional* options; disclose how the score is obtained and why cheaper or higher-protein alternatives might appear elsewhere.
5. **Output warnings**: report undated/stale prices, incomplete nutrient references, unreviewed labels, unmeasured kitchen performance and missing approved recipe status.
6. **Human escalation**: do not prepare, advertise as allergy-safe, sell, or claim nutritional equivalence based on the output. Obtain exact label/ingredient verification, dated supplier quotations, measured serving yields, food-expert and regulatory review.

## Evidence and hackathon rules
The official Hack the Fork Nigeria 2026 participant guide states that AI should make a meaningful analytical or recommendation contribution; teams must distinguish measured facts from inferred estimates, and must **not claim experimental/market/model performance they have not demonstrated**. Challenge 2 asks for plausible plant-based transformations under culinary and price constraints, visible reasoning, and a working prototype—not a certified food product. No ingredient in the current ZIP or source workbook automatically becomes an approved finished recipe.

## Mandatory remaining work
- Validate at least one complete recipe with measured purchased/finished grams, oils, fuel, labour and confirmed allergen/compound seasoning labels.
- Confirm local pricing and quoted date/region (and correct any historic NBS vs WFP scope confusion).
- Record chef/restaurant evaluations before claiming model superiority to cheapest feasible.
- Perform actual anonymous, mobile, zoom and keyboard browser walkthroughs; automated tests cannot certify accessibility or food safety.
- If a generative LLM is added later, give it a **retrieval-only role** with untrusted sources, no tool execution, structured schema validation, output citations, refusal for harmful food claims and post-generation feasibility rechecking. These controls are not needed for the current deterministic recommendation engine.

## Key implementation
`src/menushift/safety.py` defines allergen/origin checks; `engine.py` preserves the hard filters and evidence status; `sourced_menu.py` supplies explicit origin declarations and honest unknown price dates; `quality.py` audits evidence gaps; `tests/test_ai_safety.py` covers synonym, adversarial, future-date and unknown-origin cases.
