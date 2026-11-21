/**
 * Naija MenuShift engine — TypeScript mirror of the Python prototype.
 *
 * Semantics follow src/menushift/engine.py (evaluate) and
 * src/menushift/kitchen_optimizer.py (explore) in the main repository:
 *
 *  - Hard constraints first, always: plant-only, budget, minimum estimated
 *    protein, maximum preparation time, equipment subset, inventory subset,
 *    and allergen exclusions that fail closed (an exclusion that cannot be
 *    verified excludes the option; it never gets argued away by a score).
 *  - Peanut exclusion abstains entirely: standard suya yaji frequently
 *    contains groundnut/peanut, and this dataset has no verified yaji
 *    ingredient or label, so a peanut-free recommendation cannot be
 *    established (kitchen_optimizer.explore).
 *  - Score exists only for feasible options and is an explainable weighted
 *    breakdown: cost 0.45, protein utility 0.25, time 0.15, text match 0.15.
 *    The text match is a small TF-IDF cosine (the Python default), an
 *    experimental preference signal — not taste evidence.
 *  - Beef is a comparison reference only. It is evaluated so the UI can show
 *    it beside the plant options, and it is never feasible, never a
 *    candidate, and never recommended.
 *
 * The async `explore()` below is the ONLY entry point the UI uses. It calls
 * POST /api/explore; that route runs this same local implementation tonight
 * and proxies to the AWS-hosted Python engine tomorrow when
 * MENUSHIFT_ENGINE_URL is set — no UI changes needed.
 */

import {
  ALL_EQUIPMENT,
  ALL_INVENTORY,
  EQUIPMENT_REQUIREMENTS,
  INGREDIENTS,
  INVENTORY_ITEMS,
  METHODS,
  MILLING_PRICE_NGN_PER_KG,
  OIL_PRICE_NGN_PER_75CL,
  PRESS_LOSS,
  SOURCE_TO_INVENTORY,
  SOYBEAN_PRICE_NGN_PER_KG,
  type MethodDef,
} from "./data";

/* ------------------------------------------------------------------ types */

export interface Brief {
  budgetNgn: number;
  proteinTargetG: number;
  maxPrepMinutes: number;
  equipment: string[];
  /** null means "no stock restriction recorded" (mirrors Python's None). */
  availableIngredients: string[] | null;
  portionsG: number[];
  preference: string;
  avoidAllergens: string[];
  wetYieldKgPerKgDry: number;
  oilCl: number;
  priceShock: number; // -0.2 .. 0.2 scenario, not a forecast
  onionG: number;
  pepperG: number;
  saltG: number;
  seasoningG: number;
}

export const DEFAULT_BRIEF: Brief = {
  budgetNgn: 1500,
  proteinTargetG: 15,
  maxPrepMinutes: 120,
  equipment: [...ALL_EQUIPMENT],
  availableIngredients: [...ALL_INVENTORY],
  portionsG: [80, 100, 120, 140, 160, 180, 200],
  preference: "chewy grilled",
  avoidAllergens: [],
  wetYieldKgPerKgDry: 1.75,
  oilCl: 1.0,
  priceShock: 0,
  onionG: 0,
  pepperG: 0,
  saltG: 0,
  seasoningG: 0,
};

export interface IngredientLine {
  ingredientId: string;
  name: string;
  purchaseG: number;
  estimatedCostNgn: number;
  estimatedProteinG: number;
  priceSource: string;
  nutritionSource: string;
  nutritionState: string;
  allergenLabels: string;
}

export interface ScorePart {
  key: "cost" | "protein" | "time" | "text_match";
  label: string;
  value: number;
}

export interface Candidate {
  identifier: string;
  methodId: string;
  method: string;
  name: string;
  portionG: number;
  costNgn: number;
  ingredientCostNgn: number;
  processingCostNgn: number;
  proteinG: number;
  ironMg: number;
  zincMg: number;
  prepMinutes: number;
  feasible: boolean;
  reasons: string[];
  score: number | null;
  scoreBreakdown: ScorePart[];
  ingredientLines: IngredientLine[];
  requiredEquipment: string[];
  requiredInventory: string[];
  oilCl: number;
  allergens: string[];
  allergenReviewComplete: boolean;
  sources: string[];
  modelled: boolean;
}

