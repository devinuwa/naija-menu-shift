# Naija MenuShift — jury-ready menu diversification talk track

“Our goal is to help Nigerian restaurants diversify their menus with **additional plant-based options**, without asking them to stop serving traditional dishes.

Naija MenuShift is an explainable decision-support prototype. A restaurant chooses an existing menu context and its constraints: maximum cost, minimum estimated protein, preparation time, equipment and dietary restrictions. We show possible additional preparations, eliminate options that fail those rules and explain why remaining candidates may be worth a kitchen trial.

Suya is our first working numerical case, comparing four awara preparation methods while keeping conventional beef suya as a separate reference. We also show a preliminary jollof protein-side example, explicitly excluding the cost and nutrition of rice, sauce and the original chicken. We don't present that as a complete or validated meal.

Our tool ranks eligible candidates with transparent criteria and experimental TF-IDF preference matching, then compares them to simpler cheapest-feasible choices. The Kitchen Studio also shows cost-first, protein-first and time-first possibilities and Pareto trade-offs.

The new Evidence Library provides traceable FAO and USDA reference nutrients and WFP regional historical market snapshots. These are **not live supplier prices** and do not automatically become approved recipe data. We still need real kitchen measurements and independent food-practitioner reviews before saying a proposed menu addition is ready for sale.

We're building more choices for Nigerian menus, supported by transparent reasoning and clear evidence limits.”

## Suggested live demonstration

1. Open the Streamlit Research Studio and state the unmeasured recipe limitations.
2. Choose **suya** and enter a restaurant budget and protein preference.
3. Show feasible options, the hard-filter explanation, budget/protein/time trade-offs and beef as a separate reference.
4. Open **Kitchen Intelligence** to inspect equipment limits, serving-size assumptions and Pareto choices.
5. Show the **jollof protein-side** selector while explicitly acknowledging it is a partial exploratory option.
6. Open **Evidence Library** and select WFP Borno November 2026 rice or cowpea historical price. Explain market region, date and package-unit conversion; show FAO boiled cowpea versus raw cowpea for nutritional food-state importance.
7. Finish with what still needs evidence: local price quotations, kitchen yields, energy costs, allergen checks, independent restaurant evaluation.

Avoid: "we replace beef", "the AI guarantees taste", "verified live prices", "complete jollof nutrition" or "Vchunks-equivalent protein" without actual evidence.
