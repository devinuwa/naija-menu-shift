"use client";

import { useRef, useState } from "react";
import { HOSPITAL_DATA } from "@/lib/hospital-data";
import { suggestAnyDish, type AnyDishResult } from "@/lib/hospital-engine";
import { PROTEIN_IMAGES } from "@/lib/protein-images";
import type { HospitalDish, MenuView } from "@/lib/hospital-types";
import AlternativeCard, { fmtG, fmtNgn } from "./AlternativeCard";

const CONDITIONS = [
  { id: "cardiovascular", label: "For heart patients" },
  { id: "kidney", label: "For kidney patients" },
  { id: "diabetes", label: "For diabetes patients" },
  { id: "hypertension", label: "For high blood pressure" },
];

const dishById = new Map<string, HospitalDish>(HOSPITAL_DATA.dishes.map((d) => [d.id, d]));

function DishMini({ dish, chip, chipClass }: { dish: HospitalDish; chip: string; chipClass?: string }) {
  return (
    <article className="hs-dishcard">
      <div className="hs-dishcard-top">
        <h4>{dish.name}</h4>
        <span className={chipClass ? `hs-chip ${chipClass}` : "hs-chip"}>{chip}</span>
      </div>
      <p>{dish.blurb}</p>
    </article>
  );
}

function TotalsStrip({ view }: { view: MenuView }) {
  if (view.totals.count === 0 || view.totals.proteinG == null || view.totals.costNgn == null) {
    return null;
  }
  return (
    <div className="hs-totals" role="status">
      <span className="hs-stat">
        <strong>{view.totals.count}</strong> dishes changed to plant protein
      </span>
      <span className="hs-stat">
        <strong>{fmtG(view.totals.proteinG)} g</strong> protein in those servings
      </span>
      <span className="hs-stat">
        <strong>{fmtNgn(view.totals.costNgn)}</strong> cost of the protein
      </span>
    </div>
  );
}

function BoardGroups({
  view,
  onExplore,
}: {
  view: MenuView;
  onExplore?: (dishId: string) => void;
}) {
  return (
    <>
      <h3 className="hs-group-title">Changed to plant protein</h3>
      <div className="hs-board-grid">
        {view.diversified.map(({ dishId, alternative }) => {
          const dish = dishById.get(dishId);
          const img = PROTEIN_IMAGES[alternative.proteinId];
          return (
            <article className="hs-dishcard hs-dishcard--diversified" key={dishId}>
              <div className="hs-dishcard-top">
                <h4>{dish?.name}</h4>
                <span className="hs-chip hs-chip--new">Plant protein</span>
              </div>
              <div className="hs-winner">
                {img ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={img} alt={`${alternative.name} — picture of the plant protein`} />
                ) : null}
                <div>
                  <p className="hs-winner-name">{alternative.name}</p>
                  <p className="hs-winner-facts">
                    {alternative.portionG} g portion · Protein {fmtG(alternative.proteinG)} g ·
                    Cost {fmtNgn(alternative.costNgn)} · Cooking time {alternative.prepMinutes} min
                  </p>
                </div>
              </div>
              {onExplore ? (
                <button className="hs-textbtn" onClick={() => onExplore(dishId)}>
                  See every choice for this dish →
                </button>
              ) : null}
            </article>
          );
        })}
      </div>

      <h3 className="hs-group-title">On the menu as served</h3>
      <div className="hs-board-grid">
        {view.kept.map((id) => {
          const dish = dishById.get(id);
          return dish ? (
            <DishMini key={id} dish={dish} chip="Already plant-based" chipClass="hs-chip--plant" />
          ) : null;
        })}
        {view.staysAsServed.map((id) => {
          const dish = dishById.get(id);
          return dish ? <DishMini key={id} dish={dish} chip="Served as it is today" /> : null;
        })}
      </div>

      <h3 className="hs-group-title">To confirm with the kitchen</h3>
      <div className="hs-board-grid">
        {view.confirm.map((id) => {
          const dish = dishById.get(id);
          return dish ? (
            <DishMini key={id} dish={dish} chip="Recipe to confirm" chipClass="hs-chip--confirm" />
          ) : null;
        })}
      </div>
    </>
  );
}

