---
name: menushift-streamlit-ui
description: Use when editing the Streamlit page, data visualizations, responsiveness, explanations, accessibility, or preparing the live Naija MenuShift demonstration.
---
# Streamlit experience workflow
1. Use Streamlit native controls and current official documentation. Install current Streamlit agent skill with `streamlit skills --yes` locally when available.
2. Put the user decision first: choose dish and constraints, show the top feasible alternative or a clear no-feasible state.
3. Clearly mark demo values as synthetic on every mode where they appear. Research mode must fail closed.
4. Make beef clearly a comparison reference, not a recommended plant option. Display nutrient units, cost breakdown, source references and uncertainty.
5. Use legible text, sufficient contrast, responsive columns/tables, keyboard-accessible inputs and non-color status labels.
6. Avoid user-controlled raw HTML and untrusted Markdown injection; prefer native text components for dynamic data.
7. Test on a narrow viewport, no-data mode, no-feasible state, protein threshold and price scenarios. Do not claim visual verification if only lint/tests ran.