export interface ReferenceEvaluation {
  optionId: string;
  name: string;
  portionG: number;
  costNgn: number;
  proteinG: number;
  prepMinutes: number;
  reasons: string[];
}

export interface ExploreResult {
  inspected: number;
  skippedEquipment: number;
  skippedIngredients: number;
  skippedUnverifiedYaji: number;
  candidates: Candidate[];
  eligibleIds: string[];
  frontierIds: string[];
  best: {
    budget: string | null;
    protein: string | null;
    kitchen: string | null;
    balanced: string | null;
  };
  reference: ReferenceEvaluation[];
  engineMode: "local" | "aws";
}

/* ---------------------------------------------------------------- helpers */

const round2 = (n: number) => Math.round(n * 100) / 100;
const round5 = (n: number) => Math.round(n * 100000) / 100000;

const ALLERGEN_ALIASES: Record<string, string> = {
  soya: "soy", soybean: "soy", soybeans: "soy", groundnut: "peanut",
  groundnuts: "peanut", peanuts: "peanut", gluten: "wheat",
  "wheat gluten": "wheat", dairy: "milk", casein: "milk",
};
const SUPPORTED_ALLERGENS = new Set([
  "soy", "peanut", "wheat", "milk", "egg", "sesame", "tree nut", "fish", "shellfish",
]);
function canonicalAllergen(text: string): string {
  const normalized = text.trim().toLowerCase().replace(/[_-]/g, " ").replace(/\s+/g, " ");
  return ALLERGEN_ALIASES[normalized] ?? normalized;
}
const UNCLEAR_ALLERGEN_LABELS = new Set([
  "unknown",
  "verify label",
  "unreviewed",
  "not checked",
  "pending",
  "?",
]);

function allergenInfo(allergenField: string): { labels: Set<string>; unreviewed: boolean } {
  const labels = new Set(
    allergenField
      .split(";")
      .map((p) => canonicalAllergen(p))
      .filter(Boolean),
  );
  const unreviewed =
    labels.size === 0 || [...labels].some((l) =>
      UNCLEAR_ALLERGEN_LABELS.has(l) || (l !== "none" && !SUPPORTED_ALLERGENS.has(l))
    ) || (labels.has("none") && labels.size > 1);
  for (const l of [...labels]) {
    if (UNCLEAR_ALLERGEN_LABELS.has(l) || l === "none" || !SUPPORTED_ALLERGENS.has(l)) labels.delete(l);
  }
  return { labels, unreviewed };
}

function tokens(text: string): string[] {
  return text.toLowerCase().match(/[a-z0-9]+/g) ?? [];
}

function ngrams(toks: string[]): string[] {
  const out = [...toks];
  for (let i = 0; i + 1 < toks.length; i++) out.push(`${toks[i]} ${toks[i + 1]}`);
  return out;
}

/**
 * Small TF-IDF cosine over unigrams+bigrams, mirroring the Python engine's
 * sklearn TfidfVectorizer(ngram_range=(1,2)) default closely enough for a
 * demo: smooth idf = ln((1+N)/(1+df)) + 1, raw-count tf, L2-normalised.
 * Experimental preference matching — not a predictor of taste or acceptance.
 */
function tfidfScores(texts: string[], preference: string): number[] {
  if (!preference.trim() || texts.length === 0) return texts.map(() => 0);
  const docs = texts.map((t) => ngrams(tokens(t)));
  const query = ngrams(tokens(preference));
  const corpus = [...docs, query];
  const n = corpus.length;
  const df = new Map<string, number>();
  for (const doc of corpus) {
    for (const term of new Set(doc)) df.set(term, (df.get(term) ?? 0) + 1);
  }
  const idf = (term: string) => Math.log((1 + n) / (1 + (df.get(term) ?? 0))) + 1;
  const vec = (doc: string[]) => {
    const m = new Map<string, number>();
    for (const term of doc) m.set(term, (m.get(term) ?? 0) + 1);
    for (const [term, count] of m) m.set(term, count * idf(term));
    const norm = Math.sqrt([...m.values()].reduce((s, v) => s + v * v, 0));
    if (norm > 0) for (const [term, v] of m) m.set(term, v / norm);
    return m;
  };
  const qv = vec(query);
  return docs.map((doc) => {
    const dv = vec(doc);
    let s = 0;
    for (const [term, qVal] of qv) {
      const dVal = dv.get(term);
      if (dVal) s += qVal * dVal;
    }
    return s;
  });
}

