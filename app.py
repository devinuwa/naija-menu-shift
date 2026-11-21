"""Naija MenuShift decision workspace. Sourced prices, interactive comparison."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from menushift.engine import compare_rankers, evaluate, sensitivity
from menushift.menu_pilots import DISH_LABELS, DISH_SCOPE, build_menu_pilots
from menushift.official_prices import preparation_methods, working_market_table
from menushift.quality import audit_dataset

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "data" / "sources"
ALLERGEN_CHOICES = ["soy", "peanut", "wheat", "milk", "egg", "sesame", "tree nut", "fish", "shellfish"]
DEFAULTS = {
    "budget": 500.0,
    "protein": 10.0,
    "prep": 180.0,
    "preference": "",
    "avoid": [],
    "finished": 100.0,
    "yield_ratio": 1.75,
    "firm_prep": 60.0,
    "pressed_prep": 60.0,
    "frozen_prep": 60.0,
    "fried_prep": 60.0,
    "oil_cl": 0.0,
    "onion_g": 0.0,
    "pepper_g": 0.0,
    "salt_g": 0.0,
    "seasoning_g": 0.0,
    "shock_pct": 0,
}

st.set_page_config(
    page_title="Naija MenuShift · Research Studio",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(
    """
<style>
:root { --ink: #153428; }
.block-container { max-width: 1100px; padding-top: 1.2rem; padding-bottom: 3rem; }
[data-testid="stAppViewContainer"] { background: #f6f8f6; }
h1,h2,h3 { letter-spacing: -.035em; color: var(--ink); }
h1 { font-size: clamp(1.8rem, 4vw, 3rem) !important; }
[data-testid="stMetric"] { background: #ffffff; border: 1px solid #d5e3da; border-radius: 17px; padding: 14px 18px; }
[data-testid="stMetricLabel"] { font-weight: 600; }
[data-testid="stAlert"] { border-radius: 14px; }
</style>
""",
    unsafe_allow_html=True,
)

for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)


def _apply(updates: dict) -> None:
    for key, value in updates.items():
        st.session_state[key] = value


st.caption("HACK THE FORK NIGERIA 2026 · CHALLENGE 2")
st.title("Naija MenuShift")
st.page_link("pages/1_Kitchen_Intelligence.py", label="Explore the Kitchen Intelligence Studio", icon="🌿")
st.page_link("pages/2_Evidence_Library.py", label="Inspect the Evidence Library", icon="📚")
st.caption("Expand menus with additional plant-based choices, without removing existing favourites.")
st.write("Diversify familiar Nigerian menus with additional plant-based options, transparent estimates and clear preparation constraints.")
st.warning(
    "Prices and per-100 g nutrients come from those sources. Finished weight, soy yield, "
    "prep minutes, oil, and spices are controls, because the workbook has no measured serving.",
    icon="⚠️",
)

st.subheader("1. Choose a menu to diversify")
dish_id = st.selectbox(
    "Current restaurant menu item", list(DISH_LABELS),
    format_func=lambda item: DISH_LABELS[item],
)
st.caption(DISH_SCOPE[dish_id])
if dish_id == "jollof_side":
    st.warning(
        "PARTIAL transformation: figures cover only the proposed plant-protein accompaniment. "
        "Rice, sauce, original chicken, and whole-meal totals are NOT included."
    )

st.subheader("2. Set your requirements")
with st.expander("Try a sourced scenario"):
    left, middle, right = st.columns(3)
    if left.button("100 g sheet basis", width="stretch"):
        _apply({"budget": 500.0, "protein": 10.0, "prep": 180.0, "finished": 100.0, "yield_ratio": 1.75, "oil_cl": 0.0, "avoid": []})
        st.rerun()
    if middle.button("At least 20 g protein", width="stretch"):
        _apply({"budget": 500.0, "protein": 20.0, "finished": 100.0})
        st.rerun()
    if right.button("Budget below every option", width="stretch"):
        _apply({"budget": 20.0, "protein": 10.0, "finished": 100.0})
        st.rerun()

budget_col, protein_col = st.columns(2)
budget = budget_col.number_input("Maximum cost per serving (₦)", min_value=1.0, max_value=100000.0, step=10.0, key="budget")
target = protein_col.number_input("Minimum estimated protein (g per serving)", min_value=0.0, max_value=150.0, step=1.0, key="protein")
preference = st.text_input(
    "Desired preparation characteristics (optional)",
    key="preference",
    max_chars=200,
    placeholder="e.g. pressed, fried, frozen",
    help="Word match against the method names. Not a taste test.",
)
with st.expander("Portion, yield, time, allergens, and price change"):
    portion_col, yield_col = st.columns(2)
    finished = portion_col.number_input("Finished awara (g)", min_value=50.0, max_value=400.0, step=10.0, key="finished")
    wet_yield = yield_col.slider(
        "Wet curd from 1 kg dry soy (kg)",
        min_value=1.5,
        max_value=2.0,
        step=0.05,
        key="yield_ratio",
        help="The workbook note says about 1.5 to 2 kg. It is not a measured batch.",
    )
    prep = st.number_input("Maximum preparation time (minutes)", min_value=1.0, max_value=1440.0, step=5.0, key="prep")
    time_cols = st.columns(4)
    firm_prep = time_cols[0].number_input("Firm minutes", min_value=1.0, max_value=1440.0, key="firm_prep")
    pressed_prep = time_cols[1].number_input("Pressed minutes", min_value=1.0, max_value=1440.0, key="pressed_prep")
    frozen_prep = time_cols[2].number_input("Frozen minutes", min_value=1.0, max_value=1440.0, key="frozen_prep")
    fried_prep = time_cols[3].number_input("Fried minutes", min_value=1.0, max_value=1440.0, key="fried_prep")
    st.caption("The workbook does not record minutes. Change them to see the time rule at work. The starting value is 60 for every method.")
    oil_col, onion_col = st.columns(2)
    oil_cl = oil_col.number_input("Oil for fried awara (cl)", min_value=0.0, max_value=30.0, step=0.5, key="oil_cl")
    onion_g = onion_col.number_input("Onion (g)", min_value=0.0, max_value=80.0, step=1.0, key="onion_g")
    pepper_col, salt_col, cube_col = st.columns(3)
    pepper_g = pepper_col.number_input("Pepper (g)", min_value=0.0, max_value=40.0, step=1.0, key="pepper_g")
    salt_g = salt_col.number_input("Salt (g)", min_value=0.0, max_value=20.0, step=1.0, key="salt_g")
    seasoning_g = cube_col.number_input("Seasoning cubes (g)", min_value=0.0, max_value=20.0, step=1.0, key="seasoning_g")
    avoid = st.multiselect(
        "Exclude these allergens",
        ALLERGEN_CHOICES,
        key="avoid",
        help="Soy is declared for awara. Spice rows are unreviewed, so any exclusion removes a spiced serving.",
    )
    shock = st.slider("Ingredient price change (%)", -20, 20, step=5, key="shock_pct") / 100

try:
    data = build_menu_pilots(
        SOURCES,
        finished_g=finished,
        wet_yield_kg_per_kg_dry=wet_yield,
        prep_minutes={"firm": firm_prep, "pressed": pressed_prep, "frozen": frozen_prep, "fried": fried_prep},
        oil_cl=oil_cl,
        onion_g=onion_g,
        pepper_g=pepper_g,
        salt_g=salt_g,
        seasoning_g=seasoning_g,
    )
    outputs = evaluate(
        data, dish_id, budget_ngn=budget, protein_target_g=target, price_shock=shock,
        max_prep_minutes=prep, preference=preference, avoid_allergens=avoid,
    )
    comparison = compare_rankers(
        data, dish_id, budget_ngn=budget, protein_target_g=target, price_shock=shock,
        max_prep_minutes=prep, preference=preference, avoid_allergens=avoid,
    )
except (ValueError, RuntimeError) as exc:
    st.error(f"Unable to calculate a comparison: {exc}")
    st.stop()

feasible = [row for row in outputs if row.feasible]
plants = [row for row in outputs if row.plant_only]
references = [row for row in outputs if not row.plant_only]
names = {row.option_id: row.name for row in outputs}


def _label(option_id: str | None) -> str:
    if not option_id:
        return "none (no eligible option)"
    return names.get(option_id, option_id)


summary, evidence, stress, methodology = st.tabs(
    ["3. Recommendations", "Evidence & sources", "Price scenarios", "How the score works"]
)

with summary:
    if oil_cl <= 0:
        st.info("Fried awara stays out until you enter an oil amount in centilitres. The workbook prices oil by the 75 cl bottle, not by a serving.")
    if feasible:
        choice = feasible[0]
        st.info(
            "Provisional calculation meets the entered numeric and ingredient constraints. "
            "This is NOT a safe-to-serve recipe, nutrient certification or current supplier quote."
        )
        st.subheader(choice.name)
        cost_col, protein_metric, time_col = st.columns(3)
        cost_col.metric("Total cost for this portion", f"₦{choice.cost_ngn:,.0f}")
        protein_metric.metric("Estimated protein", f"{choice.protein_g:.1f} g")
        time_col.metric("Preparation time", f"{choice.prep_minutes:.0f} min")
        st.caption("Protein for firm, pressed, and frozen pieces is the firm-tofu reference on the wet curd that went in. Pressing concentrates that curd. It does not create protein.")
        if not choice.allergen_review_complete:
            st.warning("Ingredient labels are incomplete. This is NOT cleared for an allergy restriction or food service.")
        with st.expander("Evidence & safety limitations", expanded=True):
            for warning in choice.evidence_warnings:
                st.warning(warning)
        with st.expander("Why this option came first", expanded=True):
            for reason in choice.reasons:
                st.write("- " + reason)
            st.write("Ingredients:", f"₦{choice.ingredient_cost_ngn:,.0f}")
            st.write("Oil and other preparation:", f"₦{choice.processing_cost_ngn:,.0f}")
            if choice.score_breakdown:
                st.json(dict(choice.score_breakdown), expanded=False)
    else:
        st.error("No plant-protein option meets all of these requirements.")
        st.write("Review the budget, protein target, available time and ingredient labels. Never bypass a dietary restriction.")
        for row in plants:
            with st.expander("Why " + row.name + " was excluded"):
                for reason in row.reasons:
                    st.write("- " + reason)

    chart = pd.DataFrame(
        {"Cost (naira)": [row.cost_ngn for row in plants], "Protein (g)": [row.protein_g for row in plants]},
        index=[row.name for row in plants],
    )
    st.bar_chart(chart)
    st.dataframe(
        pd.DataFrame([
            {"Alternative": row.name, "Cost (₦)": row.cost_ngn, "Est. protein (g)": row.protein_g, "Minutes": row.prep_minutes, "Status": "Provisional" if row.feasible else "Excluded"}
            for row in plants
        ]),
        width="stretch",
        hide_index=True,
    )
    if references:
        beef = references[0]
        with st.expander("Beef comparison (reference only)"):
            st.write(beef.name)
            left, right = st.columns(2)
            left.metric("Raw price on this gram weight", f"₦{beef.cost_ngn:,.0f}")
            right.metric("Cooked reference protein on this gram weight", f"{beef.protein_g:.1f} g")
            st.caption("The price figure is for raw boneless beef. The protein figure is cooked lean beef. They are not one weighed serving, and beef is never a plant recommendation.")
    with st.expander("Compare the recommendation methods"):
        st.write("Cheapest feasible:", _label(comparison["cheapest_feasible_plant"]))
        st.write("Keyword preference:", _label(comparison["keyword_hybrid"]))
        st.write("TF-IDF preference:", _label(comparison["tfidf_hybrid"]))
        if comparison["methods_disagree"]:
            st.warning("The text methods disagree. There is no single winner.")
        if comparison["abstained"]:
            st.info("Every method abstains because no awara option meets the requirements.")

with evidence:
    st.subheader("Ingredient evidence status")
    st.warning(
        "Published ingredient data is not a verified finished-meal recipe. "
        "Kitchen trials and current local supplier quotes remain outstanding."
    )
    st.caption("No independently reviewed kitchen trials recorded; intake template: data/evaluation/kitchen_trials.csv.")
    st.subheader("Vchunks: sourced competitor, not yet rankable")
    st.write(
        "VeggieVictory lists a 150 g packaged Vchunks product at ₦4,500 and "
        "a prepared Vchunks suya item at ₦2,000 (checked 20 Nov 2026). "
        "The suya listing describes wheat-based protein; complete current product "
        "nutrition, final serving size and kitchen processing costs were not verified."
    )
    st.link_button("See Vchunks product", "https://veggievictory.com/product/vchunks-plant-based-meat/")
    st.link_button("See Vchunks suya menu item", "https://veggievictory.com/product/vchunks-suya/")
    st.caption(
        "The packaged product and prepared menu item are not equivalent price units. "
        "Vchunks is excluded from numeric ranking until a product-level label and recipe are verified."
    )
    st.subheader("Prices used")
    st.dataframe(pd.DataFrame(working_market_table(SOURCES)), width="stretch", hide_index=True)
    st.subheader("Nutrition rows")
    st.dataframe(pd.DataFrame(preparation_methods(SOURCES)), width="stretch", hide_index=True)
    st.subheader("Dataset audit")
    st.dataframe(pd.DataFrame(issue.to_dict() for issue in audit_dataset(data)), width="stretch", hide_index=True)
    st.caption("A stale-price warning means the NBS month is older than 30 days. It does not turn the figure back into a placeholder.")

with stress:
    st.subheader("Ingredient price scenarios: minus 20%, base, plus 20%")
    scenarios = sensitivity(
        data, dish_id, budget_ngn=budget, protein_target_g=target, max_prep_minutes=prep,
        preference=preference, avoid_allergens=avoid,
    )
    records = [
        {"Scenario": label, "Option": row.name, "Cost (naira)": row.cost_ngn, "Status": "Provisional" if row.feasible else "Excluded"}
        for label, collection in scenarios.items()
        for row in collection
        if row.plant_only
    ]
    st.dataframe(pd.DataFrame(records), width="stretch", hide_index=True)
    st.caption("The shock moves naira-per-kilogram ingredients together. Oil entered in centilitres stays at the bottle price.")

with methodology:
    st.write("Hard filters run first: plant-only, budget, estimated protein, preparation time, and declared allergens.")
    st.write("Eligible options then get a provisional score: 45% cost margin, 25% protein utility, 15% time, and 15% text match.")
    st.write("Firm, pressed, and frozen protein uses the firm-tofu reference on the wet curd required after the sheet's water-loss percentage.")
    st.write("Fried awara uses a generic fried-tofu nutrient row and entered oil; cooking yield is unmeasured.")
    if dish_id == "suya":
        st.write("Beef is a reference using differently prepared food states, not a plant option.")
    else:
        st.write("Jollof rice and original chicken remain outside this protein-side estimate.")
    st.caption("This is not a food-safety, nutrition, purchasing, or dietary advice service.")
