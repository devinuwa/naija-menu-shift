import type { Alternative } from "@/lib/hospital-types";
import { PROTEIN_IMAGES } from "@/lib/protein-images";
import FunctionalBars from "./FunctionalBars";

export const fmtNgn = (n: number) =>
  "₦" + n.toLocaleString("en-NG", { minimumFractionDigits: n % 1 !== 0 ? 2 : 0, maximumFractionDigits: 2 });
export const fmtG = (n: number) => (Math.round(n * 10) / 10).toLocaleString("en-NG");

export default function AlternativeCard({
  alt,
  rank,
  featured = false,
  reasoning,
}: {
  alt: Alternative;
  rank?: number;
  featured?: boolean;
  reasoning?: string;
}) {
  const img = PROTEIN_IMAGES[alt.proteinId];
  return (
    <article className={featured ? "hs-altcard hs-altcard--featured" : "hs-altcard"}>
      {img ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img className="hs-altcard-img" src={img} alt={`${alt.name} — generated illustration`} />
      ) : null}
      <div className="hs-altcard-body">
        {rank ? <p className="hs-altcard-rank">Option {rank}</p> : null}
        <h4 className="hs-altcard-name">{alt.name}</h4>
        <p className="hs-altcard-portion">{alt.portionG} g portion</p>
        <div className="hs-altcard-metrics">
          <span>
            <strong>{fmtG(alt.proteinG)} g</strong> protein
          </span>
          <span>
            <strong>{fmtNgn(alt.costNgn)}</strong> per serving
          </span>
          <span>
            <strong>{alt.prepMinutes} min</strong> prep
          </span>
        </div>
        {alt.allergens.length > 0 ? (
          <p className="hs-chips">
            {alt.allergens.map((a) => (
              <span className="hs-chip hs-chip--allergen" key={a.label}>
                Allergen: {a.label}
              </span>
            ))}
          </p>
        ) : null}
        <FunctionalBars functional={alt.functional} />
        <p className="hs-altcard-meaning">{alt.kitchenMeaning}</p>
        {reasoning ? <p className="hs-altcard-reasoning">{reasoning}</p> : null}
      </div>
    </article>
  );
}