function proteinUtility(proteinG: number, targetG: number): number {
  return proteinG / (proteinG + Math.max(targetG, 1.0));
}

/* ------------------------------------------------------------- validation */

export function validateBrief(brief: Brief): void {
  const amounts = [
    brief.budgetNgn,
    brief.proteinTargetG,
    brief.maxPrepMinutes,
    brief.wetYieldKgPerKgDry,
    brief.oilCl,
    brief.priceShock,
    brief.onionG,
    brief.pepperG,
    brief.saltG,
    brief.seasoningG,
  ];
  if (amounts.some((v) => typeof v !== "number" || !Number.isFinite(v))) {
    throw new Error("All numeric inputs must be finite");
  }
  if (!(brief.budgetNgn > 0) || brief.proteinTargetG < 0 || !(brief.maxPrepMinutes > 0)) {
    throw new Error(
      "Budget and preparation time must be positive and protein target nonnegative",
    );
  }
  if (!(brief.wetYieldKgPerKgDry > 0 && brief.wetYieldKgPerKgDry <= 10)) {
    throw new Error("Wet-curd yield must be a positive plausible research assumption");
  }
  if (
    brief.oilCl < 0 ||
    [brief.onionG, brief.pepperG, brief.saltG, brief.seasoningG].some((x) => x < 0)
  ) {
    throw new Error("Ingredient inputs cannot be negative");
  }
  if (brief.priceShock < -0.2 || brief.priceShock > 0.2) {
    throw new Error("Price scenario must be between -20% and +20%");
  }
  if (typeof brief.preference !== "string" || brief.preference.length > 200) {
    throw new Error("Preference cannot exceed 200 characters");
  }
  if (!Array.isArray(brief.avoidAllergens) || brief.avoidAllergens.length > 10 ||
      brief.avoidAllergens.some((x) => typeof x !== "string" || !SUPPORTED_ALLERGENS.has(canonicalAllergen(x)))) {
    throw new Error("Unsupported allergen exclusion: request an ingredient-label review instead");
  }
  if (!Array.isArray(brief.equipment) || brief.equipment.length > 12 ||
      brief.equipment.some((x) => typeof x !== "string")) {
    throw new Error("Equipment must be a supported list");
  }
  if (brief.availableIngredients !== null &&
      (!Array.isArray(brief.availableIngredients) || brief.availableIngredients.length > 20 ||
       brief.availableIngredients.some((x) => typeof x !== "string"))) {
    throw new Error("Ingredient inventory must be a supported list");
  }
  const portions = brief.portionsG;
  if (
    !Array.isArray(portions) ||
    portions.length === 0 ||
    portions.length > 20 ||
    new Set(portions).size !== portions.length
  ) {
    throw new Error("Provide one to twenty distinct portion sizes");
  }
  if (portions.some((p) => !Number.isInteger(p) || p < 50 || p > 400)) {
    throw new Error("Portions must be whole grams between 50 and 400");
  }
  const allowedEquipment = new Set(ALL_EQUIPMENT);
  if (brief.equipment.some((e) => !allowedEquipment.has(e))) {
    throw new Error("Unsupported kitchen equipment");
  }
  if (brief.availableIngredients !== null) {
    const unknown = brief.availableIngredients.filter((i) => !(i in INVENTORY_ITEMS));
    if (unknown.length) {
      throw new Error(`Unknown inventory item(s): ${[...unknown].sort().join(", ")}`);
    }
  }
}

/* ------------------------------------------------------- option building */

interface BuiltOption {
  method: MethodDef | null; // null for the beef reference
  optionId: string;
  name: string;
  group: "plant" | "reference";
  prepMinutes: number;
  processingCostNgn: number;
  lines: { ingredientId: string; purchaseG: number }[];
  text: string;
}

function wetCurdPricePerKg(brief: Brief): number {
  // (soybean price + milling) / yield, as in sourced_menu.build_sourced_menu.
  return (SOYBEAN_PRICE_NGN_PER_KG + MILLING_PRICE_NGN_PER_KG) / brief.wetYieldKgPerKgDry;
}

