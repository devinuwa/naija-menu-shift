/**
 * Demo dataset for the Naija MenuShift web UI.
 *
 * SYNTHETIC DEMO DATA: the figures below mirror the team's research workbook
 * values (NBS Selected Food Price Watch transcriptions and USDA FoodData
 * Central references, retrieved 14 Nov 2026) so the interface behaves like the
 * Python prototype. They are NOT verified market measurements and must not be
 * presented as such. See the Python sources in src/menushift/sourced_menu.py
 * and data/sources/*.csv of the main repository.
 */

export const DATASET_NOTE =
  "Synthetic demo dataset — values mirror the team's research workbook for interface demonstration; not verified market measurements.";

export interface IngredientDef {
  ingredientId: string;
  name: string;
  /** NGN per kg. For wet/fried awara this is derived from soy + milling over the yield assumption. */
  priceNgnPerKg: number | "derived_wet_curd";
  proteinGPer100g: number;
  ironMgPer100g: number;
  zincMgPer100g: number;
  priceSource: string;
  nutritionSource: string;
  nutritionState: string;
  allergens: string;
  isAnimal: boolean;
}

/** Workbook quotes (NGN) used to derive the wet-curd price, as in sourced_menu.py. */
export const SOYBEAN_PRICE_NGN_PER_KG = 644; // Mansa Markets benchmark, workbook
export const MILLING_PRICE_NGN_PER_KG = 150; // informal vendor note, workbook
export const OIL_PRICE_NGN_PER_75CL = 3263.5; // NBS Selected Food Price Watch, May 2026

export const INGREDIENTS: Record<string, IngredientDef> = {
  wet_awara: {
    ingredientId: "wet_awara",
    name: "Wet awara curd",
    priceNgnPerKg: "derived_wet_curd",
    proteinGPer100g: 17.3,
    ironMgPer100g: 2.66,
    zincMgPer100g: 1.57,
    priceSource:
      "Mansa Markets soybean benchmark plus local milling note; workbook yield assumption (kg wet curd per kg dry soy)",
    nutritionSource: "USDA FoodData Central 172475 (firm tofu reference), via project workbook",
    nutritionState: "firm raw tofu reference applied to purchased wet curd",
    allergens: "soy",
    isAnimal: false,
  },
  fried_awara: {
    ingredientId: "fried_awara",
    name: "Fried awara",
    priceNgnPerKg: "derived_wet_curd",
    proteinGPer100g: 18.8,
    ironMgPer100g: 4.87,
    zincMgPer100g: 1.99,
    priceSource:
      "Wet-curd rate (soybean benchmark plus milling, over the yield assumption); fried piece priced at the wet-curd rate because starting weight is unmeasured",
    nutritionSource: "Published fried-tofu reference (MyFoodData 172451), via project workbook",
    nutritionState: "published fried-tofu reference per 100 g finished piece",
    allergens: "soy",
    isAnimal: false,
  },
  onion: {
    ingredientId: "onion",
    name: "Onions fresh",
    priceNgnPerKg: 1180.01,
    proteinGPer100g: 0,
    ironMgPer100g: 0,
    zincMgPer100g: 0,
    priceSource: "NBS Selected Food Price Watch, May 2026 national average (secondary transcription)",
    nutritionSource: "no nutrient row in the workbook",
    nutritionState: "price only",
    allergens: "unreviewed",
    isAnimal: false,
  },
  pepper: {
    ingredientId: "pepper",
    name: "Pepper (Fresh / Chili)",
    priceNgnPerKg: 1178,
    proteinGPer100g: 0,
    ironMgPer100g: 0,
    zincMgPer100g: 0,
    priceSource: "Workbook quote (NBS Selected Food Price Watch average)",
    nutritionSource: "no nutrient row in the workbook",
    nutritionState: "price only",
    allergens: "unreviewed",
    isAnimal: false,
  },
  salt: {
    ingredientId: "salt",
    name: "Iodized Table Salt",
    priceNgnPerKg: 350,
    proteinGPer100g: 0,
    ironMgPer100g: 0,
    zincMgPer100g: 0,
    priceSource: "Retail pack price from the workbook (₦175 per 500 g pack)",
    nutritionSource: "no nutrient row in the workbook",
    nutritionState: "price only",
    allergens: "unreviewed",
    isAnimal: false,
  },
  seasoning: {
    ingredientId: "seasoning",
    name: "Seasoning Cubes",
    priceNgnPerKg: 4750,
    proteinGPer100g: 0,
    ironMgPer100g: 0,
    zincMgPer100g: 0,
    priceSource: "Retail pack price from the workbook (₦1,900 per 100 × 4 g pack); package label not reviewed",
    nutritionSource: "no nutrient row in the workbook",
    nutritionState: "price only",
    allergens: "unknown;verify label",
    isAnimal: false,
  },
  beef: {
    ingredientId: "beef",
    name: "Beef boneless raw",
    priceNgnPerKg: 7171.41,
    proteinGPer100g: 29.5,
    ironMgPer100g: 2.88,
    zincMgPer100g: 6.8,
    priceSource: "NBS Selected Food Price Watch, May 2026 national average (secondary transcription)",
    nutritionSource: "USDA FoodData Central 170209 (cooked lean beef); not the nutrient content of the raw priced kilogram",
    nutritionState: "cooked lean per 100 g, shown beside a raw price",
    allergens: "unreviewed",
    isAnimal: true,
  },
};

