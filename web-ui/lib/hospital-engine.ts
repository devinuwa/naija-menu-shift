// Any-dish suggestion engine (client port).
//
// Mirrors the hospital engine's gates over the baked catalogue: allergen
// exclusions fail closed, the method-survival screen uses the same rule
// table's verdicts, each survivor is portioned at the smallest standard
// portion that clears the protein floor, and survivors are ranked by
// protein delivered, then cost.

import { HOSPITAL_DATA } from "./hospital-data";
import type {
  Alternative,
  FunctionalProfile,
  PoolProtein,
} from "./hospital-types";

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

export interface AnyDishMiss {
  alternative: Alternative;
  note: string;
}

function buildAlternative(p: PoolProtein, portion: number): Alternative {
  return {
    proteinId: p.id,
    name: p.name,
    portionG: portion,
    proteinG: round2((p.proteinPer100g * portion) / 100),
    costNgn: round2((p.pricePerKg * portion) / 1000),
    prepMinutes: p.prepMinutes,
    allergens: p.allergens,
    functional: p.functional,
    kitchenMeaning: p.kitchenMeaning,
    reason: "",
  };
}

// Nearest miss for the any-dish form: when no protein passes every gate,
// find the ones that fail exactly one gate and surface the best of them with
// a plain-language note, so the kitchen always gets a next step instead of
// a dead end. Priority: a protein that is only short on protein (shown at
// the largest standard portion), then one blocked only by the cooking
// method, then one blocked only by an allergy choice.
export function nearestMissAnyDish(input: {
  currentProtein: string;
  method: string;
  avoidKeys: string[];
}): AnyDishMiss | null {
  const { pool, survival, proteinFloorG, portionsG } = HOSPITAL_DATA;
  const avoid = new Set(input.avoidKeys);
  const maxPortion = portionsG[portionsG.length - 1];

  interface Scored {
    miss: AnyDishMiss;
    protein: number;
    cost: number;
  }
  const floorMisses: Scored[] = [];
  const methodMisses: Scored[] = [];
  const allergenMisses: Scored[] = [];

  for (const p of pool) {
    const allergenFail = p.allergens.some((a) =>
      a.keys.some((k) => avoid.has(k)),
    );
    const surv = survival[p.id]?.[input.method];
    const methodFail = !surv || !surv.survives;
    let clearingPortion: number | null = null;
    for (const portion of portionsG) {
      if ((p.proteinPer100g * portion) / 100 >= proteinFloorG) {
        clearingPortion = portion;
        break;
      }
    }
    const floorFail = clearingPortion === null;
    const failures =
      Number(allergenFail) + Number(methodFail) + Number(floorFail);
    if (failures !== 1) continue;

    if (floorFail) {
      const alt = buildAlternative(p, maxPortion);
      const short = round2(proteinFloorG - alt.proteinG);
      floorMisses.push({
        miss: {
          alternative: alt,
          note:
            `Closest option — ${p.name} gives ${fmt1(alt.proteinG)} g of ` +
            `protein in a ${maxPortion} g portion, ${fmt1(short)} g short ` +
            `of the ${fmt1(proteinFloorG)} g target.`,
        },
        protein: alt.proteinG,
        cost: alt.costNgn,
      });
    } else if (methodFail) {
      const alt = buildAlternative(p, clearingPortion as number);
      methodMisses.push({
        miss: {
          alternative: alt,
          note:
            `Closest option — ${p.name} gives enough protein, but it does ` +
            `not hold up with this way of cooking. Try a different way of ` +
            `cooking the dish.`,
        },
        protein: alt.proteinG,
        cost: alt.costNgn,
      });
    } else {
      const alt = buildAlternative(p, clearingPortion as number);
      const blocked = p.allergens
        .filter((a) => a.keys.some((k) => avoid.has(k)))
        .map((a) => a.label.toLowerCase())
        .join(" and ");
      allergenMisses.push({
        miss: {
          alternative: alt,
          note:
            `Closest option — ${p.name} fits the dish and gives enough ` +
            `protein, but it contains ${blocked}, which you asked to keep out.`,
        },
        protein: alt.proteinG,
        cost: alt.costNgn,
      });
    }
  }

  if (floorMisses.length > 0) {
    floorMisses.sort((a, b) => b.protein - a.protein || a.cost - b.cost);
    return floorMisses[0].miss;
  }
  if (methodMisses.length > 0) {
    methodMisses.sort((a, b) => a.cost - b.cost || b.protein - a.protein);
    return methodMisses[0].miss;
  }
  if (allergenMisses.length > 0) {
    allergenMisses.sort((a, b) => b.protein - a.protein || a.cost - b.cost);
    return allergenMisses[0].miss;
  }
  return null;
}