function pricePerKg(ingredientId: string, brief: Brief): number {
  const def = INGREDIENTS[ingredientId];
  if (def.priceNgnPerKg === "derived_wet_curd") return wetCurdPricePerKg(brief);
  return def.priceNgnPerKg;
}

function buildOptions(brief: Brief, portionG: number): BuiltOption[] {
  const spices: { ingredientId: string; purchaseG: number }[] = [
    { ingredientId: "onion", purchaseG: brief.onionG },
    { ingredientId: "pepper", purchaseG: brief.pepperG },
    { ingredientId: "salt", purchaseG: brief.saltG },
    { ingredientId: "seasoning", purchaseG: brief.seasoningG },
  ].filter((s) => s.purchaseG > 0);

  const options: BuiltOption[] = [];
  for (const method of METHODS) {
    if (method.optionId === "awara_fried" && brief.oilCl <= 0) continue;
    const loss = PRESS_LOSS[method.optionId] ?? 0;
    const purchase = portionG / (1 - loss);
    options.push({
      method,
      optionId: method.optionId,
      name: method.name,
      group: "plant",
      prepMinutes: method.prepMinutes,
      processingCostNgn:
        method.optionId === "awara_fried"
          ? (brief.oilCl / 75) * OIL_PRICE_NGN_PER_75CL
          : 0,
      lines: [
        { ingredientId: method.mainIngredientId, purchaseG: purchase },
        ...spices.map((s) => ({ ...s })),
      ],
      text: `${method.name} ${method.textureTags} ${method.methodNotes}`,
    });
  }
  // Beef: comparison reference only. Same gram weight applied to a raw price
  // and a cooked nutrient row, exactly as the Python prototype presents it.
  options.push({
    method: null,
    optionId: "beef_suya",
    name: "Beef suya reference",
    group: "reference",
    prepMinutes: METHODS[0].prepMinutes,
    processingCostNgn: 0,
    lines: [{ ingredientId: "beef", purchaseG: portionG }],
    text: "Beef suya reference beef reference",
  });
  return options;
}

/* ------------------------------------------------------------- evaluation */

interface Evaluation {
  option: BuiltOption;
  costNgn: number;
  ingredientCostNgn: number;
  processingCostNgn: number;
  proteinG: number;
  ironMg: number;
  zincMg: number;
  feasible: boolean;
  reasons: string[];
  score: number | null;
  scoreBreakdown: ScorePart[];
  allergens: string[];
  allergenReviewComplete: boolean;
  sources: string[];
  ingredientLines: IngredientLine[];
}

