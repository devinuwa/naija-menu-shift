# Contributing

1. Agree on an issue and acceptance criteria. Branch from `main` using `feature/`, `data/` or `fix/`.
2. Make the smallest change that can be reviewed independently; use pull requests for integration.
3. Run `pytest -q` and `ruff check src tests app.py` after installing the `dev` extra.
4. Do not replace sourced data with synthetic/demo values. Commit source citations and calculation assumptions in `docs/RESEARCH_AND_VALIDATION.md`.
5. When updating `data/verified`, record supplier/source, location, quote date, nutrition source, and raw-vs-cooked state.
6. Never commit private restaurant data without permission, personal contact addresses, API credentials, or secret files.
7. Keep domain logic in `src/menushift/` and interface logic in `app.py`; avoid suya-specific conditionals in the generic engine.
8. Seek at least one independent review before merging changes to food- or nutrition-related calculations.

## Proposed branches
- `data/source-audit` — Amina: source-backed real data and limits.
- `feature/streamlit-ranking` — Muhammad Inuwa: explainability, UI and NLP experiment.
- `feature/cost-and-benchmark` — Ibrahim: tests, comparison, sensitivity and baseline.

Access requires accepting the repository invitation; branches are proposals, not already created on GitHub.
