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
        <img className="hs-altcard-img" src={img} alt={`${alt.name} — picture of the plant protein`} />
      ) : null}
      <div className="hs-altcard-body">
        {rank ? <p className="hs-altcard-rank">Choice {rank}</p> : null}
        <h4 className="hs-altcard-name">{alt.name}</h4>
        <p className="hs-altcard-portion">{alt.portionG} g portion</p>
        <dl className="hs-altcard-metrics">
          <div>
            <dt>Protein</dt>
            <dd>{fmtG(alt.proteinG)} g</dd>
          </div>
          <div>
            <dt>Cost</dt>
            <dd>{fmtNgn(alt.costNgn)}</dd>
          </div>
          <div>
            <dt>Cooking time</dt>
            <dd>{alt.prepMinutes} min</dd>
          </div>
        </dl>
        {alt.allergens.length > 0 ? (
          <p className="hs-chips">
            {alt.allergens.map((a) => (
              <span className="hs-chip hs-chip--allergen" key={a.label}>
                Allergy: {a.label}
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
