import type { Brief, Candidate } from "./engine";
import { DATASET_NOTE, MEASUREMENTS_NEEDED, TRIAL_STEPS } from "./data";

const naira = (n: number) =>
  `₦${n.toLocaleString("en-NG", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

/**
 * Kitchen trial worksheet (Markdown download), mirroring the handoff spec:
 * recipe ID, ingredient grams, price/nutrient sources, calculation caveats
 * and the field measurements still required. This is a research worksheet —
 * not a retail recipe and not approved for food service.
 */
export function buildWorksheet(candidate: Candidate, brief: Brief): string {
  const lines = candidate.ingredientLines
    .map(
      (l) =>
        `- ${l.name}: ${l.purchaseG} g — est. ${naira(l.estimatedCostNgn)}, est. protein ${l.estimatedProteinG} g\n  - Price source: ${l.priceSource}\n  - Nutrition source: ${l.nutritionSource} [${l.nutritionState}]\n  - Allergen labels on file: ${l.allergenLabels}`,
    )
    .join("\n");
  const steps = (TRIAL_STEPS[candidate.methodId] ?? [])
    .map((s, i) => `${i + 1}. ${s}`)
    .join("\n");
  const needed = MEASUREMENTS_NEEDED.map((m) => `- ${m}`).join("\n");
  const breakdown = candidate.scoreBreakdown
    .map((p) => `- ${p.label}: ${p.value}`)
    .join("\n");

  return `# Kitchen trial worksheet — ${candidate.identifier}

Naija MenuShift · Kitchen Intelligence Studio (research prototype)

> NOT approved for food service. This worksheet supports a supervised
> kitchen trial only. Costs are listed partial costs from research
> estimates; they are not a commercial price.

## Formulation
- Recipe ID: ${candidate.identifier}
- Method: ${candidate.method} (${candidate.name})
- Modelled finished portion: ${candidate.portionG} g
- Listed cost (incomplete): ${naira(candidate.costNgn)} — ingredients ${naira(candidate.ingredientCostNgn)} + processing ${naira(candidate.processingCostNgn)}
- Estimated protein: ${candidate.proteinG} g · Iron: ${candidate.ironMg} mg · Zinc: ${candidate.zincMg} mg
- Assumed preparation time: ${candidate.prepMinutes} min (modelled, not timed)
- Required equipment: ${candidate.requiredEquipment.join(", ")}
- Required stock: ${candidate.requiredInventory.join(", ")}

## Brief used
- Budget for listed partial costs: ${naira(brief.budgetNgn)}
- Protein target: ${brief.proteinTargetG} g · Max prep: ${brief.maxPrepMinutes} min
- Allergen exclusions requested: ${brief.avoidAllergens.join(", ") || "none"}
- Price scenario: ${Math.round(brief.priceShock * 100)}% (scenario, not a forecast)
- Wet-curd yield assumption: ${brief.wetYieldKgPerKgDry} kg per kg dry soy

## Ingredients
${lines}

## Why this formulation was suggested
${candidate.reasons.map((r) => `- ${r}`).join("\n")}

## Score breakdown (explainable; secondary to the hard constraints)
${breakdown || "- Not scored (constraints not met)"}
${candidate.score !== null ? `- Total score: ${candidate.score}` : ""}

## Trial steps (research observations)
${steps}

## Measurements still needed before any real recipe
${needed}

## Caveats
- ${DATASET_NOTE}
- Pressing and freezing do not create protein; denser figures are moisture recalculations.
- The yaji spice blend is not part of the sourced dataset; a full suya serving's allergen review is incomplete.
- Seasoning cube labels have not been reviewed for animal ingredients or allergens.
`;
}