function evaluateOptions(options: BuiltOption[], brief: Brief): Evaluation[] {
  const avoid = brief.avoidAllergens.map(canonicalAllergen);
  const plantTexts = options.filter((o) => o.group === "plant").map((o) => o.text);
  const textScores = tfidfScores(plantTexts, brief.preference);
  const textByOption = new Map<string, number>();
  options
    .filter((o) => o.group === "plant")
    .forEach((o, i) => textByOption.set(o.optionId, textScores[i]));

  return options.map((option) => {
    let ingredientCost = 0;
    let protein = 0;
    let iron = 0;
    let zinc = 0;
    const allergenSet = new Set<string>();
    let anyUnreviewed = false;
    const sourceRefs = new Set<string>();
    const ingredientLines: IngredientLine[] = [];

    for (const line of option.lines) {
      const ing = INGREDIENTS[line.ingredientId];
      const price = pricePerKg(line.ingredientId, brief);
      const lineCost = (line.purchaseG * price) / 1000 * (1 + brief.priceShock);
      const lineProtein = (line.purchaseG * ing.proteinGPer100g) / 100; // retention fraction 1
      ingredientCost += lineCost;
      protein += lineProtein;
      iron += (line.purchaseG * ing.ironMgPer100g) / 100;
      zinc += (line.purchaseG * ing.zincMgPer100g) / 100;
      const info = allergenInfo(ing.allergens);
      if (info.unreviewed) anyUnreviewed = true;
      for (const l of info.labels) allergenSet.add(l);
      sourceRefs.add(
        `${ing.ingredientId}: price=${ing.priceSource}; nutrients=${ing.nutritionSource} [${ing.nutritionState}]`,
      );
      ingredientLines.push({
        ingredientId: ing.ingredientId,
        name: ing.name,
        purchaseG: round2(line.purchaseG),
        estimatedCostNgn: round2(lineCost),
        estimatedProteinG: round2(lineProtein),
        priceSource: ing.priceSource,
        nutritionSource: ing.nutritionSource,
        nutritionState: ing.nutritionState,
        allergenLabels: ing.allergens,
      });
    }

    const cost = ingredientCost + option.processingCostNgn;
    const plant = option.group === "plant";
    const affordable = cost <= brief.budgetNgn + 1e-7;
    const enough = protein + 1e-7 >= brief.proteinTargetG;
    const timely = option.prepMinutes <= brief.maxPrepMinutes;
    const conflicts = avoid.filter((a) => allergenSet.has(a)).sort();
    const unknownStatus = avoid.length > 0 && anyUnreviewed;
    // Compound seasoning has no reviewed animal-origin declaration.
    const unknownAnimalOrigin = plant && option.lines.some((l) => l.ingredientId === "seasoning");
    const feasible = plant && affordable && enough && timely &&
      conflicts.length === 0 && !unknownStatus && !unknownAnimalOrigin;

    const reasons: string[] = [];
    if (!plant) reasons.push("Beef/reference only; excluded from plant recommendations");
    if (!affordable) reasons.push("Exceeds ingredient-and-processing budget");
    if (!enough) reasons.push("Does not reach estimated protein target");
    if (!timely) reasons.push("Exceeds preparation time limit");
    if (conflicts.length)
      reasons.push(`Excluded labeled allergen(s): ${conflicts.join(", ")}`);
    if (unknownStatus)
      reasons.push("Cannot verify allergen exclusion; ingredient label review is incomplete");
    if (unknownAnimalOrigin)
      reasons.push("Seasoning animal-origin declaration unreviewed; cannot confirm plant-only status");

    let score: number | null = null;
    let breakdown: ScorePart[] = [];
    if (feasible) {
      const similarity = textByOption.get(option.optionId) ?? 0;
      const parts: ScorePart[] = [
        { key: "cost", label: "Cost (45%)", value: round5(0.45 * Math.max(0, 1 - cost / brief.budgetNgn)) },
        { key: "protein", label: "Protein (25%)", value: round5(0.25 * proteinUtility(protein, brief.proteinTargetG)) },
        { key: "time", label: "Time (15%)", value: round5(0.15 * Math.max(0, 1 - option.prepMinutes / brief.maxPrepMinutes)) },
        { key: "text_match", label: "Preference text match (15%)", value: round5(0.15 * similarity) },
      ];
      breakdown = parts;
      score = round5(parts.reduce((s, p) => s + p.value, 0));
      reasons.push("Passes budget, estimated protein and preparation constraints");
      reasons.push(
        `Preference text match (tfidf): ${similarity.toFixed(2)} (experimental, not taste evidence)`,
      );
    }

    return {
      option,
      costNgn: round2(cost),
      ingredientCostNgn: round2(ingredientCost),
      processingCostNgn: round2(option.processingCostNgn),
      proteinG: round2(protein),
      ironMg: round2(iron),
      zincMg: round2(zinc),
      feasible,
      reasons,
      score,
      scoreBreakdown: breakdown,
      allergens: [...allergenSet].sort(),
      allergenReviewComplete: !anyUnreviewed,
      sources: [...sourceRefs].sort(),
      ingredientLines,
    };
  });
}

/* ---------------------------------------------------------------- explore */

