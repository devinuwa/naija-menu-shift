# Kitchen Intelligence Studio — Product, design & engineering specification
**19 November 2026 — Hack the Fork Nigeria 2026 · Challenge 2**

## Product promise
Help Nigerian restaurants explore credible plant-based adaptations of existing menu items under **cost, protein, preparation, available equipment and dietary** constraints. The UI is designed around a single story: **choose dish → describe the kitchen → explore alternatives → inspect the evidence**.

This project is a *research prototype*, **not** a kitchen-certified recipe system, sensory prediction model or a source of guaranteed cost savings. Keep all existing independent Challenge 3 code in its own repository.

## UX north star
- Users: independent restaurant owners and caterers; technical researchers/judges can inspect secondary information.
- Hero: warm culinary identity, concise positioning, no long technical introduction.
- Core controls: dish, budget, protein, time, preparation preference and available equipment.
- Secondary controls: portion variation, wet-curd yield, ingredient price shock, assumptions and allergen exclusions. Every advanced choice stays labelled and editable.
- Results: three first-glance outcomes — **Budget-first**, **Protein-first**, **Kitchen-first** — followed by one detailed formulation and a trade-off scatter view.
- Explainability: what passed, what was excluded, the recipe's purchased-ingredient weights, requirements, price source traces and a blunt limitations summary.
- Failure UX: when no formulation is feasible, abstain with corrective actions; never silently use beef or unknown allergen data.
- Contrast and accessibility: semantic headings and labels, visible focus, readable text on warm backgrounds, no information conveyed only by colour. Mobile uses stacked native Streamlit columns. Manual browser audits still required.

## Visual system (prototype design)
- Forest `#173B2D` / deep `#102C22`, near-white cream `#FBFAF5`, amber accent `#BC8948`, muted mint-border `#D8E2D9`.
- System font, generous spacing, 16–23px rounded corners and limited shadows.
- Native Streamlit forms, accessible controls and tabs; no fragile third-party widgets, huge images or frontend rewrite.
- Treat source-quality badges and research warnings as functional, not decorative elements.

## Implementation
- `src/menushift/kitchen_optimizer.py`: deterministic, bounded **constrained recipe exploration**. Enumerates base methods and varied finished-serving sizes, enforces hard price/protein/time/allergen checks through the original `engine.evaluate`, excludes methods requiring unavailable kitchen equipment and computes a Pareto frontier.
- `pages/1_Kitchen_Intelligence.py`: polished, responsive restaurant-first workspace with three decision perspectives, itemised recipe estimates, price sources and model limitations.
- All ingredient identities come from the existing sourced-menu domain. No generative model invents nutrient values, ingredient prices, allergen labels, yields or preparation times.
- Fixed material: the PDF's original source-price rows and method references; variable experimental settings: finished grams, wet-curd yield, equipment, prep minutes and oil.
- **Important:** `sourced_menu.build_sourced_menu` is source-backed but relies on unmeasured yields, modelled portions and zero/unknown energy and labour costs. `data/verified/` is not promoted or modified. Never label calculated results independently validated.
- Current formulation search varies **portion size and the four preparation methods**. It does not yet generate unconstrained new ingredients or claim sensory optimisation.

## What the 54-minute AWS video adds
Reviewed sampled video frames and the companion webinar notes, not a complete machine transcript.
- ~02–04 min: event environment introduction, temporary workshop setup.
- ~12–14 min: sign-in methods and account event page.
- ~24–27 min: presentation explicitly contrasts a raw Bedrock answer with open data and a **checked** answer; human verification is emphasised.
- ~30–38 min: practical Workshop Studio/Kiro remote access and organisation sign-in.
- ~40–54 min: Kiro AI-assisted Python/Bedrock coding demonstration and finishing recommendations.
The key product lesson is **ground the model and check every result**. The temporary AWS/Kiro account is not a persistent backend.

## Substantive AI contribution — release gate
The new deterministic optimiser is useful but **not a learned taste or culinary model**. It does not by itself establish AI novelty. The next gate is a safe, optional Bedrock component in the organiser's sandbox:
1. Only send synthetic, anonymised or open/public non-sensitive content to Bedrock.
2. Accept only structured **candidate IDs, permitted ingredient IDs and bounded quantity suggestions** from an allowed model.
3. Validate every suggestion with local constraints and source references; refuse arbitrary food additions or guessed nutrition/prices.
4. Compare model-assisted candidate discovery with the no-model optimisation baseline on *fixed chef-authored scenarios*, including false suggestions and refusals.
5. Preserve offline deterministic functionality and a prerecorded demo. Do not expose AWS keys, tokens or team access codes; use only time-limited credentials inside event permissions.
6. An optional explanation model should report sourced numbers and assumptions, not generate culinary claims.
7. Stop using the workshop endpoint after its 72-hour lifetime; keep code and outputs outside the sandbox.

## Required non-AI proof
- For each tofu method, actually measure starting and finished masses, oil absorption, energy, prep time, and at least two skewer/texture observations under comparable cooking conditions.
- Record local food pricing date, region, exact package size and source.
- Recheck purchased food state vs nutrition reference; pressing does not create protein.
- Document direct retailer/chef feedback and what the tool changed relative to a simple cost-only baseline.

## Targeted QA
Automated: invalid numeric inputs; available equipment, soy/unknown allergen abstention, impossible budget, beef exclusion, cost shock, bounded portion search, Pareto dominance and Streamlit AppTest.

Manual **before release**:
- [ ] Public app loads on narrow mobile (320px and 390px) without horizontal clipping.
- [ ] 200% zoom with readable cards, labels and warnings.
- [ ] Complete form keyboard-only; visible focus and logical tab order.
- [ ] Screen-reader label on budget, protein, equipment and allergen fields.
- [ ] No hidden data/status behind colour; all source links accessible.
- [ ] Different equipment choices visibly change recommendations.
- [ ] No-feasible state and soy restriction show honest abstention.
- [ ] See core recommendation with minimal scrolling on desktop; inspect practical prep in secondary section.
- [ ] Review all generated examples with Amina and chef mentor before claims.
- [ ] Record demo and save GitHub commits before AWS account expiration.

## Recommended 90-second demonstration
1. Show restaurant owner selects suya, budget and equipment.
2. Show three decision perspectives and a frontier of feasible formulations.
3. Remove the press or fryer: method exclusions update and stay explainable.
4. Add soy exclusion or impossible budget: software **refuses to recommend**.
5. Open recipe card, ingredient sources, and measured/unmeasured warning.
6. Compare baseline to any validated model-assisted candidate in a separately labelled experiment; do not invent gains.

## Merge/deployment boundary
This branch is review-only. Do not merge or deploy until Muhammad confirms interface/scoring, Amina confirms source claims, meaningful automated checks pass, and the team approves publication. Streamlit app `main` is unchanged.
