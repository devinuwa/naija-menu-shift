"""Read-only source exploration for menu-diversification research."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from menushift.evidence_catalog import load_nutrition_references, load_wfp_price_snapshots

st.set_page_config(page_title="Evidence Library | Naija MenuShift", page_icon="📚", layout="wide")
st.caption("NAIJA MENUSHIFT · DIVERSIFY NIGERIAN MENUS")
st.title("Evidence Library")
st.write(
    "Trace food-composition references and historical Nigerian market prices while "
    "exploring additional plant-based menu choices."
)
st.warning(
    "NOT live supplier quotations or validated recipes. These records are kept separate "
    "from the recommendation engine until a specific food, state, serving and kitchen "
    "process are independently reviewed."
)

try:
    nutrition = load_nutrition_references()
    prices = load_wfp_price_snapshots()
except (OSError, ValueError) as exc:
    st.error(f"Evidence catalog failed validation: {exc}")
    st.stop()

n_tab, p_tab, info_tab = st.tabs(
    ["Nutrition references", "Historical prices", "Source quality & next steps"]
)
with n_tab:
    st.subheader("Food composition per 100 g edible portion")
    st.caption(
        "FAO/INFOODS WAFCT 2019 and USDA SR Legacy. Published reference profiles "
        "are NOT measured nutrient profiles of local awara, branded Vchunks or a finished dish."
    )
    source = st.selectbox(
        "Source", ["All", "FAO/INFOODS WAFCT 2019", "USDA FoodData Central SR Legacy"],
    )
    query = st.text_input("Find a food", placeholder="rice, cowpea, tofu, chicken…")
    selected = [
        r for r in nutrition
        if (source == "All" or r["source"] == source)
        and query.strip().casefold() in r["food_name"].casefold()
    ]
    st.caption(f"{len(selected)} reference records; 0 approved finished recipes.")
    if selected:
        df = pd.DataFrame(selected).rename(columns={
            "reference_id": "ID", "food_name": "Food", "food_state": "State",
            "protein_g_per_100g": "Protein (g/100g)",
            "iron_mg_per_100g": "Iron (mg/100g)",
            "zinc_mg_per_100g": "Zinc (mg/100g)",
            "energy_kcal_per_100g": "Energy (kcal/100g)",
            "source_url": "Publisher URL",
        })
        st.dataframe(
            df[["ID", "Food", "State", "Protein (g/100g)", "Iron (mg/100g)",
                "Zinc (mg/100g)", "Energy (kcal/100g)", "Publisher URL"]],
            hide_index=True, use_container_width=True,
        )
    else:
        st.info("No exact match. Similar food names are not evidence of equivalent composition.")
    st.link_button("FAO/INFOODS database", "https://www.fao.org/infoods/infoods/tables-and-databases/faoinfoods-databases/en")
    st.link_button("USDA FoodData Central", "https://fdc.nal.usda.gov/")

with p_tab:
    st.subheader("WFP Nigeria — historical retail market aggregates")
    st.caption("October–November 2026 · Borno and Yobe only · not national averages.")
    a, b, c = st.columns(3)
    month = a.selectbox("Survey month", sorted({r["month"] for r in prices}, reverse=True))
    state = b.selectbox("Survey state", sorted({r["state"] for r in prices}))
    commodity = c.selectbox("Commodity", ["All", *sorted({r["commodity"] for r in prices})])
    selected = [
        r for r in prices if r["month"] == month and r["state"] == state
        and (commodity == "All" or r["commodity"] == commodity)
    ]
    if selected:
        df = pd.DataFrame(selected).rename(columns={
            "commodity": "Commodity", "original_unit": "Reported unit",
            "median_ngn_per_reported_unit": "Median ₦ per reported unit",
            "median_ngn_per_kg": "Median ₦/kg (mass only)",
            "market_count": "Survey markets", "last_observation": "Survey date",
        })
        st.dataframe(
            df[["Commodity", "Reported unit", "Median ₦ per reported unit",
                "Median ₦/kg (mass only)", "Survey markets", "Survey date"]],
            hide_index=True, use_container_width=True,
        )
    st.caption(
        "Values are medians across WFP market entries marked 'aggregate'. "
        "Oil priced per litre intentionally has no calculated ₦/kg. "
        "These are not current prices for Abuja, Zaria or a specific supplier."
    )
    st.link_button(
        "WFP Nigeria original price dataset",
        "https://data.humdata.org/dataset/wfp-food-prices-for-nigeria",
    )

with info_tab:
    st.subheader("What was carefully imported")
    st.write(
        "15 selected FAO/USDA nutrition references and 28 WFP market aggregates. "
        "The original datasets are retained in Muhammad's source ZIP, not copied wholesale into GitHub."
    )
    st.subheader("Held back from numeric recommendations")
    st.write(
        "NBS: existing May 2026 historical benchmarks retained separately. "
        "HESTIA: environmental impact boundaries not yet reviewed. "
        "Open Food Facts: incomplete branded labels and ODbL reuse considerations. "
        "No additional recipe or ingredient is automatically approved by this catalog."
    )
    st.subheader("Before a new recipe can be recommended")
    st.write(
        "Identify the exact ingredient and food state; collect local dated quotations; "
        "measure cooking yield and cost; confirm allergen labels and kitchen practicality; "
        "obtain food-specialist review. A restaurant may then add the new option to its menu."
    )
