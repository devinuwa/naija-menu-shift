import type { FunctionalProfile, Level } from "@/lib/hospital-types";

const LEVEL_VALUE: Record<Level, number> = { Low: 1, Moderate: 2, High: 3 };

const ROWS: { key: keyof FunctionalProfile; label: string }[] = [
  { key: "solubility", label: "Solubility" },
  { key: "waterHolding", label: "Water-holding" },
  { key: "emulsification", label: "Emulsification" },
  { key: "gelation", label: "Gelation" },
];

export default function FunctionalBars({ functional }: { functional: FunctionalProfile }) {
  return (
    <div className="hs-fbars" aria-label="Functional properties">
      {ROWS.map(({ key, label }) => {
        const level = functional[key];
        const value = LEVEL_VALUE[level];
        return (
          <div className="hs-fbar" key={key}>
            <span className="hs-fbar-label">{label}</span>
            <span className="hs-fbar-track" aria-hidden="true">
              {[1, 2, 3].map((seg) => (
                <span
                  key={seg}
                  className={seg <= value ? "hs-fbar-seg hs-fbar-seg--on" : "hs-fbar-seg"}
                />
              ))}
            </span>
            <span className="hs-fbar-level">{level}</span>
          </div>
        );
      })}
    </div>
  );
}