export default function HospitalStudio() {
  const [condition, setCondition] = useState("cardiovascular");
  const [explorerDish, setExplorerDish] = useState("meat");
  const explorerRef = useRef<HTMLDivElement>(null);

  const generalView = HOSPITAL_DATA.views["general"];
  const conditionView = HOSPITAL_DATA.views[condition];

  const openInExplorer = (dishId: string) => {
    setExplorerDish(dishId);
    explorerRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  // Any-dish form state
  const [dishName, setDishName] = useState("");
  const [currentProtein, setCurrentProtein] = useState("beef");
  const [method, setMethod] = useState("grill");
  const [avoidSoy, setAvoidSoy] = useState(false);
  const [avoidGluten, setAvoidGluten] = useState(false);
  const [anyResults, setAnyResults] = useState<AnyDishResult[] | null>(null);
  const [anyDishLabel, setAnyDishLabel] = useState("");

  const runAnyDish = (e: React.FormEvent) => {
    e.preventDefault();
    const avoidKeys = [
      ...(avoidSoy ? ["soy"] : []),
      ...(avoidGluten ? ["gluten", "wheat"] : []),
    ];
    setAnyResults(suggestAnyDish({ currentProtein, method, avoidKeys }));
    setAnyDishLabel(dishName.trim());
  };

  // Feedback form state
  const [fbState, setFbState] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const sendFeedback = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const data = new FormData(form);
    setFbState("sending");
    try {
      const res = await fetch("https://formsubmit.co/ajax/inuwamuhammad930@gmail.com", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          _subject: "Hospital Menu Studio — kitchen feedback",
          name: data.get("name"),
          kitchen: data.get("kitchen"),
          dish: data.get("dish"),
          landing: data.get("landing"),
          comment: data.get("comment"),
        }),
      });
      const body = await res.json().catch(() => null);
      if (res.ok && body && String(body.success) === "true") {
        setFbState("sent");
        form.reset();
      } else {
        setFbState("error");
      }
    } catch {
      setFbState("error");
    }
  };

  const explorer = HOSPITAL_DATA.explorer[explorerDish];
  const explorerDishObj = dishById.get(explorerDish);

  return (
    <>
      {/* ---------- 1 · Plant-protein swaps ---------- */}
      <section className="hs-section" aria-labelledby="hs-swaps-title">
        <h2 id="hs-swaps-title" className="hs-display hs-section-title">
          Plant-protein swaps
        </h2>
        <p className="hs-section-lede">
          This is one hospital kitchen&rsquo;s real ward menu. The dishes that are
          already plant-based stay just as they are. For the dishes built on meat
          or fish, the tool finds the plant protein that can take their place —
          and keeps the protein up.
        </p>

        <TotalsStrip view={generalView} />
        <BoardGroups view={generalView} onExplore={openInExplorer} />

        <div ref={explorerRef} className="hs-subblock">
          <h3 className="hs-display hs-subblock-title">Look at one dish closely</h3>
          <p className="hs-section-lede">
            Choose a dish to see the plant proteins that can take its place, best
            first — with a picture, the protein, the cost and the cooking time
            for each one.
          </p>

          <label className="hs-field">
            <span>Dish</span>
            <select value={explorerDish} onChange={(e) => setExplorerDish(e.target.value)}>
              {HOSPITAL_DATA.dishes.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                  {HOSPITAL_DATA.explorer[d.id] ? " — see plant choices" : ""}
                </option>
              ))}
            </select>
          </label>

          {explorer ? (
            <>
              {explorer.reference ? (
                <p className="hs-reference">
                  The dish as served today: {explorer.reference.portionG} g · Protein{" "}
                  {fmtG(explorer.reference.proteinG)} g · Cost {fmtNgn(explorer.reference.costNgn)}{" "}
                  · Cooking time {explorer.reference.prepMinutes} min. Every choice
                  below is measured against it.
                </p>
              ) : null}
              <div className="hs-altgrid">
                {explorer.alternatives.map((alt, i) => (
                  <AlternativeCard
                    key={`${alt.proteinId}-${alt.portionG}`}
                    alt={alt}
                    rank={i + 1}
                    featured={i === 0}
                  />
                ))}
              </div>
            </>
          ) : explorerDishObj?.alreadyPlantBased ? (
            <div className="hs-panel-note">
              <h3>{explorerDishObj.name} is already plant-based</h3>
              <p>
                {explorerDishObj.blurb} It stays on the menu just as it is — the
                kitchen already serves it, so there is nothing to change.
              </p>
            </div>
          ) : (
            <div className="hs-panel-note">
              <h3>The kitchen confirms the recipe first</h3>
              <p>
                {explorerDishObj?.blurb} Once the kitchen confirms what goes into
                this dish, the tool can look for the plant protein to take its
                place.
              </p>
            </div>
          )}
        </div>

        <div className="hs-subblock">
          <h3 className="hs-display hs-subblock-title">A dish from your own kitchen</h3>
          <p className="hs-section-lede">
            Serving a dish that is not on this board? Type its name, tell us the
            meat it uses today and how you cook it. The tool checks every plant
            protein against your allergy choices, the way the dish is cooked,
            and how much protein it gives — then shows the best three.
          </p>

          <form className="hs-form" onSubmit={runAnyDish}>
            <label className="hs-field">
              <span>Dish name</span>
              <input
                type="text"
                required
                maxLength={120}
                placeholder="e.g. Grilled chicken skewers"
                value={dishName}
                onChange={(e) => setDishName(e.target.value)}
              />
            </label>
            <div className="hs-form-row">
              <label className="hs-field">
                <span>Meat it uses today</span>
                <select value={currentProtein} onChange={(e) => setCurrentProtein(e.target.value)}>
                  {Object.entries(HOSPITAL_DATA.baselines).map(([id, b]) => (
                    <option key={id} value={id}>
                      {b.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="hs-field">
                <span>How you cook it</span>
                <select value={method} onChange={(e) => setMethod(e.target.value)}>
                  {HOSPITAL_DATA.methods.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <fieldset className="hs-fieldset">
              <legend>Keep these out (allergies)</legend>
              <label className="hs-check">
                <input type="checkbox" checked={avoidSoy} onChange={(e) => setAvoidSoy(e.target.checked)} />
                Soy
              </label>
              <label className="hs-check">
                <input type="checkbox" checked={avoidGluten} onChange={(e) => setAvoidGluten(e.target.checked)} />
                Gluten / wheat
              </label>
            </fieldset>
            <button className="hs-button" type="submit">
              Show the best choices
            </button>
          </form>

          {anyResults !== null ? (
            anyResults.length > 0 ? (
              <>
                <h3 className="hs-group-title">
                  Best choices{anyDishLabel ? ` for ${anyDishLabel}` : ""}
                </h3>
                <div className="hs-altgrid">
                  {anyResults.map((r, i) => (
                    <AlternativeCard
                      key={r.alternative.proteinId}
                      alt={r.alternative}
                      rank={i + 1}
                      featured={i === 0}
                      reasoning={r.reasoning}
                    />
                  ))}
                </div>
              </>
            ) : (
              <div className="hs-panel-note">
                <h3>No plant protein fits this dish</h3>
                <p>
                  For this dish and cooking style, no plant protein passes all
                  the checks together. Try a different way of cooking it, or
                  untick one of the allergy boxes above.
                </p>
              </div>
            )
          ) : null}
        </div>
      </section>

      {/* ---------- 2 · Condition-aware meals ---------- */}
      <section className="hs-section" aria-labelledby="hs-condition-title">
        <h2 id="hs-condition-title" className="hs-display hs-section-title">
          Condition-aware meals
        </h2>
        <p className="hs-section-lede">
          The same meals, adjusted for the patients who will eat them. Pick a
          patient group and the board changes — the plant-protein choices are
          picked again under that group&rsquo;s needs.
        </p>

        <div className="hs-conditions" role="tablist" aria-label="Patient group">
          {CONDITIONS.map((c) => (
            <button
              key={c.id}
              role="tab"
              aria-selected={condition === c.id}
              className={condition === c.id ? "hs-cond hs-cond--active" : "hs-cond"}
              onClick={() => setCondition(c.id)}
            >
              {c.label}
            </button>
          ))}
        </div>

        <TotalsStrip view={conditionView} />
        <BoardGroups view={conditionView} />
      </section>

      {/* ---------- Feedback ---------- */}
      <section className="hs-section" aria-labelledby="hs-feedback-title">
        <h2 id="hs-feedback-title" className="hs-display hs-section-title">
          Tell us how it went
        </h2>
        <p className="hs-section-lede">
          Have you served one of these meals in your hospital? Tell the team how
          it went — could you find the ingredients, was it easy to cook, and did
          the patients eat it?
        </p>
        {fbState === "sent" ? (
          <div className="hs-panel-note">
            <h3>Thank you — your feedback has been sent</h3>
            <p>The team reads every note and uses it to make the next menu better.</p>
          </div>
        ) : (
          <form className="hs-form" onSubmit={sendFeedback}>
            <div className="hs-form-row">
              <label className="hs-field">
                <span>Your name</span>
                <input type="text" name="name" required maxLength={120} autoComplete="name" />
              </label>
              <label className="hs-field">
                <span>Hospital or kitchen</span>
                <input type="text" name="kitchen" required maxLength={160} />
              </label>
            </div>
            <div className="hs-form-row">
              <label className="hs-field">
                <span>Dish you tried</span>
                <input type="text" name="dish" required maxLength={160} placeholder="e.g. Fish — the awara choice" />
              </label>
              <label className="hs-field">
                <span>How did it go?</span>
                <select name="landing" defaultValue="Went down well">
                  <option>Went down well</option>
                  <option>Mixed</option>
                  <option>Did not go down well</option>
                </select>
              </label>
            </div>
            <label className="hs-field">
              <span>Anything else the team should know?</span>
              <textarea name="comment" rows={4} maxLength={2000} />
            </label>
            {fbState === "error" ? (
              <p className="hs-form-error" role="alert">
                Sending did not finish — please check your connection and try again.
              </p>
            ) : null}
            <button className="hs-button" type="submit" disabled={fbState === "sending"}>
              {fbState === "sending" ? "Sending…" : "Send feedback"}
            </button>
          </form>
        )}
      </section>
    </>
  );
}
