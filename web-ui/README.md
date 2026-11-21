# Naija MenuShift — Web UI (Kitchen Intelligence Studio)

A Vercel-ready Next.js (App Router) + TypeScript implementation of the Naija
MenuShift Kitchen Intelligence Studio, built to the team's design handoff
(`KITCHEN_UI_DESIGN_HANDOFF_2026-11-19.md`): forest `#173B2D`, dark green
`#102C22`, rich green `#1B5940`, warm cream `#FBFAF5`, gold `#BC8948`, light
border `#D8E2D9`, max width 1180px, tabular numerals for naira.

**Research prototype.** Demo data is synthetic (it mirrors the team's research
workbook values so the interface behaves like the Python prototype). Nothing in
this UI labels a result "safe", "delicious", "measured" or "retail-priced", and
beef appears only as a comparison reference — never as a recommendation.

## What it does

A restaurant owner finds a viable *research formulation* for kitchen testing in
under four steps:

1. **Choose dish** — Suya (awara / soy-curd formulations) is the first sourced
   use case.
2. **Set constraints** — budget for listed partial costs, minimum estimated
   protein, maximum assumed prep time, desired characteristics, equipment,
   stock, allergen exclusions, plus advanced assumptions (portions, yield, oil,
   spice grams, ±20% price scenario).
3. **Compare formulations** — summary counts (inspected / candidates / eligible
   / Pareto frontier / exclusion reasons) and three decision cards:
   Budget-first, Protein-first, Kitchen-first. When one formulation wins
   several objectives, the card says so — no artificial diversity.
4. **Inspect & trial** — ingredient lines with grams, estimated costs and
   proteins, price and nutrition sources, score breakdown, evidence badges
   ("source reference", "modelled", "unreviewed"), trial steps, and a
   downloadable kitchen trial worksheet (Markdown).

If nothing satisfies every hard constraint, the studio shows a clear
no-feasible state — *"We don't invent a recommendation when your constraints
cannot be satisfied"* — instead of relaxing the rules.

### Constraint semantics (identical to the Python engine)

The local engine (`lib/engine.ts`) is a TypeScript mirror of
`src/menushift/engine.py` + `src/menushift/kitchen_optimizer.py`:

- Hard constraints first: plant-only, budget, protein, time, equipment subset,
  inventory subset, allergen exclusions that **fail closed** (an exclusion
  that cannot be verified excludes the option).
- **Peanut exclusion abstains entirely**: standard suya yaji frequently
  contains groundnut and the dataset has no verified peanut-free yaji, so no
  recommendation is made.
- Score exists only for feasible options: cost 0.45 + protein utility 0.25 +
  time 0.15 + TF-IDF text match 0.15 (experimental; not taste evidence).
- Four awara methods (firm / pressed / frozen–thawed / fried) × modelled
  portions, with press-loss purchase maths and the fried method's oil cost
  kept separate from ingredient cost.

## Architecture — one seam for the AWS switch

```
Browser ──► lib/engine.ts  explore(brief)  (async — the ONLY UI entry point)
              │  POST /api/explore
              ▼
        app/api/explore/route.ts
              ├─ MENUSHIFT_ENGINE_URL unset → local TypeScript engine (demo mode)
              └─ MENUSHIFT_ENGINE_URL set   → proxy to the AWS-hosted Python engine
```

The UI never calls the engine directly; it only knows the JSON contract of
`POST /api/explore` (brief in, exploration result out). Tomorrow's AWS move is
configuration, not a rewrite.

### Switching to AWS (tomorrow)

1. Host the Python engine so it exposes `POST /explore` accepting the same
   brief JSON and returning the same result JSON (API Gateway + Lambda, ECS,
   or App Runner all work).
2. Set one environment variable wherever this UI runs:

   ```
   MENUSHIFT_ENGINE_URL=https://<your-api-id>.execute-api.us-east-1.amazonaws.com/prod
   ```

3. Redeploy/restart. The summary strip's engine chip switches from
   "local demo" to "AWS (Python)" based on the response. No UI code changes.

## Run locally

```bash
npm install
npm run dev        # http://localhost:3000
# or production:
npm run build
npm start
```

## Deploy to Vercel

**Dashboard path**