export function exploreLocal(brief: Brief): ExploreResult {
  validateBrief(brief);
  const avoidLower = new Set(brief.avoidAllergens.map(canonicalAllergen));

  const candidates: Candidate[] = [];
  const reference: ReferenceEvaluation[] = [];
  let inspected = 0;
  let skippedEquipment = 0;
  let skippedIngredients = 0;
  let skippedUnverifiedYaji = 0;

  const portions = [...brief.portionsG].sort((a, b) => a - b);
  for (const portion of portions) {
    const evaluations = evaluateOptions(buildOptions(brief, portion), brief);
    for (const ev of evaluations) {
      if (ev.option.group !== "plant") {
        reference.push({
          optionId: ev.option.optionId,
          name: ev.option.name,
          portionG: portion,
          costNgn: ev.costNgn,
          proteinG: ev.proteinG,
          prepMinutes: ev.option.prepMinutes,
          reasons: ev.reasons,
        });
        continue;
      }
      inspected += 1;
      const method = ev.option.method as MethodDef;
      const requirement = EQUIPMENT_REQUIREMENTS[ev.option.optionId];
      if (!requirement.every((e) => brief.equipment.includes(e))) {
        skippedEquipment += 1;
        continue;
      }
      const requiredInventory = new Set<string>();
      for (const line of ev.ingredientLines) {
        const inv = SOURCE_TO_INVENTORY[line.ingredientId];
        if (inv) requiredInventory.add(inv);
      }
      if (ev.option.optionId === "awara_fried") requiredInventory.add("oil");
      if (
        brief.availableIngredients !== null &&
        ![...requiredInventory].every((i) => brief.availableIngredients?.includes(i))
      ) {
        skippedIngredients += 1;
        continue;
      }
      // Standard Nigerian suya yaji frequently contains groundnut/peanut,
      // but this dataset lacks a verified yaji ingredient and label.
      // A "peanut-free suya" recommendation cannot be established.
      if (avoidLower.has("peanut")) {
        skippedUnverifiedYaji += 1;
        continue;
      }
      candidates.push({
        identifier: `${ev.option.optionId}@${portion}g`,
        methodId: ev.option.optionId,
        method: method.label,
        name: ev.option.name,
        portionG: portion,
        costNgn: ev.costNgn,
        ingredientCostNgn: ev.ingredientCostNgn,
        processingCostNgn: ev.processingCostNgn,
        proteinG: ev.proteinG,
        ironMg: ev.ironMg,
        zincMg: ev.zincMg,
        prepMinutes: ev.option.prepMinutes,
        feasible: ev.feasible,
        reasons: ev.reasons,
        score: ev.score,
        scoreBreakdown: ev.scoreBreakdown,
        ingredientLines: ev.ingredientLines,
        requiredEquipment: requirement,
        requiredInventory: [...requiredInventory],
        oilCl: ev.option.optionId === "awara_fried" ? brief.oilCl : 0,
        allergens: ev.allergens,
        allergenReviewComplete: ev.allergenReviewComplete,
        sources: ev.sources,
        modelled: method.modelled,
      });
    }
  }

  const eligible = candidates.filter((c) => c.feasible);
  const frontier = eligible.filter(
    (item) =>
      !eligible.some(
        (other) =>
          other !== item &&
          other.costNgn <= item.costNgn &&
          other.prepMinutes <= item.prepMinutes &&
          other.proteinG >= item.proteinG &&
          (other.costNgn < item.costNgn ||
            other.prepMinutes < item.prepMinutes ||
            other.proteinG > item.proteinG),
      ),
  );

  const pick = (
    compare: (a: Candidate, b: Candidate) => number,
  ): string | null => {
    if (!eligible.length) return null;
    return [...eligible].sort(compare)[0].identifier;
  };

  return {
    inspected,
    skippedEquipment,
    skippedIngredients,
    skippedUnverifiedYaji,
    candidates,
    eligibleIds: eligible.map((c) => c.identifier),
    frontierIds: frontier.map((c) => c.identifier),
    best: {
      budget: pick((a, b) => a.costNgn - b.costNgn || b.proteinG - a.proteinG),
      protein: pick((a, b) => b.proteinG - a.proteinG || a.costNgn - b.costNgn),
      kitchen: pick((a, b) => a.prepMinutes - b.prepMinutes || a.costNgn - b.costNgn),
      balanced: pick(
        (a, b) => (b.score ?? 0) - (a.score ?? 0) || a.costNgn - b.costNgn,
      ),
    },
    reference,
    engineMode: "local",
  };
}

/* -------------------------------------------------------- async interface */

/**
 * The single async entry point used by the UI. Posts the brief to
 * /api/explore, which runs a bounded local research-only engine.
 * No paid external LLM or unreviewed proxy is enabled.
 */
export async function explore(brief: Brief): Promise<ExploreResult> {
  const res = await fetch("/api/explore", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(brief),
  });
  const payload = (await res.json()) as ExploreResult & { error?: string };
  if (!res.ok) {
    throw new Error(payload.error ?? `Engine request failed (${res.status})`);
  }
  return payload;
}
