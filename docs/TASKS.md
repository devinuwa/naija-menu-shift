# Team action board — 12–13 November 2026

**Status at package creation:** code scaffolding and synthetic checks complete locally; real source data and end-user validation are outstanding. This is not a record of completed team validation.

## Ibrahim — cost/code integration
- [x] General-purpose repository structure, data files and cost formulas (local starter).
- [x] Separate beef reference; cheapest-only and cheapest-feasible baselines.
- [x] ±20% price scenarios and automated fixture tests.
- [ ] Review actual price/unit source details with Amina and integrate her validated dataset.
- [ ] Re-run tests and check scenarios with realistic budgets/protein targets.
- [x] Create private GitHub repository and send invites (reported by owner).
- [ ] Verify first remote push, CI and collaborator acceptance.

## Muhammad Inuwa — ranking, Streamlit and presentation
- [x] Starter Streamlit app, results table, cost chart, rationale and text-retrieval scoring included as scaffolding.
- [x] Compare keyword and TF-IDF hybrids with cheapest baselines on a frozen synthetic set. Weights stay 45/25/15/15; that set does not justify retuning. See `docs/EVALUATION_PROTOCOL.md`.
- [x] Decision studio shows cost split, protein, beef as a reference, ranker disagreement, and empty states for no-feasible and missing research files.
- [x] Keyword overlap is the transparent baseline beside experimental TF-IDF. The crispy-fried case is a recorded disagreement, not a taste result.
- [x] Three useful synthetic cases plus one impossible budget are presets in the app and recorded in `docs/EVALUATION_PROTOCOL.md`.

## Amina — research, sources and validation
- [x] Data schema and editable blanks prepared in `data/verified`.
- [ ] Confirm problem statement and user success metric.
- [ ] Source/date/location of beef, tofu and preparation ingredient price *ranges*.
- [ ] Source protein, iron and zinc per 100g **for exact food state**.
- [ ] Provide purchase and finished weights, energy/fuel, cooking oil and servings.
- [ ] Review tool calculations, document uncertainties and chef/restaurant feedback.

## Whole team — before hackathon
- [ ] Agree single-serving definition and nutritional/price normalization.
- [ ] Ask organisers about pre-event coding/building rules and final deliverables.
- [ ] Secure at least one kitchen/food domain reviewer.
- [ ] Define success on real data; record tests and limitations.
- [ ] Decide whether to expand to a second dish **only after** the complete suya path is testable.
- [ ] Rehearse a 3–5 minute pitch showing one real constraint shift and honest caveats.
