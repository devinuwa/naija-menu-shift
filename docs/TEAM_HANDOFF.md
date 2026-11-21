# Team handoff · 12 November 2026

**Repository:** `Ibrahim-KIA/naija-menushift` · **Privacy:** keep private until all contributors approve release and claims.

## Scope
The product is a general AI-assisted menu-innovation system. **Suya is the first test case**, with four tofu preparation variants and beef reference; meat pie, egusi, jollof, and pepper soup are research candidates, not implemented complete solutions.

## Ibrahim · repo, cost and testing
- Keep the calculation engine generic, review the data model and source provenance.
- Verify cost equations, cheapest baseline, beef reference and ±20% price tests.
- Integrate Amina's real validated ingredient quotes and nutrition (do not change demo to appear real).
- Help Muhammad benchmark the candidate-ranking approach.

## Muhammad Inuwa (`devinuwa`) · recommendation and Streamlit
- Start a feature branch; review `app.py`, `src/menushift/engine.py`, `docs/EVALUATION_PROTOCOL.md`.
- Improve mobile/responsive experience, charts, calculations and explainability without hiding sample-data warnings.
- Propose an actual evaluated NLP/recommendation enhancement that demonstrably improves relevant decisions over simple filtering; do not make untested taste claims.
- Create PR with snapshots, tests and a short demonstration narrative.

## Amina · user and evidence research
- Finalize problem statement and measurable user-value criteria; discuss with at least one actual restaurant operator if possible.
- Populate `data/verified/*.csv` with dated/located Nigerian prices, per-100g nutrients and exact food states, measured or clearly estimated serving weights and prep overhead.
- Log safety/allergy uncertainties and verify sources. Provide a second-person review of the app numbers.

## Before the event
- Confirm pre-event development permissions with organisers.
- Complete one source-backed, technically valid, end-to-end suya demonstration; consider additional dishes only if time remains.
- Prepare 3 reproducible constraint scenarios and one honest no-feasible case for the jury.
- Issue trackers, reviews, CI and source quality are part of completion, not extras.
