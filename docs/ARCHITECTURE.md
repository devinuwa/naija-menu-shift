# Architecture decisions · Naija MenuShift

## ADR 001 — data-first multi-dish foundation (2026-11-12)
**Decision:** local, normalized CSV data for dishes, ingredients, options and recipe items; a pure Python decision engine; a separate Streamlit presentation layer. Suya/4 tofu treatments are an initial experimental dataset, not a permanent product limit.

**Rationale:** free, offline-capable, testable, explainable and suitable for a two-day hackathon. No database, login system, paid APIs, or insecure public upload service is necessary yet.

**Trade-off:** CSV schema, provenance and food safety must be curated. Future storage (Postgres/API) can replace the reader without changing computation semantics. Multi-user authoring is not available.

## ADR 002 — auditability over unsupported AI claims
**Decision:** deterministic rules enforce hard constraints; a transparent weighted scorer ranks eligible candidates. An experimental TF-IDF similarity feature matches preparation preferences. Cheapest-only and cheapest-feasible options are shown as baselines.

**Rationale:** every output is inspectable. This is an AI *research experiment*, not a trained sensory prediction model. A stronger semantic model may be introduced only after a labeled evaluation set shows measurable value over simpler baselines.

**Boundary:** no automatic culinary safety certification, nutrient equivalence, taste prediction or restaurant endorsement.

## ADR 003 — fail-closed research mode
**Decision:** clearly synthetic demo data can power presentations. The research dataset fails if source, units, numeric fields or recipe rows are missing. No silent fallback.

## Data flow
```text
CSV dishes + ingredients + options + option_items
    -> schema validation + source records
    -> per-serving cost and nutrient arithmetic
    -> filter hard constraints / declared allergens
    -> tentative NLP preference similarity
    -> weighted ranking + cheapest baseline
    -> Streamlit explanation, beef reference, scenarios, evidence audit
```

## Threats & safeguards
- **Misinformation:** prominent demo label, source/date/food state, validation refusal on gaps.
- **Incorrect units:** purchase grams × NGN/kg / 1000; nutrient per 100 g × purchase grams / 100. Check food state.
- **Unsafe diet advice:** clear research-only warning; no health claims or verified allergy assurances.
- **Dependencies / code supply chain:** minimum GitHub Actions token permissions, SHA-pinned official actions, Dependabot, review on PRs.
- **Secrets:** none needed, `.env` and `.streamlit/secrets.toml` ignored; do not log credentials.
- **Data injection:** no external file uploads or arbitrary code execution in the UI; no user-provided HTML rendered dynamically.
- **Privacy:** no personal contact details in repository data.

## Future evolution (not yet implemented)
Typed Pydantic models, Postgres migration, real restaurant quotes and reviewer approval, energy measurement, ingredient-specific price uncertainty, richer semantic retrieval, trained/reviewed taste feasibility if a trustworthy local dataset becomes available.
