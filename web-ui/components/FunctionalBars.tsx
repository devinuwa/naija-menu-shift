import type { FunctionalProfile, Level } from "@/lib/hospital-types";

const LEVEL_VALUE: Record<Level, number> = { Low: 1, Moderate: 2, High: 3 };

const ROWS: { key: keyof FunctionalProfile; label: string }[] = [
  { key: "waterHolding", label: "Soaks up water" },
  { key: "gelation", label: "Sets and holds together" },
  { key: "emulsification", label: "Mixes into sauces" },
  { key: "solubility", label: "Dissolves in liquid" },
];

export default function FunctionalBars({ functional }: { functional: FunctionalProfile }) {
  return (
    <div className="hs-fbars-wrap">
      <p className="hs-fbars-title">How it behaves in cooking</p>
      <div className="hs-fbars" aria-label="How it behaves in cooking">
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
    </div>
  );
}
