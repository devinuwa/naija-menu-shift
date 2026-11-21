// Any-dish suggestion engine (client port).
//
// Mirrors the hospital engine's gates over the baked catalogue: allergen
// exclusions fail closed, the method-survival screen uses the same rule
// table's verdicts, each survivor is portioned at the smallest standard
// portion that clears the protein floor, and survivors are ranked by
// protein delivered, then cost.

import { HOSPITAL_DATA } from "./hospital-data";
import type { Alternative } from "./hospital-types";

export interface AnyDishResult {
  alternative: Alternative;
  reasoning: string;
}

const round2 = (n: number) => Math.round(n * 100) / 100;
const fmt1 = (n: number) => (Math.round(n * 10) / 10).toString();

export function suggestAnyDish(input: {
  currentProtein: string;
  method: string;
  avoidKeys: string[];
}): AnyDishResult[] {
  const { pool, survival, baselines, proteinFloorG, portionsG } = HOSPITAL_DATA;
  const avoid = new Set(input.avoidKeys);
  const baseline = baselines[input.currentProtein];
  const results: AnyDishResult[] = [];

  for (const p of pool) {
    // Allergen gate - fail closed.
    if (p.allergens.some((a) => a.keys.some((k) => avoid.has(k)))) continue;
    // Method-survival screen (baked verdicts from the same rule table).
    const surv = survival[p.id]?.[input.method];
    if (!surv || !surv.survives) continue;
    // Protein floor at the smallest standard portion that clears it.
    let chosen: { portion: number; protein: number } | null = null;
    for (const portion of portionsG) {
      const protein = (p.proteinPer100g * portion) / 100;
      if (protein >= proteinFloorG) {
        chosen = { portion, protein };
        break;
      }
    }
    if (!chosen) continue;

    const alternative: Alternative = {
      proteinId: p.id,
      name: p.name,
      portionG: chosen.portion,
      proteinG: round2(chosen.protein),
      costNgn: round2((p.pricePerKg * chosen.portion) / 1000),
      prepMinutes: p.prepMinutes,
      allergens: p.allergens,
      functional: p.functional,
      kitchenMeaning: p.kitchenMeaning,
      reason: "",
    };

    const methodReason = surv.reasons[0] ?? "";
    const proteinLine =
      baseline && baseline.proteinPer100g != null
        ? ` It carries ${fmt1(p.proteinPer100g)} g protein per 100 g against ` +
          `${baseline.label.toLowerCase()}'s ${fmt1(baseline.proteinPer100g)} g.`
        : ` At a ${chosen.portion} g portion it clears the ${proteinFloorG} g ` +
          `protein floor for the dish.`;
    results.push({ alternative, reasoning: methodReason + proteinLine });
  }

  results.sort(
    (a, b) =>
      b.alternative.proteinG - a.alternative.proteinG ||
      a.alternative.costNgn - b.alternative.costNgn,
  );
  return results.slice(0, 3);
}
