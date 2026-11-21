// Types for the baked hospital data (lib/hospital-data.ts), generated from
// the MenuShift hospital engine's real outputs.

export type Level = "Low" | "Moderate" | "High";

export interface FunctionalProfile {
  solubility: Level;
  waterHolding: Level;
  emulsification: Level;
  gelation: Level;
}

export interface AllergenTag {
  label: string;
  keys: string[];
}

export interface Alternative {
  proteinId: string;
  name: string;
  portionG: number;
  proteinG: number;
  costNgn: number;
  prepMinutes: number;
  allergens: AllergenTag[];
  functional: FunctionalProfile;
  kitchenMeaning: string;
  reason: string;
}

export interface HospitalDish {
  id: string;
  name: string;
  status: "documented_animal" | "already_plant_based" | "unspecified" | "none_documented";
  alreadyPlantBased: boolean;
  blurb: string;
}

export interface MenuView {
  kept: string[];
  diversified: { dishId: string; alternative: Alternative }[];
  confirm: string[];
  staysAsServed: string[];
  totals: { proteinG: number | null; costNgn: number | null; count: number };
}

export interface DishReference {
  name: string;
  portionG: number;
  proteinG: number;
  costNgn: number;
  prepMinutes: number;
}

export interface PoolProtein {
  id: string;
  name: string;
  proteinPer100g: number;
  pricePerKg: number;
  prepMinutes: number;
  allergens: AllergenTag[];
  functional: FunctionalProfile;
  kitchenMeaning: string;
}

export interface Baseline {
  label: string;
  proteinPer100g: number | null;
  costPer100g: number | null;
  prepMinutes: number | null;
}

export interface HospitalData {
  dishes: HospitalDish[];
  views: Record<string, MenuView>;
  explorer: Record<string, { alternatives: Alternative[]; reference?: DishReference }>;
  pool: PoolProtein[];
  survival: Record<string, Record<string, { survives: boolean; reasons: string[] }>>;
  baselines: Record<string, Baseline>;
  methods: { id: string; label: string }[];
  proteinFloorG: number;
  portionsG: number[];
}
