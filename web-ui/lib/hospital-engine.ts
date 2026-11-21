// Any-dish suggestion engine (client port).
//
// Mirrors the hospital engine's gates over the baked catalogue: allergen
// exclusions fail closed, the method-survival screen uses the same rule
// table's verdicts, each survivor is portioned at the smallest standard
// portion that clears the protein floor, and survivors are ranked by
// protein delivered, then cost.

import { HOSPITAL_DATA } from "./hospital-data";
import type { Alternative, FunctionalProfile } from "./hospital-types";

const METHOD_VERB: Record<string, string> = {
  grill: "grilling",
  fry: "frying",
  boil: "boiling",
  soup: "soups and stews",
  steam: "steaming",
};

// Plain-word descriptions of what each cooking behaviour means, used only
// for behaviours the protein is genuinely strong or fair at (baked levels).
const TRAIT_PHRASE: { key: keyof FunctionalProfile; phrase: string }[] = [
  { key: "gelation", phrase: "it sets and holds together when cooked" },
  { key: "waterHolding", phrase: "it soaks up water, so it stays juicy" },
  { key: "emulsification", phrase: "it mixes smoothly into sauces" },
  { key: "solubility", phrase: "it dissolves into the cooking liquid" },
];

function traitPhrases(functional: FunctionalProfile): string[] {
  const scored = TRAIT_PHRASE.map((t) => ({
    phrase: t.phrase,
    strength: functional[t.key] === "High" ? 2 : functional[t.key] === "Moderate" ? 1 : 0,
  })).filter((t) => t.strength > 0);
  scored.sort((a, b) => b.strength - a.strength);
  return scored.slice(0, 2).map((t) => t.phrase);
}

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

    const traits = traitPhrases(p.functional);
    const verb = METHOD_VERB[input.method] ?? "this cooking style";
    const methodLine =
      traits.length > 0
        ? `Good for ${verb}: ${traits.join(", and ")}.`
        : `It holds up well in ${verb}.`;
    const proteinLine =
      baseline && baseline.proteinPer100g != null
        ? ` It gives ${fmt1(p.proteinPer100g)} g of protein in every 100 g — ` +
          `the ${baseline.label.toLowerCase()} it stands in for gives ` +
          `${fmt1(baseline.proteinPer100g)} g.`
        : ` A ${chosen.portion} g portion gives ${fmt1(chosen.protein)} g of protein.`;
    results.push({ alternative, reasoning: methodLine + proteinLine });
  }

  results.sort(
    (a, b) =>
      b.alternative.proteinG - a.alternative.proteinG ||
      a.alternative.costNgn - b.alternative.costNgn,
  );
  return results.slice(0, 3);
}
