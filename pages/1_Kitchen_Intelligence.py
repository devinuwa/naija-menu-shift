"""Premium restaurant-first, source-aware Kitchen Intelligence experience."""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st

from menushift.bedrock_image import (
    TITAN_IMAGE_MODEL_ID,
    TitanImageGenerator,
    workshop_generation_enabled,
)
from menushift.kitchen_optimizer import explore
from menushift.menu_pilots import DISH_LABELS, DISH_SCOPE
from menushift.visual_intent import BedrockVisualInterpreter, visual_interpretation_enabled
from menushift.visual_preview import METHODS, STYLES, build_preview_draft

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "sources"

st.set_page_config(
    page_title="Kitchen Intelligence | Naija MenuShift",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
:root{--forest:#173b2d;--forest-deep:#102c22;--cream:#fbfaf5;--gold:#bc8948;--line:#d8e2d9;}
[data-testid="stAppViewContainer"] {background:var(--cream);color:#183329;}
[data-testid="stHeader"]{background:rgba(251,250,245,.94);}
.block-container{max-width:1180px;padding-top:1rem;padding-bottom:4rem;}
.stMarkdown h1,.stMarkdown h2,.stMarkdown h3{color:var(--forest);letter-spacing:-.03em;}
[data-testid="stMetric"] {background:white;border:1px solid var(--line);border-radius:16px;padding:18px;}
[data-testid="stMetricLabel"] p{font-weight:650;}
[data-testid="stAlert"]{border-radius:14px;}
[data-testid="stForm"]{background:#fff;border:1px solid var(--line);border-radius:20px;padding:20px;}
div.stButton>button[kind="primary"],div.stFormSubmitButton>button[kind="primary"]{
  background:#1b5940;color:white;border:1px solid #1b5940;border-radius:11px;font-weight:650;
}
div.stButton>button[kind="primary"]:hover,div.stFormSubmitButton>button[kind="primary"]:hover{
  background:#143f2f;color:white;border-color:#143f2f;
}
button:focus-visible,input:focus-visible,[role="tab"]:focus-visible{
  outline:3px solid #c18a40!important;outline-offset:2px!important;
}
.ms-hero{
  background:radial-gradient(circle at 84% 20%,#34644a 0%,transparent 34%),
             linear-gradient(125deg,#102d23 0%,#24533d 100%);
  color:#fff;padding:40px 44px;border-radius:23px;margin:4px 0 22px;
  box-shadow:0 16px 30px rgba(16,45,35,.10);
}
.ms-eyebrow{font-size:.8rem;letter-spacing:.15em;text-transform:uppercase;color:#e2bd7b;font-weight:750}
.ms-hero h1{font-size:clamp(2rem,5vw,3.7rem);line-height:1.05;color:#fff!important;margin:14px 0;}
.ms-hero p{color:#e0eee5;max-width:750px;font-size:1.07rem;line-height:1.62;}
.ms-hero-tags{display:flex;gap:8px;flex-wrap:wrap;margin-top:18px}
.ms-hero-tags span{padding:6px 12px;border:1px solid #70947d;border-radius:999px;font-size:.82rem;color:#f0eadc}
.ms-steps{display:flex;gap:6px;flex-wrap:wrap;margin:12px 0 20px}
.ms-steps span{background:#e7ede6;padding:9px 13px;border-radius:9px;color:#274436;font-size:.88rem;font-weight:600}
.ms-section{font-size:.8rem;letter-spacing:.1em;font-weight:800;color:#517a60;text-transform:uppercase;margin:18px 0 8px}
.ms-warning{padding:12px 16px;background:#fff3da;border-left:4px solid #af7930;border-radius:8px;color:#684817;margin:14px 0}
.ms-card-intro{color:#557366;font-size:.86rem;font-weight:650;letter-spacing:.06em;text-transform:uppercase;}
.ms-card-name{font-size:1.25rem;font-weight:800;color:#183a2a;line-height:1.25;margin-top:6px;}
.ms-research{color:#50665a;font-size:.87rem}
@media(max-width:640px){
 .ms-hero{padding:24px 22px;border-radius:18px;}
 .ms-steps span{font-size:.78rem;padding:7px 9px;}
 .block-container{padding-left:1rem;padding-right:1rem}
 [data-testid="stForm"]{padding:12px}
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<section class="ms-hero" aria-label="Kitchen Intelligence Studio introduction">
  <div class="ms-eyebrow">Naija MenuShift · Hack the Fork Nigeria · Challenge 2</div>
  <h1>More menu choices.<br>Better kitchen decisions.</h1>
  <p>Diversify familiar Nigerian menus with additional plant-based choices,
  ingredient estimates, budget checks, equipment-aware planning and
  transparent evidence. Existing dishes remain on the menu.</p>
  <div class="ms-hero-tags"><span>Recipe exploration</span>
  <span>Cost & protein trade-offs</span><span>Clear reasoning</span></div>
</section>
<div class="ms-steps" aria-label="Four-step workflow">
<span>01 · Choose a dish</span><span>02 · Set the brief</span>
<span>03 · Explore options</span><span>04 · Understand why</span>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="ms-section">01 · Restaurant brief</div>', unsafe_allow_html=True)
st.subheader("Which menu would you like to diversify?")
dish_id = st.selectbox(
    "Existing menu dish", list(DISH_LABELS),
    format_func=lambda code: DISH_LABELS[code],
    help="Suya is the primary pilot; jollof is a protein-side exploration only.",
)
st.caption(DISH_SCOPE[dish_id])
if dish_id == "jollof_side":
    st.warning(
        "PARTIAL menu adaptation: these figures cover the proposed plant-protein accompaniment "
        "ONLY. Rice, sauce, chicken baseline, whole-meal cost and nutrition are not included."
    )

with st.container(border=True):
    st.markdown("### 02 · Your constraints")
    st.caption("Live simulation — results update when you change a requirement.")
    b, p, t = st.columns(3)
    budget = b.number_input(
        "Maximum estimated cost per serving (₦)",
        min_value=1.0, max_value=100000.0, value=750.0, step=50.0,
    )
    protein = p.number_input(
        "Minimum estimated protein (g)",
        min_value=0.0, max_value=150.0, value=12.0, step=1.0,
    )
    max_time = t.number_input(
        "Maximum preparation time (minutes)",
        min_value=1.0, max_value=1440.0, value=120.0, step=5.0,
    )
    preference = st.text_input(
        "What matters about the dish?",
        placeholder="For example: chewy and smoky, soft and mild, crisp exterior",
        max_chars=200,
        help="Experimental text similarity.",
    )
    labels = {
        "grill": "Grill / charcoal setup",
        "press": "Press or weights",
        "freezer": "Freezer",
        "frying_pan": "Frying pan & heat source",
    }
    equipment = st.multiselect(
        "What equipment is available?",
        list(labels),
        default=["grill", "press", "frying_pan"],
        format_func=lambda code: labels[code],
        help="Options needing absent equipment are not recommended.",
    )
    with st.expander("Advanced assumptions, allergens and scenarios"):
        size_min, size_max = st.select_slider(
            "Finished serving sizes (grams)",
            options=list(range(60, 221, 20)), value=(80, 200),
        )
        avoid = st.multiselect(
            "Exclude these declared allergens",
            ["soy", "peanut", "wheat", "sesame", "milk", "egg", "tree nut", "fish", "shellfish"],
            help="Unknown ingredient labels cause exclusion.",
        )
        oil_cl = st.number_input(
            "Oil for fried method (centilitres)",
            min_value=0.0, max_value=30.0, value=1.0, step=0.5,
        )
        shock = st.slider("Ingredient-price scenario (%)", -20, 20, 0, step=5)
        yield_ratio = st.slider(
            "Wet curd per kg dry soy (kg)",
            1.5, 2.0, 1.75, 0.05,
        )
        a, c, d, e = st.columns(4)
        firm_t = a.number_input("Firm minutes", min_value=1, max_value=600, value=35)
        pressed_t = c.number_input("Pressed minutes", min_value=1, max_value=600, value=48)
        frozen_t = d.number_input("Freeze/thaw minutes", min_value=1, max_value=1440, value=110)
        fried_t = e.number_input("Fried minutes", min_value=1, max_value=600, value=65)

# Streamlit controls are rerunnable; one bounded, deterministic analysis per brief.
try:
    search = explore(
        SOURCES,
        dish_id=dish_id,
        budget_ngn=budget,
        protein_target_g=protein,
        max_prep_minutes=max_time,
        equipment=frozenset(equipment),
        portions_g=tuple(range(int(size_min), int(size_max) + 1, 20)),
        preference=preference,
        avoid_allergens=tuple(avoid),
        wet_yield_kg_per_kg_dry=yield_ratio,
        oil_cl=oil_cl,
        price_shock=shock / 100,
        prep_minutes={"firm": firm_t, "pressed": pressed_t,
                      "frozen": frozen_t, "fried": fried_t},
    )
except (ValueError, OSError, RuntimeError) as exc:
    st.error(f"Cannot calculate this scenario: {exc}")
    st.stop()

st.markdown('<div class="ms-section">03 · Formulation exploration</div>', unsafe_allow_html=True)
st.subheader("Find a formulation that fits your kitchen")
if dish_id == "jollof_side":
    st.caption("Estimated plant-protein accompaniment ONLY — not a complete jollof meal.")
a, b, c = st.columns(3)
a.metric("Candidates evaluated", f"{search.inspected}")
b.metric("Within hard limits", f"{len(search.eligible)}")
c.metric("Pareto alternatives", f"{len(search.frontier)}")
if search.skipped_equipment:
    st.caption(f"{search.skipped_equipment} candidate configurations excluded for unavailable equipment.")

if not search.eligible:
    st.error("No plant-based formulation meets all of your requirements.")
    st.write(
        "Try increasing the budget or time, adjusting the protein target, or supplying "
        "the required equipment. Dietary exclusions cannot be bypassed."
    )
    st.info("We don't invent a recommendation when your constraints cannot be satisfied.")
else:
    cards = (
        ("Budget-first", "budget", "Lowest estimated serving cost within your limits"),
        ("Protein-first", "protein", "Highest estimated protein within your limits"),
        ("Kitchen-first", "kitchen", "Fastest assumed preparation within your limits"),
    )
    cols = st.columns(3)
    for col, (heading, objective, description) in zip(cols, cards):
        candidate = search.best(objective)
        if candidate is None:
            continue
        with col, st.container(border=True):
            st.markdown(f'<div class="ms-card-intro">{heading}</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="ms-card-name">{candidate.method}</div>',
                unsafe_allow_html=True,
            )
            st.caption(description)
            st.metric("Estimated cost", f"₦{candidate.evaluation.cost_ngn:,.0f}")
            st.write(
                f"**{candidate.portion_g:.0f} g** serving · "
                f"**{candidate.evaluation.protein_g:.1f} g** estimated protein"
            )

    st.markdown('<div class="ms-section">04 · Understand the recommendation</div>', unsafe_allow_html=True)
    st.subheader("Inspect a formulation")
    indexed = {c.identifier: c for c in search.eligible}
    chosen_id = st.selectbox(
        "Choose a feasible formulation to inspect",
        list(indexed),
        format_func=lambda k: (
            f"{indexed[k].method} · {indexed[k].portion_g:.0f} g · "
            f"₦{indexed[k].evaluation.cost_ngn:,.0f}"
        ),
        index=list(indexed).index(search.best("balanced").identifier),
    )
    selected = indexed[chosen_id]
    info, recipe = st.columns([1, 1], gap="large")
    with info:
        st.markdown("#### Why this candidate qualifies")
        st.write(
            f"Estimated ingredients: ₦{selected.evaluation.ingredient_cost_ngn:,.0f} · "
            f"Other listed preparation: ₦{selected.evaluation.processing_cost_ngn:,.0f}"
        )
        st.write(
            f"Estimated protein: {selected.evaluation.protein_g:.1f} g · "
            f"Preparation time: {selected.evaluation.prep_minutes:.0f} minutes"
        )
        st.write("Required equipment:", ", ".join(labels[x] for x in sorted(selected.required_equipment)))
        for reason in selected.evaluation.reasons:
            st.write("• " + reason)
    with recipe:
        st.markdown("#### Ingredient and quantity worksheet")
        st.dataframe(
            pd.DataFrame([
                {
                    "Ingredient": line.name,
                    "Purchased grams (estimated)": line.purchase_g,
                    "Declared label": line.allergen_labels or "Unreviewed",
                }
                for line in selected.ingredient_lines
            ]),
            hide_index=True, width="stretch",
        )
        if selected.evaluation.option_id not in METHODS:
            st.caption(
                "The AI dish visual preview covers the suya awara formulations; "
                "this partial accompaniment has no visual preview."
            )
        else:
            st.markdown("#### AI dish visual preview")
            st.caption("An optional concept illustration of the dish.")
            visual_style = st.selectbox(
                "How should we present the dish?",
                options=list(STYLES),
                index=1,
                key="preview_style",
            )
            visual_request = st.text_area(
                "Describe your preferred appearance or presentation",
                placeholder="e.g. a relaxed outdoor street-food setting at sunset, "
                            "overhead on a wooden serving board",
                max_chars=600,
                key="preview_request",
                help="The free-form AI can interpret presentation, light and camera direction. "
                     "Requests to change food must go through the recipe engine.",
            )
            intent_key = (selected.identifier, visual_style, visual_request)
            if visual_interpretation_enabled():
                if st.button("Interpret my description with AI", width="stretch"):
                    try:
                        interpreter = BedrockVisualInterpreter(
                            model_id=os.environ["BEDROCK_TEXT_MODEL_ID"]
                        )
                        intent = interpreter.interpret(visual_request)
                        st.session_state["visual_interpretation"] = {
                            "key": intent_key,
                            "intent": intent,
                        }
                    except Exception:  # noqa: BLE001 — external API failures cannot affect recipe
                        st.session_state.pop("visual_interpretation", None)
                        st.warning(
                            "AI interpretation was unavailable. The controlled local "
                            "presentation parser is still available."
                        )
            else:
                st.caption(
                    "Advanced Bedrock text interpretation becomes available when an "
                    "event-approved text model is configured. Basic safe cues work offline."
                )
            saved_intent = st.session_state.get("visual_interpretation")
            selected_intent = (
                saved_intent["intent"] if saved_intent and saved_intent["key"] == intent_key
                else None
            )
            recipe_change_requested = bool(
                selected_intent and selected_intent.requires_recipe_change
            )
            if recipe_change_requested:
                st.warning(
                    "Your visual request appears to change the recipe. Please select or "
                    "revalidate the ingredients in the recipe editor first. "
                    "No image will be generated from this request."
                )
            draft = build_preview_draft(
                selected, style=visual_style, restaurant_request=visual_request,
                visual_intent=None if recipe_change_requested else selected_intent,
            )
            st.caption(
                "Interpreted visual direction: "
                + (", ".join(draft.interpreted_preferences) or "default presentation only")
            )
            if selected_intent is not None and not recipe_change_requested:
                st.caption("Interpreted by the Bedrock text model, locally validated.")
            else:
                st.caption("Interpreted by the local parser.")
            with st.expander("Inspect or download the recipe-grounded image prompt"):
                st.code(draft.prompt, language=None)
                st.caption("Excluded elements: " + draft.negative_prompt)
                st.download_button(
                    "Download image prompt",
                    data=draft.prompt + "\n",
                    file_name="naija-menushift-visual-prompt.txt",
                    mime="text/plain",
                    width="stretch",
                )
            image_allowed = workshop_generation_enabled()
            if st.button(
                "Generate one AI dish concept image",
                type="secondary",
                disabled=recipe_change_requested,
                width="stretch",
                help="One explicit request only, requiring an authorised image model.",
            ):
                if not image_allowed:
                    st.warning(
                        "Image generation cannot run yet: the organisers' AWS account "
                        "does not list an authorised image model. The prompt is ready "
                        "and the recipe remains available."
                    )
                else:
                    try:
                        generator = TitanImageGenerator(
                            model_id=TITAN_IMAGE_MODEL_ID, approved=True
                        )
                        generated = generator.generate(draft)
                        st.session_state["preview_result"] = {
                            "key": draft.fingerprint,
                            "bytes": generated.content,
                            "mime": generated.mime_type,
                        }
                    except Exception:  # noqa: BLE001 — external provider failures are isolated
                        st.error(
                            "Image generation failed or access was denied. "
                            "The recipe and prompt remain available."
                        )
            if not image_allowed:
                st.info(
                    "Image creation is not enabled for this event account. "
                    "The organiser's model allowlist does not include Titan Image Generator. "
                    "No paid image-generation calls will be attempted."
                )
            preview_result = st.session_state.get("preview_result")
            if (
                image_allowed and not recipe_change_requested and preview_result
                and preview_result["key"] == draft.fingerprint
            ):
                st.image(
                    preview_result["bytes"], caption=draft.label,
                    use_container_width=True,
                )
                st.download_button(
                    "Download illustrative image",
                    data=preview_result["bytes"],
                    file_name="naija-menushift-concept.png",
                    mime=preview_result["mime"],
                )
    st.subheader("Trade-offs across eligible formulations")
    chart = pd.DataFrame([
        {
            "Recipe": f"{c.method} · {c.portion_g:.0f}g",
            "Cost (₦)": c.evaluation.cost_ngn,
            "Estimated protein (g)": c.evaluation.protein_g,
            "Time (min)": c.evaluation.prep_minutes,
        }
        for c in search.eligible
    ])
    st.scatter_chart(chart, x="Cost (₦)", y="Estimated protein (g)")
    with st.expander("Inspect Pareto-efficient options and method benchmark"):
        st.caption(
            "Pareto-efficient means no other eligible candidate has lower/equal "
            "cost and time plus greater/equal protein, with at least one improvement."
        )
        st.dataframe(
            pd.DataFrame([
                {
                    "Alternative": c.method,
                    "Portion (g)": c.portion_g,
                    "Estimated cost (₦)": c.evaluation.cost_ngn,
                    "Estimated protein (g)": c.evaluation.protein_g,
                    "Prep (min)": c.evaluation.prep_minutes,
                }
                for c in search.frontier
            ]),
            hide_index=True, width="stretch",
        )
        cheap = search.best("budget")
        balanced = search.best("balanced")
        st.write("Cheapest feasible baseline:", cheap.identifier)
        st.write("Balanced ranking:", balanced.identifier)

with st.expander("Vchunks competitor"):
    st.write(
        "VeggieVictory lists 150 g packaged Vchunks at ₦4,500 and a prepared "
        "Vchunks suya menu item at ₦2,000."
    )
    st.link_button("Vchunks product listing", "https://veggievictory.com/product/vchunks-plant-based-meat/")
    st.link_button("Prepared Vchunks suya", "https://veggievictory.com/product/vchunks-suya/")

st.caption(
    "Naija MenuShift · Kitchen Intelligence Studio · Hack the Fork Nigeria."
)