/** Water-loss fractions from the workbook, as in sourced_menu.PRESS_LOSS. */
export const PRESS_LOSS: Record<string, number> = {
  awara_firm: 0.0,
  awara_pressed: 0.2,
  awara_frozen: 0.25,
  awara_fried: 0.0,
};

export interface MethodDef {
  optionId: string;
  /** Display label from kitchen_optimizer.METHOD_LABELS. */
  label: string;
  /** Option name as in sourced_menu definitions. */
  name: string;
  textureTags: string;
  methodNotes: string;
  /** Assumed preparation minutes for this demo (modelled, not measured). */
  prepMinutes: number;
  mainIngredientId: string;
  /** True when the nutrient density is a moisture recalculation rather than a published row. */
  modelled: boolean;
}

export const METHODS: MethodDef[] = [
  {
    optionId: "awara_firm",
    label: "Firm awara",
    name: "Firm awara (unpressed)",
    textureTags: "firm raw unpressed awara",
    methodNotes: "Wet curd at the finished weight. No press loss.",
    prepMinutes: 35,
    mainIngredientId: "wet_awara",
    modelled: false,
  },
  {
    optionId: "awara_pressed",
    label: "Pressed awara",
    name: "Pressed awara (20% water loss)",
    textureTags: "pressed firm chewy awara",
    methodNotes: "20% water loss from the workbook. Extra curd is purchased; protein is not created.",
    prepMinutes: 48,
    mainIngredientId: "wet_awara",
    modelled: true,
  },
  {
    optionId: "awara_frozen",
    label: "Frozen–thawed awara",
    name: "Frozen, thawed, pressed awara (25% water loss)",
    textureTags: "frozen thawed pressed chewy awara",
    methodNotes: "25% water loss from the workbook. Extra curd is purchased; protein is not created.",
    prepMinutes: 110,
    mainIngredientId: "wet_awara",
    modelled: true,
  },
  {
    optionId: "awara_fried",
    label: "Fried awara",
    name: "Fried awara",
    textureTags: "fried deep-fried awara",
    methodNotes: "Fried nutrient row on the finished weight, plus the oil volume you enter.",
    prepMinutes: 65,
    mainIngredientId: "fried_awara",
    modelled: false,
  },
];

/** Equipment each method requires, from kitchen_optimizer.EQUIPMENT_REQUIREMENTS. */
export const EQUIPMENT_REQUIREMENTS: Record<string, string[]> = {
  awara_firm: ["grill"],
  awara_pressed: ["grill", "press"],
  awara_frozen: ["grill", "press", "freezer"],
  awara_fried: ["grill", "frying_pan"],
};

export const EQUIPMENT_LABELS: Record<string, string> = {
  grill: "Grill",
  press: "Press",
  freezer: "Freezer",
  frying_pan: "Frying pan",
};

export const ALL_EQUIPMENT = Object.keys(EQUIPMENT_LABELS);

/** Inventory checklist, from kitchen_optimizer.INVENTORY_ITEMS. */
export const INVENTORY_ITEMS: Record<string, string> = {
  awara: "Fresh awara / tofu",
  onion: "Onions",
  pepper: "Fresh pepper",
  salt: "Salt",
  seasoning: "Seasoning (label review outstanding)",
  oil: "Vegetable oil",
};

export const ALL_INVENTORY = Object.keys(INVENTORY_ITEMS);

/** Maps sourced ingredient ids to inventory ids, from kitchen_optimizer.SOURCE_TO_INVENTORY. */
export const SOURCE_TO_INVENTORY: Record<string, string> = {
  wet_awara: "awara",
  fried_awara: "awara",
  onion: "onion",
  pepper: "pepper",
  salt: "salt",
  seasoning: "seasoning",
};

