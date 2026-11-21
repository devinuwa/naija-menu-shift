"""Hospital food-service mode: diversify a documented hospital menu.

The menu shown is the therapeutic diet kitchen menu at UNTH Enugu, published
in Maduforo et al., Pakistan Journal of Nutrition 15(2), 2016 - the only
peer-reviewed extraction of a real Nigerian hospital kitchen menu the team
could find. This page is decision support for dietetics and catering teams:
it proposes additional plant-protein options for the two dishes whose animal
protein the source documents (fish and meat). Nothing here is a served menu,
and a dietitian must approve any change before service.

An "Any dish" mode sits beside the documented menu: staff type any dish
they serve, name the animal protein and portion in it today and the cooking
method, and the same gates rank plant alternatives for it. Original-side
baselines are shown only where the project data carries a cited value.

A patient-condition selector sits above the dish flows: choosing a
condition (cardiovascular, hypertension, kidney, diabetes) applies that
condition's documented preset bundle to both flows and composes a draft
condition menu from the whole documented menu, with the cited evidence
and its limitations shown. Conditions change constraints and attach
evidence - they never turn this page into a prescription.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from menushift import hospital_image
from menushift.hospital import (
    ACCEPTABILITY_VALUES,
    AVAILABILITY_VALUES,
    CONDITIONS,
    COST_REALISTIC_VALUES,
    CURRENT_PROTEIN_LABELS,
    DEFAULT_FEEDBACK_PATH,
    METHOD_LABELS,
    METHOD_REQUIREMENTS,
    PRACTICALITY_VALUES,
    THERAPEUTIC_PRESETS,
    build_any_dish_comparison,
    build_comparison,
    build_condition_menu,
    display_text,
    get_condition,
    load_unth_menu,
    plant_protein_dataset,
    recommend_for_dish,
    submit_hospital_feedback,
    suggest_for_any_dish,
)
from menushift.safety import KNOWN_ALLERGENS

st.set_page_config(
    page_title="Hospital Menu | Naija MenuShift",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _show_alternative_image(
    dish_name: str, protein_name: str, method: str | None,
) -> None:
    """Show the AI illustration for a recommendation's top alternative.

    Bedrock mode only: local mode shows nothing, and a failed generation
    shows a short note - never a stock or substitute image.
    """
    outcome = hospital_image.generate_alternative_image(
        dish_name, protein_name, method)
    if outcome.status == "shown" and outcome.preview is not None:
        st.image(outcome.preview.content, use_container_width=True)
        st.caption(hospital_image.IMAGE_CAPTION)
    elif outcome.status == "unavailable":
        st.caption(
            "An AI illustration of this alternative could not be generated."
        )


st.title("Hospital food service — diversify the documented menu")
st.caption("Team Sprout · hospital mode · decision support for dietetics and catering teams")
st.warning(
    "Decision support only. This is not a served menu and not clinical "
    "guidance: a dietitian must approve any change before it reaches a "
    "patient."
)

menu = load_unth_menu()

st.subheader("The documented menu — UNTH Enugu therapeutic diet kitchen")
st.write(
    "Fourteen items. Fish and meat are the dishes with a documented "
    "animal protein; stew and the soups are listed without stated "
    "contents."
)
menu_frame = pd.DataFrame(
    [
        {
            "Item": dish.name,
            "Documented animal protein": dish.documented_animal_protein or "—",
            "Status": {
                "documented_animal": "Animal protein documented",
                "already_plant_based": "Already plant-based",
                "unspecified": "Contents not specified",
                "none_documented": "No animal protein documented",
            }[dish.protein_status],
            "Note": display_text(dish.notes),
        }
        for dish in menu
    ]
)
st.dataframe(menu_frame, hide_index=True, width="stretch")

with st.expander("Plant protein dataset — the catalogue the suggestions come from"):
    st.write(
        "Every plant protein the engine can suggest, with the values it "
        "ranks on. Dawadawa is listed as an adjunct: it is a seasoning "
        "used at 5–10 g per serving and is never ranked as a main protein."
    )
    dataset_frame = pd.DataFrame(
        [
            {
                "Protein": row.name,
                "Role": (
                    "Ranked candidate" if row.role == "candidate"
                    else "Adjunct (seasoning — not ranked)"
                ),
                "Protein (g/100 g)": row.protein_g_per_100g,
                "Price (NGN/kg)": row.price_ngn_per_kg,
                "Functional profile": (
                    f"Solubility {row.functional.solubility} · "
                    f"Water-holding {row.functional.water_holding} · "
                    f"Emulsification {row.functional.emulsification} · "
                    f"Gelation {row.functional.gelation}"
                ),
                "Allergens": (
                    ", ".join(row.allergens) if row.allergens
                    else "None declared"
                ),
            }
            for row in plant_protein_dataset()
        ]
    )
    st.dataframe(dataset_frame, hide_index=True, width="stretch")

st.subheader("Patient condition — menus that support dietary management")
st.write(
    "Choose a condition and both dish flows below apply that condition's "
    "constraint bundle instead of a free preset choice. The condition "
    "menu further down composes the whole documented menu under the "
    "same bundle."
)
condition_id = st.selectbox(
    "Patient condition (optional)",
    ["none", *CONDITIONS],
    format_func=lambda key: (
        "None — choose a therapeutic preset directly"
        if key == "none" else CONDITIONS[key].label
    ),
    key="patient_condition",
)
condition = None if condition_id == "none" else get_condition(condition_id)
if condition is not None:
    st.caption(display_text(
        f"Bundle applied: {condition.label} → "
        f"{THERAPEUTIC_PRESETS[condition.preset_id].label}."
    ))

st.subheader("Diversify a dish")
mode = st.radio(
    "Which dish?",
    ["Documented UNTH menu", "Any dish (type your own)"],
    horizontal=True,
)

result = None
comparison = None
feedback_dish = ""
preset_id = "standard"

if mode == "Documented UNTH menu":
    transformable = [d for d in menu if d.protein_status == "documented_animal"]
    dish_name = st.selectbox(
        "Menu item with a documented animal protein",
        [d.name for d in transformable],
    )
    if condition is not None:
        preset_id = condition.preset_id
    else:
        preset_id = st.selectbox(
            "Therapeutic preset (constraint bundle)",
            list(THERAPEUTIC_PRESETS),
            format_func=lambda key: display_text(THERAPEUTIC_PRESETS[key].label),
        )
    avoid = st.multiselect(
        "Allergen exclusions (fail closed — an excluded allergen removes the option)",
        sorted(KNOWN_ALLERGENS),
    )
    budget = st.number_input(
        "Budget cap per portion (NGN, planning parameter)",
        min_value=100.0, max_value=20000.0, value=1500.0, step=50.0,
    )
    floor = st.number_input(
        "Minimum protein per portion (g) — leave the preset's floor in place by keeping this at 0",
        min_value=0.0, max_value=100.0, value=0.0, step=1.0,
    )
    result = recommend_for_dish(
        dish_name,
        preset_id=preset_id,
        avoid_allergens=tuple(avoid),
        budget_ngn=float(budget),
        protein_floor_g=float(floor) if floor > 0 else None,
    )
    comparison = build_comparison(result)
    feedback_dish = dish_name
else:
    st.write(
        "Type any dish your kitchen serves. The same hard gates rank the "
        "plant alternatives: allergen exclusions fail closed, the protein "
        "must survive the cooking method, and the preset's floor or cap "
        "applies."
    )
    custom_name = st.text_input(
        "Dish name (as your kitchen calls it)",
        placeholder="e.g. Grilled beef skewers",
    )
    current_protein = st.selectbox(
        "Animal protein in the dish today",
        list(CURRENT_PROTEIN_LABELS),
        format_func=lambda key: CURRENT_PROTEIN_LABELS[key],
    )
    portion_g = st.number_input(
        "Portion of that protein per serving (g)",
        min_value=10.0, max_value=500.0, value=100.0, step=10.0,
    )
    method = st.selectbox(
        "Cooking method",
        list(METHOD_REQUIREMENTS),
        format_func=lambda key: METHOD_LABELS[key],
    )
    if condition is not None:
        preset_id = condition.preset_id
    else:
        preset_id = st.selectbox(
            "Therapeutic preset (constraint bundle)",
            list(THERAPEUTIC_PRESETS),
            format_func=lambda key: display_text(THERAPEUTIC_PRESETS[key].label),
        )
    avoid = st.multiselect(
        "Allergen exclusions (fail closed — an excluded allergen removes the option)",
        sorted(KNOWN_ALLERGENS),
    )
    budget = st.number_input(
        "Budget cap per portion (NGN, planning parameter)",
        min_value=100.0, max_value=20000.0, value=1500.0, step=50.0,
    )
    floor = st.number_input(
        "Minimum protein per portion (g) — leave the preset's floor in place by keeping this at 0",
        min_value=0.0, max_value=100.0, value=0.0, step=1.0,
    )
    feedback_dish = custom_name.strip() or "Any dish (unnamed)"
    if not custom_name.strip():
        st.info("Type the dish name above to get its ranked alternatives.")
    else:
        try:
            result = suggest_for_any_dish(
                custom_name,
                current_protein=current_protein,
                portion_g=float(portion_g),
                method=method,
                preset_id=preset_id,
                avoid_allergens=tuple(avoid),
                budget_ngn=float(budget),
                protein_floor_g=float(floor) if floor > 0 else None,
            )
            comparison = build_any_dish_comparison(result)
        except ValueError as exc:
            st.error(str(exc))
            result = None
            comparison = None

# Product rule (user): the site shows no data-source attributions and no
# limitation notes. Provenance and limitations stay in the data layer and
# the evidence pages; this filter keeps source/limitation notes from the
# data layer out of the rendered page while keeping functional notes.
_NOTE_SKIP_PREFIXES = (
    "Menu source:", "Preset source:", "Condition bundle:",
    "Method screen:", "No costed original is shown",
)


def _public_notes(notes, extra_skip=()):
    skip = set(extra_skip)
    return [
        note for note in notes
        if note not in skip and not note.startswith(_NOTE_SKIP_PREFIXES)
    ]


if result is not None:
    st.info(result.signoff_note)
    _skip = list(result.preset.notes)
    _baseline = getattr(result, "baseline", None)
    if _baseline is not None:
        _skip.append(_baseline.note)
    for note in _public_notes(result.notes, _skip):
        st.write("• " + display_text(note))

if comparison is not None:
    st.subheader("Original vs modified — side by side")
    st.write(f"Portion basis: {comparison.portion_g:g} g for both sides.")

    def _fmt(value: float | None, unit: str) -> str:
        return "—" if value is None else f"{value:g} {unit}"

    def _functional(profile) -> str:
        if profile is None:
            return "—"
        return (
            f"Solubility {profile.solubility} · Water-holding {profile.water_holding} · "
            f"Emulsification {profile.emulsification} · Gelation {profile.gelation}"
        )

    def _allergens(labels) -> str:
        if labels is None:
            return "—"
        return ", ".join(labels) if labels else "None declared"

    compare_frame = pd.DataFrame(
        [
            {"Measure": "Protein", "Original": _fmt(comparison.original_protein_g, "g"),
             "Modified": _fmt(comparison.alternative_protein_g, "g")},
            {"Measure": "Cost per serving", "Original": _fmt(comparison.original_cost_ngn, "NGN"),
             "Modified": _fmt(comparison.alternative_cost_ngn, "NGN")},
            {"Measure": "Prep time", "Original": _fmt(comparison.original_prep_minutes, "min"),
             "Modified": _fmt(comparison.alternative_prep_minutes, "min")},
            {"Measure": "Functional fit",
             "Original": _functional(comparison.original_functional),
             "Modified": _functional(comparison.alternative_functional)},
            {"Measure": "Allergens", "Original": _allergens(comparison.original_allergens),
             "Modified": _allergens(comparison.alternative_allergens)},
        ]
    )
    st.dataframe(compare_frame, hide_index=True, width="stretch")

if result is not None and result.alternatives:
    st.subheader("Recommended additional options (ranked)")
    for alt in result.alternatives:
        st.markdown(f"**{alt.name} — {alt.portion_g:g} g portion**")
        cols = st.columns(4)
        cols[0].metric("Protein", f"{alt.protein_g:g} g")
        cols[1].metric("Estimated cost", f"NGN {alt.cost_ngn:,.2f}")
        cols[2].metric("Prep time", f"{alt.prep_minutes:g} min")
        cols[3].metric("Allergens", ", ".join(alt.allergens) if alt.allergens else "None declared")
        st.write(
            f"Functional properties: solubility {alt.functional.solubility}, "
            f"water-holding {alt.functional.water_holding}, emulsification "
            f"{alt.functional.emulsification}, gelation {alt.functional.gelation}."
        )
        st.write(display_text(alt.kitchen_meaning))
        for reason in alt.reasons:
            st.write("• " + display_text(reason))
elif result is not None and result.status == "ok":
    st.error(
        "No plant alternative passes every hard constraint under this preset. "
        "That is a valid result — the rejected options below show exactly why."
    )

if result is not None and result.alternatives:
    _top = result.alternatives[0]
    _dish_name = getattr(result, "dish_name", None) or result.dish.name
    _show_alternative_image(_dish_name, _top.name, getattr(result, "method", None))

if result is not None and result.rejected:
    st.subheader("Rejected, with reasons (largest portion tried per protein)")
    for rej in result.rejected:
        st.write(f"**{rej.name} — {rej.portion_g:g} g**: "
                 + display_text("; ".join(rej.reasons)))

st.subheader("Condition menu — the whole documented menu, composed")
if condition is None:
    st.info(
        "Choose a patient condition above to compose its draft menu from "
        "the documented UNTH items."
    )
else:
    cm_avoid = st.multiselect(
        "Condition menu — allergen exclusions (fail closed — an excluded allergen removes the option)",
        sorted(KNOWN_ALLERGENS),
        key="condition_menu_avoid",
    )
    cm_budget = st.number_input(
        "Condition menu — budget cap per portion (NGN, planning parameter)",
        min_value=100.0, max_value=20000.0, value=1500.0, step=50.0,
        key="condition_menu_budget",
    )
    condition_menu = build_condition_menu(
        condition.id,
        avoid_allergens=tuple(cm_avoid),
        budget_ngn=float(cm_budget),
        menu=menu,
    )
    st.info(condition_menu.signoff_note)
    st.write(display_text(condition_menu.framing))
    cm_status_labels = {
        "kept_as_is": "Kept as documented — already plant-based",
        "transformed": "Diversified — additional plant option ranked",
        "no_eligible_alternative": (
            "Stays as documented — no option passed every gate"
        ),
        "confirm_with_kitchen": "Confirm recipe with the kitchen first",
    }
    cm_frame = pd.DataFrame(
        [
            {
                "Item": item.dish.name,
                "Status": cm_status_labels[item.status],
                "Additional option (top-ranked)": (
                    f"{item.alternative.name} — {item.alternative.portion_g:g} g"
                    if item.alternative is not None else "—"
                ),
                "Protein (g)": (
                    f"{item.alternative.protein_g:g}"
                    if item.alternative is not None else "—"
                ),
                "Estimated cost (NGN)": (
                    f"{item.alternative.cost_ngn:,.2f}"
                    if item.alternative is not None else "—"
                ),
                "Note": display_text(item.note),
            }
            for item in condition_menu.items
        ]
    )
    st.dataframe(cm_frame, hide_index=True, width="stretch")
    if condition_menu.transformed_protein_g is not None:
        st.write(
            "Chosen additional options across the diversified dishes: "
            f"{condition_menu.transformed_protein_g:g} g protein, "
            f"estimated NGN {condition_menu.transformed_cost_ngn:,.2f}."
        )
    for note in _public_notes(
            condition_menu.notes, condition_menu.preset.notes):
        st.write("• " + display_text(note))
    _first_transformed = next(
        (item for item in condition_menu.items
         if item.status == "transformed" and item.alternative is not None),
        None,
    )
    if _first_transformed is not None:
        st.write(
            "First diversified dish in this draft: "
            f"{_first_transformed.dish.name} with "
            f"{_first_transformed.alternative.name}."
        )
        _show_alternative_image(
            _first_transformed.dish.name,
            _first_transformed.alternative.name,
            None,
        )

st.subheader("Kitchen feedback")
st.write(
    "Used this transformation in a real kitchen? Record what you found. "
    "Feedback is recorded for team review, emailed to the team and used "
    "to improve the data and recommendations — the app does not learn "
    "automatically, and nothing changes until a person reviews it."
)
if result is not None and result.alternatives:
    feedback_alternative = result.alternatives[0].name
else:
    feedback_alternative = "none recommended"
with st.form("hospital_feedback_form"):
    fb_availability = st.selectbox("Ingredient availability", list(AVAILABILITY_VALUES))
    fb_practicality = st.selectbox("Practicality of preparation", list(PRACTICALITY_VALUES))
    fb_cost = st.selectbox("Was the cost estimate realistic?", list(COST_REALISTIC_VALUES))
    fb_acceptability = st.selectbox("Acceptability", list(ACCEPTABILITY_VALUES))
    fb_comment = st.text_area("Anything else (optional)", max_chars=2000)
    submitted = st.form_submit_button("Save feedback", width="stretch")
if submitted:
    _row, _emailed = submit_hospital_feedback(
        DEFAULT_FEEDBACK_PATH,
        dish=feedback_dish,
        alternative=feedback_alternative,
        preset=preset_id,
        availability=fb_availability,
        practicality=fb_practicality,
        cost_realistic=fb_cost,
        acceptability=fb_acceptability,
        comment=fb_comment,
    )
    if _emailed:
        st.success(
            "Feedback recorded for team review and emailed to the team. "
            "Thank you."
        )
    else:
        st.success("Feedback recorded for team review. Thank you.")