1. Push this folder to a Git repository (or use `vercel` CLI from this folder).
2. Vercel → Add New → Project → import the repo.
3. **Root Directory:** `web-ui` (if the repo root is the deliverables folder)
   or `.` if this folder is the repo root. Framework preset: **Next.js**
   (auto-detected). Build command `npm run build`, output default.
4. Environment Variables: add `MENUSHIFT_ENGINE_URL` only when the AWS engine
   is live; leave it unset for the offline demo.
5. Deploy.

**CLI path**

```bash
npm i -g vercel
cd web-ui
vercel          # preview deployment
vercel --prod   # production deployment
# optional, once AWS is live:
vercel env add MENUSHIFT_ENGINE_URL production
```

## API contract (POST /api/explore)

Request body — a brief (all fields optional; defaults mirror the Python
`explore()` defaults):

```json
{
  "budgetNgn": 1500,
  "proteinTargetG": 15,
  "maxPrepMinutes": 120,
  "equipment": ["grill", "press", "freezer", "frying_pan"],
  "availableIngredients": ["awara", "onion", "pepper", "salt", "seasoning", "oil"],
  "portionsG": [80, 100, 120, 140, 160, 180, 200],
  "preference": "chewy grilled",
  "avoidAllergens": [],
  "wetYieldKgPerKgDry": 1.75,
  "oilCl": 1.0,
  "priceShock": 0,
  "onionG": 0, "pepperG": 0, "saltG": 0, "seasoningG": 0
}
```

Response: `{ inspected, skippedEquipment, skippedIngredients,
skippedUnverifiedYaji, candidates[], eligibleIds[], frontierIds[],
best{budget, protein, kitchen, balanced}, reference[], engineMode }`.
Invalid briefs return HTTP 400 with the Python engine's validation message.

## Layout of this folder

```
app/
  page.tsx                 header, hero + research warning, studio, explorer
  layout.tsx, globals.css  design tokens + responsive rules (single column ≤1023px, stacked cards ≤760px)
  api/explore/route.ts     local engine tonight / AWS proxy via env var
components/
  Studio.tsx               steps, constraint panel, summary, decision cards, detail, no-feasible state
  MenuExplorer.tsx         illustrative Veggie Victory–inspired menu vision (not engine outputs)
lib/
  engine.ts                TS mirror of the Python constraint engine + async explore()
  data.ts                  synthetic demo dataset, methods, trial steps, menu items
  worksheet.ts             downloadable kitchen trial worksheet (Markdown)
.env.example               MENUSHIFT_ENGINE_URL documentation
```

## Verification performed (2026-11-20)

- `npm install` and `npm run build` succeed (Next.js 15.5, types + lint clean).
- Production server: `GET /` → 200 with the studio rendered.
- `POST /api/explore` feasible brief (3 portions): inspected 12, eligible 12,
  frontier 9; firm awara @100 g = ₦45.37 listed cost / 17.3 g estimated protein;
  fried @100 g = ₦45.37 ingredients + ₦43.51 oil processing; beef reference
  @100 g = ₦717.14 / 29.5 g — all matching hand calculations from the Python
  formulas.
- Peanut avoidance → 0 candidates, `skippedUnverifiedYaji = 12`, all bests
  null (abstention). Soy avoidance → 0 eligible with the labelled-allergen
  reason. ₦40 budget → 0 eligible. Grill-only equipment → only firm awara,
  9 equipment exclusions. Invalid portion / equipment / price-shock → HTTP 400
  with the Python validation messages.

## Parallel Vercel prototype and restrictions (20 November 2026)

This is a suya-focused **separate synthetic demonstration**, not the full Python
Streamlit research application. The original Streamlit app remains authoritative
for multi-dish research, the Evidence Library and Python safety checks.

The Vercel server accepts only JSON briefs with known keys and <=12 KB bodies;
unknown allergen exclusions fail rather than being ignored. Soy, groundnut and
wheat aliases are canonicalised. Compound seasoning with unreviewed animal origin
cannot qualify for a plant-only recommendation. A hard filter always comes before
ranking. This is not food-safety certification or a live market quote.

No AWS Bedrock integration or paid model calls are enabled. Next.js is pinned to
15.5.29, the November 2026 patched maintenance release. Vercel Hobby is for
eligible personal non-commercial demonstration use, not commercial service.