export const ALLERGEN_OPTIONS: { id: string; label: string; hint: string }[] = [
  { id: "soy", label: "Soy", hint: "Awara is a soy curd; excluding soy removes every current formulation." },
  {
    id: "peanut",
    label: "Peanut / groundnut",
    hint: "Standard suya yaji often contains groundnut and no verified peanut-free yaji is in the dataset, so the studio abstains.",
  },
];

/** Trial-worksheet steps per method: research trial observations, not food-service instructions. */
export const TRIAL_STEPS: Record<string, string[]> = {
  awara_firm: [
    "Weigh the dry soybeans and record the batch; note the yield assumption used in this formulation.",
    "Record the actual wet-curd weight after setting, and the finished weight of each trial piece.",
    "Apply the entered onion, pepper, salt and seasoning amounts; record any deviation.",
    "Grill one trial piece; record grill time and the finished weight after grilling.",
    "Record taster notes as research observations only; do not treat them as acceptance evidence.",
  ],
  awara_pressed: [
    "Weigh the dry soybeans and record the batch; note the yield assumption used in this formulation.",
    "Press the curd and record the actual water loss; compare it with the modelled 20%.",
    "Record the finished weight of each pressed trial piece before grilling.",
    "Apply the entered spice amounts; record any deviation.",
    "Grill one trial piece; record grill time and finished weight after grilling.",
  ],
  awara_frozen: [
    "Weigh the dry soybeans and record the batch; note the yield assumption used in this formulation.",
    "Record freeze duration and thaw method used for the trial batch.",
    "Press after thawing and record the actual water loss; compare it with the modelled 25%.",
    "Apply the entered spice amounts; record any deviation.",
    "Grill one trial piece; record grill time and finished weight after grilling.",
  ],
  awara_fried: [
    "Weigh the dry soybeans and record the batch; note the yield assumption used in this formulation.",
    "Record the oil volume before and after frying to estimate actual absorption; compare with the entered volume.",
    "Record the finished weight of each fried trial piece.",
    "Apply the entered spice amounts; record any deviation.",
    "Record frying time and finished weight; note oil cost separately from ingredient cost.",
  ],
};

export const MEASUREMENTS_NEEDED: string[] = [
  "Actual wet-curd yield from 1 kg dry soybeans in your kitchen (the model assumes a yield you can change).",
  "Actual water loss when pressing and after freeze–thaw, per batch.",
  "Actual preparation minutes per method, timed in your kitchen.",
  "Actual oil absorption for the fried method (volume before vs. after).",
  "A reviewed ingredient label for the seasoning cubes (animal ingredients and allergens).",
  "A verified peanut-free yaji formulation before any peanut-exclusion claim can be made.",
];

/**
 * Illustrative menu explorer items, inspired by the real menu of Veggie
 * Victory (Lagos — Nigeria's first vegan restaurant, est. 2013). These are
 * product-vision examples only: they are NOT engine outputs, carry no costed
 * formulation, and are shown to communicate the broader menu-shift idea.
 */
export interface MenuExplorerItem {
  name: string;
  style: string;
  description: string;
  proteinBase: string;
}

export const MENU_EXPLORER_ITEMS: MenuExplorerItem[] = [
  {
    name: "Vegan Jollof Rice",
    style: "Party-style rice, plant-based",
    description:
      "Smoky tomato-pepper jollof served with plant protein chunks — the celebration staple, re-based on soy.",
    proteinBase: "Soy chunks",
  },
  {
    name: "Egusi Soup",
    style: "Melon-seed soup",
    description:
      "Ground egusi seeds thicken the soup itself, so the protein is in the base; served with a swallow of choice.",
    proteinBase: "Egusi seed + soy chunks",
  },
  {
    name: "Efo Riro",
    style: "Leafy vegetable soup",
    description:
      "Rich spinach-style greens stewed with peppers, finished with curd pieces instead of assorted meat.",
    proteinBase: "Awara curd",
  },
  {
    name: "Vegan Suya",
    style: "Yaji-spiced grill",
    description:
      "The studio's research dish: awara methods grilled and dusted with yaji-style spice, beside the beef reference.",
    proteinBase: "Awara (soy curd)",
  },
  {
    name: "Vegan Shawarma",
    style: "Wrap, Lagos style",
    description:
      "Marinated soy strips with cabbage, carrot and sauce in a warm wrap — a familiar format with a plant protein core.",
    proteinBase: "Soy strips",
  },
  {
    name: "Soy Chunks (“Vchunks”-style)",
    style: "Retail protein base",
    description:
      "Shelf-stable textured soy chunks of the kind Nigerian vegan kitchens already buy, ready for stews and grills.",
    proteinBase: "Textured soy protein",
  },
];
