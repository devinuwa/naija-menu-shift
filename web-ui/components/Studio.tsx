"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  ALLERGEN_OPTIONS,
  ALL_EQUIPMENT,
  ALL_INVENTORY,
  DATASET_NOTE,
  EQUIPMENT_LABELS,
  INVENTORY_ITEMS,
  MEASUREMENTS_NEEDED,
  TRIAL_STEPS,
} from "@/lib/data";
import {
  DEFAULT_BRIEF,
  explore,
  type Brief,
  type Candidate,
  type ExploreResult,
} from "@/lib/engine";
import { buildWorksheet } from "@/lib/worksheet";

const naira0 = (n: number) => `₦${n.toLocaleString("en-NG", { maximumFractionDigits: 0 })}`;
const naira2 = (n: number) =>
  `₦${n.toLocaleString("en-NG", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const PORTION_CHOICES = [80, 100, 120, 140, 160, 180, 200];

const OBJECTIVES = [
  {
    key: "budget" as const,
    heading: "Budget-first",
    description: "Lowest modelled listed cost within your limits",
  },
  {
    key: "protein" as const,
    heading: "Protein-first",
    description: "Highest source-referenced estimated protein within limits",
  },
  {
    key: "kitchen" as const,
    heading: "Kitchen-first",
    description: "Shortest assumed preparation within your limits",
  },
];

function toggle(list: string[], value: string): string[] {
  return list.includes(value) ? list.filter((v) => v !== value) : [...list, value];
}

export default function Studio() {
  const [brief, setBrief] = useState<Brief>(DEFAULT_BRIEF);
  const [result, setResult] = useState<ExploreResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const requestSeq = useRef(0);

  useEffect(() => {
    const seq = ++requestSeq.current;
    setLoading(true);
    explore(brief)
      .then((res) => {
        if (seq !== requestSeq.current) return;
        setResult(res);
        setError(null);
        setLoading(false);
      })
      .catch((err: unknown) => {
        if (seq !== requestSeq.current) return;
        setError(err instanceof Error ? err.message : "Engine request failed");
        setLoading(false);
      });
  }, [brief]);

  const byId = useMemo(() => {
    const map = new Map<string, Candidate>();
    for (const c of result?.candidates ?? []) map.set(c.identifier, c);
    return map;
  }, [result]);

  useEffect(() => {
    if (!result) return;
    const fallback =
      result.best.balanced ?? result.eligibleIds[0] ?? result.candidates[0]?.identifier ?? null;
    if (!selectedId || !byId.has(selectedId)) setSelectedId(fallback);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [result]);

  const selected = selectedId ? byId.get(selectedId) ?? null : null;
  const eligibleCount = result?.eligibleIds.length ?? 0;
  const frontierCount = result?.frontierIds.length ?? 0;
  const referenceForPortion = selected
    ? result?.reference.find((r) => r.portionG === selected.portionG)
    : undefined;

  const currentStep = !result ? 2 : eligibleCount > 0 ? 4 : 3;

  const patch = (p: Partial<Brief>) => setBrief((b) => ({ ...b, ...p }));

  const downloadWorksheet = () => {
    if (!selected) return;
    const blob = new Blob([buildWorksheet(selected, brief)], {
      type: "text/markdown;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `menushift-trial-${selected.identifier.replace("@", "-")}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <>
      <ol className="ns-steps" aria-label="Progress">
        {["Choose dish", "Set constraints", "Compare formulations", "Inspect & trial"].map(
          (label, i) => {
            const n = i + 1;
            const state = n < currentStep ? "done" : n === currentStep ? "current" : "todo";
            return (
              <li key={label} className={`ns-step ns-step--${state}`} aria-current={state === "current" ? "step" : undefined}>
                <span className="ns-step-num">{n}</span> {label}
              </li>
            );
          },
        )}
      </ol>

      <div className="ns-layout">
        {/* ------------------------------------------------ constraints */}
        <section className="ns-panel" aria-labelledby="constraints-heading">
          <h2 id="constraints-heading" className="ns-panel-title">
            01 · Restaurant brief
          </h2>

          <label className="ns-field">
            <span className="ns-label">Current menu item</span>
            <select value="suya" disabled aria-describedby="dish-note">
              <option value="suya">Suya — awara (soy curd) formulations</option>
            </select>
          </label>
          <p className="ns-note" id="dish-note">
            Suya is the first sourced use case. Further dishes join only when a sourced
            dataset exists for them; the studio does not invent dishes or data.
          </p>

          <div className="ns-field">
            <label className="ns-label" htmlFor="budget">
              Budget for listed partial costs (₦)
            </label>
            <div className="ns-dual">
              <input
                id="budget"
                type="number"
                min={1}
                value={brief.budgetNgn}
                onChange={(e) => patch({ budgetNgn: Number(e.target.value) })}
              />
              <input
                type="range"
                min={100}
                max={3000}
                step={50}
                value={Math.min(3000, Math.max(100, brief.budgetNgn))}
                onChange={(e) => patch({ budgetNgn: Number(e.target.value) })}
                aria-label="Budget slider"
              />
            </div>
            <p className="ns-note">Listed ingredient + processing costs only — not a menu price.</p>
          </div>

          <div className="ns-field">
            <label className="ns-label" htmlFor="protein">
              Minimum estimated protein (g)
            </label>
            <div className="ns-dual">
              <input
                id="protein"
                type="number"
                min={0}
                max={60}
                value={brief.proteinTargetG}
                onChange={(e) => patch({ proteinTargetG: Number(e.target.value) })}
              />
              <input
                type="range"
                min={0}
                max={40}
                step={1}
                value={Math.min(40, brief.proteinTargetG)}
                onChange={(e) => patch({ proteinTargetG: Number(e.target.value) })}
                aria-label="Protein target slider"
              />
            </div>
          </div>

          <div className="ns-field">
            <label className="ns-label" htmlFor="prep">
              Maximum assumed preparation time (minutes)
            </label>
            <div className="ns-dual">
              <input
                id="prep"
                type="number"
                min={1}
                value={brief.maxPrepMinutes}
                onChange={(e) => patch({ maxPrepMinutes: Number(e.target.value) })}
              />
              <input
                type="range"
                min={15}
                max={240}
                step={5}
                value={Math.min(240, Math.max(15, brief.maxPrepMinutes))}
                onChange={(e) => patch({ maxPrepMinutes: Number(e.target.value) })}
                aria-label="Preparation time slider"
              />
            </div>
          </div>

          <label className="ns-field">
            <span className="ns-label">Desired characteristics</span>
            <input
              type="text"
              maxLength={200}
              value={brief.preference}
              onChange={(e) => patch({ preference: e.target.value })}
              placeholder="e.g. chewy grilled"
            />
            <span className="ns-note">
              Experimental text match only — it never overrides a hard constraint and is
              not evidence about taste.
            </span>
          </label>

          <fieldset className="ns-fieldset">
            <legend className="ns-label">Available equipment</legend>
            {ALL_EQUIPMENT.map((id) => (
              <label key={id} className="ns-check">
                <input
                  type="checkbox"
                  checked={brief.equipment.includes(id)}
                  onChange={() => patch({ equipment: toggle(brief.equipment, id) })}
                />
                <span>{EQUIPMENT_LABELS[id]}</span>
              </label>
            ))}
          </fieldset>

          <fieldset className="ns-fieldset">
            <legend className="ns-label">Ingredients in stock</legend>
            {ALL_INVENTORY.map((id) => (
              <label key={id} className="ns-check">
                <input
                  type="checkbox"
                  checked={(brief.availableIngredients ?? []).includes(id)}
                  onChange={() =>
                    patch({
                      availableIngredients: toggle(brief.availableIngredients ?? [], id),
                    })
                  }
                />
                <span>{INVENTORY_ITEMS[id]}</span>
              </label>
            ))}
          </fieldset>

          <fieldset className="ns-fieldset">
            <legend className="ns-label">Allergen exclusions (fail closed)</legend>
            {ALLERGEN_OPTIONS.map((a) => (
              <div key={a.id}>
                <label className="ns-check">
                  <input
                    type="checkbox"
                    checked={brief.avoidAllergens.includes(a.id)}
                    onChange={() =>
                      patch({ avoidAllergens: toggle(brief.avoidAllergens, a.id) })
                    }
                  />
                  <span>Avoid {a.label}</span>
                </label>
                <p className="ns-note ns-note--indent">{a.hint}</p>
              </div>
            ))}
          </fieldset>

          <details className="ns-advanced">
            <summary>Advanced assumptions</summary>
            <fieldset className="ns-fieldset">
              <legend className="ns-label">Modelled portion sizes (g)</legend>
              <div className="ns-checkrow">
                {PORTION_CHOICES.map((p) => (
                  <label key={p} className="ns-check ns-check--chip">
                    <input
                      type="checkbox"
                      checked={brief.portionsG.includes(p)}
                      onChange={() => {
                        const next = brief.portionsG.includes(p)
                          ? brief.portionsG.filter((x) => x !== p)
                          : [...brief.portionsG, p].sort((a, b) => a - b);
                        if (next.length > 0) patch({ portionsG: next });
                      }}
                    />
                    <span>{p}</span>
                  </label>
                ))}
              </div>
            </fieldset>

            <div className="ns-grid2">
              <label className="ns-field">
                <span className="ns-label">Wet-curd yield (kg per kg dry soy)</span>
                <input
                  type="number"
                  step={0.05}
                  min={0.1}
                  max={10}
                  value={brief.wetYieldKgPerKgDry}
                  onChange={(e) => patch({ wetYieldKgPerKgDry: Number(e.target.value) })}
                />
              </label>
              <label className="ns-field">
                <span className="ns-label">Oil for frying (cl)</span>
                <input
                  type="number"
                  step={0.5}
                  min={0}
                  value={brief.oilCl}
                  onChange={(e) => patch({ oilCl: Number(e.target.value) })}
                />
              </label>
              <label className="ns-field">
                <span className="ns-label">Onion (g)</span>
                <input
                  type="number"
                  min={0}
                  value={brief.onionG}
                  onChange={(e) => patch({ onionG: Number(e.target.value) })}
                />
              </label>
              <label className="ns-field">
                <span className="ns-label">Pepper (g)</span>
                <input
                  type="number"
                  min={0}
                  value={brief.pepperG}
                  onChange={(e) => patch({ pepperG: Number(e.target.value) })}
                />
              </label>
              <label className="ns-field">
                <span className="ns-label">Salt (g)</span>
                <input
                  type="number"
                  min={0}
                  value={brief.saltG}
                  onChange={(e) => patch({ saltG: Number(e.target.value) })}
                />
              </label>
              <label className="ns-field">
                <span className="ns-label">Seasoning (g) — label unreviewed</span>
                <input
                  type="number"
                  min={0}
                  value={brief.seasoningG}
                  onChange={(e) => patch({ seasoningG: Number(e.target.value) })}
                />
              </label>
            </div>

            <label className="ns-field">
              <span className="ns-label">Price scenario (not a forecast)</span>
              <select
                value={String(brief.priceShock)}
                onChange={(e) => patch({ priceShock: Number(e.target.value) })}
              >
                <option value="-0.2">−20% prices</option>
                <option value="0">Base prices</option>
                <option value="0.2">+20% prices</option>
              </select>
            </label>
          </details>
        </section>

        {/* ---------------------------------------------------- results */}
        <section className="ns-results" aria-labelledby="results-heading">
          <h2 id="results-heading" className="ns-panel-title">
            02 · Formulation exploration
          </h2>

          {error && (
            <div className="ns-alert ns-alert--error" role="alert">
              <strong>Brief rejected:</strong> {error}
            </div>
          )}

          {result && (
            <div className="ns-summary" aria-live="polite">
              <div className="ns-stat">
                <span className="ns-stat-num num">{result.inspected}</span>
                <span className="ns-stat-label">inspected</span>
              </div>
              <div className="ns-stat">
                <span className="ns-stat-num num">{result.candidates.length}</span>
                <span className="ns-stat-label">candidates</span>
              </div>
              <div className="ns-stat">
                <span className="ns-stat-num num">{eligibleCount}</span>
                <span className="ns-stat-label">eligible</span>
              </div>
              <div className="ns-stat">
                <span className="ns-stat-num num">{frontierCount}</span>
                <span className="ns-stat-label">on Pareto frontier</span>
              </div>
              <div className="ns-exclusions">
                {result.skippedEquipment > 0 && (
                  <span className="ns-chip ns-chip--warn">
                    {result.skippedEquipment} excluded — equipment not available
                  </span>
                )}
                {result.skippedIngredients > 0 && (
                  <span className="ns-chip ns-chip--warn">
                    {result.skippedIngredients} excluded — ingredient not in stock
                  </span>
                )}
                {result.skippedUnverifiedYaji > 0 && (
                  <span className="ns-chip ns-chip--warn">
                    {result.skippedUnverifiedYaji} excluded — no verified peanut-free yaji
                  </span>
                )}
                <span className="ns-chip">
                  Engine: {result.engineMode === "aws" ? "AWS (Python)" : "local demo"}
                </span>
              </div>
            </div>
          )}

          {loading && !result && <p className="ns-note">Calculating…</p>}

          {result && eligibleCount === 0 && !error && (
            <div className="ns-nofeasible" role="alert">
              <h3>No plant-based formulation meets all of your requirements.</h3>
              <p>
                <strong>
                  We don’t invent a recommendation when your constraints cannot be
                  satisfied.
                </strong>
              </p>
              {result.skippedUnverifiedYaji > 0 && (
                <p>
                  Peanut exclusion: standard suya yaji frequently contains groundnut, and
                  this dataset has no verified peanut-free yaji formulation — so the
                  studio abstains rather than guessing.
                </p>
              )}
              <p>
                Try increasing the budget or time, adjusting the protein target, or
                supplying the required equipment or stock. Dietary exclusions cannot be
                bypassed, and no score or model text can override them.
              </p>
            </div>
          )}

          {result && eligibleCount > 0 && (
            <>
              <div className="ns-cards">
                {OBJECTIVES.map((obj) => {
                  const id = result.best[obj.key];
                  const cand = id ? byId.get(id) : undefined;
                  if (!cand) return null;
                  const alsoFor = OBJECTIVES.filter(
                    (o) => o.key !== obj.key && result.best[o.key] === cand.identifier,
                  ).map((o) => o.heading.replace("-first", ""));
                  return (
                    <article key={obj.key} className="ns-card">
                      <p className="ns-card-kicker">{obj.heading}</p>
                      <h3 className="ns-card-name">{cand.method}</h3>
                      <p className="ns-card-metric num">{naira0(cand.costNgn)}</p>
                      <p className="ns-card-metric-label">Listed cost (incomplete)</p>
                      <p className="ns-card-facts">
                        <strong className="num">{cand.portionG} g</strong> modelled portion ·{" "}
                        <strong className="num">{cand.proteinG.toFixed(1)} g</strong>{" "}
                        estimated protein ·{" "}
                        <strong className="num">{cand.prepMinutes} min</strong> assumed prep
                      </p>
                      <p className="ns-note">{obj.description}</p>
                      {alsoFor.length > 0 && (
                        <p className="ns-chip">Also the pick for: {alsoFor.join(", ")}</p>
                      )}
                      <button
                        type="button"
                        className="ns-button"
                        onClick={() => setSelectedId(cand.identifier)}
                        aria-pressed={selectedId === cand.identifier}
                      >
                        {selectedId === cand.identifier ? "Inspecting below" : "Inspect"}
                      </button>
                    </article>
                  );
                })}
              </div>
              <p className="ns-note">
                Highest explainable score (balanced):{" "}
                <strong>{result.best.balanced ?? "—"}</strong>. Scores are secondary —
                cost, protein and practicality come first, and a score can never make an
                infeasible formulation eligible.
              </p>
            </>
          )}

          {selected && result && (
            <article className="ns-detail" aria-labelledby="detail-heading">
              <h3 id="detail-heading" className="ns-panel-title">
                03 · Inspect — {selected.method} · {selected.portionG} g
              </h3>

              <div className="ns-badges" aria-label="Evidence status">
                <span className="ns-badge">Synthetic demo data</span>
                <span className="ns-badge">Source reference</span>
                <span className="ns-badge">Modelled</span>
                {(!selected.allergenReviewComplete || selected.ingredientLines.some((l) => l.ingredientId === "seasoning")) && (
                  <span className="ns-badge ns-badge--warn">Unreviewed</span>
                )}
                {!selected.feasible && (
                  <span className="ns-badge ns-badge--warn">Not eligible under this brief</span>
                )}
              </div>

              <div className="ns-metrics">
                <div>
                  <span className="ns-metric-num num">{naira2(selected.costNgn)}</span>
                  <span className="ns-metric-label">
                    Listed cost (incomplete) — ingredients {naira2(selected.ingredientCostNgn)}{" "}
                    + processing {naira2(selected.processingCostNgn)}
                  </span>
                </div>
                <div>
                  <span className="ns-metric-num num">{selected.proteinG.toFixed(1)} g</span>
                  <span className="ns-metric-label">Estimated protein</span>
                </div>
                <div>
                  <span className="ns-metric-num num">{selected.prepMinutes} min</span>
                  <span className="ns-metric-label">Assumed preparation time</span>
                </div>
                <div>
                  <span className="ns-metric-num num">
                    {selected.ironMg.toFixed(2)} / {selected.zincMg.toFixed(2)} mg
                  </span>
                  <span className="ns-metric-label">Estimated iron / zinc</span>
                </div>
              </div>

              {referenceForPortion && (
                <p className="ns-reference">
                  <strong>Comparison reference only:</strong> beef suya at{" "}
                  {referenceForPortion.portionG} g — listed cost{" "}
                  <span className="num">{naira2(referenceForPortion.costNgn)}</span>,
                  estimated protein{" "}
                  <span className="num">{referenceForPortion.proteinG.toFixed(1)} g</span>.
                  The raw price and the cooked nutrient row are shown on the same gram
                  weight; they are not one measured piece. Beef is never a recommendation.
                </p>
              )}

              <h4>Why this formulation</h4>
              <ul className="ns-reasons">
                {selected.reasons.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
              <p className="ns-note">
                Requires: {selected.requiredEquipment.map((e) => EQUIPMENT_LABELS[e] ?? e).join(", ")}
                {" · "}Stock: {selected.requiredInventory.map((i) => INVENTORY_ITEMS[i] ?? i).join(", ")}
                {selected.allergens.length > 0 &&
                  ` · Labelled allergens: ${selected.allergens.join(", ")}`}
              </p>
              <p className="ns-note">
                The yaji spice blend is not part of the sourced dataset, so the allergen
                review of a full suya serving remains incomplete.
              </p>

              <h4>Estimated ingredient lines</h4>
              <div className="ns-tablewrap">
                <table className="ns-table">
                  <thead>
                    <tr>
                      <th scope="col">Ingredient</th>
                      <th scope="col">Purchase (g)</th>
                      <th scope="col">Est. cost</th>
                      <th scope="col">Est. protein (g)</th>
                      <th scope="col">Price source</th>
                      <th scope="col">Nutrition source [state]</th>
                      <th scope="col">Allergen labels</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selected.ingredientLines.map((l) => (
                      <tr key={l.ingredientId}>
                        <td>{l.name}</td>
                        <td className="num">{l.purchaseG}</td>
                        <td className="num">{naira2(l.estimatedCostNgn)}</td>
                        <td className="num">{l.estimatedProteinG}</td>
                        <td>{l.priceSource}</td>
                        <td>
                          {l.nutritionSource} [{l.nutritionState}]
                        </td>
                        <td>{l.allergenLabels}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {selected.scoreBreakdown.length > 0 && (
                <>
                  <h4>Score breakdown (explainable)</h4>
                  <div className="ns-scorebars">
                    {selected.scoreBreakdown.map((p) => (
                      <div key={p.key} className="ns-scorebar">
                        <span className="ns-scorebar-label">{p.label}</span>
                        <span className="ns-scorebar-track" aria-hidden="true">
                          <span
                            className="ns-scorebar-fill"
                            style={{ width: `${Math.min(100, p.value * 200)}%` }}
                          />
                        </span>
                        <span className="ns-scorebar-value num">{p.value.toFixed(3)}</span>
                      </div>
                    ))}
                    <p className="ns-note">
                      Total score: <strong className="num">{selected.score?.toFixed(3)}</strong>{" "}
                      — a ranking aid within the feasible set only.
                    </p>
                  </div>
                </>
              )}

              <details className="ns-advanced">
                <summary>Full source trace</summary>
                <ul className="ns-reasons">
                  {selected.sources.map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              </details>

              <h4>Kitchen trial worksheet</h4>
              <p className="ns-note">
                Research trial steps — not a retail recipe and not approved for food
                service. Warnings and sources above come before any action.
              </p>
              <ol className="ns-steps-list">
                {(TRIAL_STEPS[selected.methodId] ?? []).map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ol>
              <details className="ns-advanced">
                <summary>Measurements still needed before a real recipe</summary>
                <ul className="ns-reasons">
                  {MEASUREMENTS_NEEDED.map((m) => (
                    <li key={m}>{m}</li>
                  ))}
                </ul>
              </details>
              <button type="button" className="ns-button" onClick={downloadWorksheet}>
                Download trial worksheet (.md)
              </button>
            </article>
          )}

          <p className="ns-note ns-dataset-note">{DATASET_NOTE}</p>
        </section>
      </div>
    </>
  );
}
