"""Auditable preparation *trial* cards; not validated cooking instructions.

Steps describe what a food reviewer should test, not a certified kitchen process.
No temperatures, safe holding periods, cooking yields or sensory scores are invented.
"""
from __future__ import annotations

from dataclasses import dataclass

from .kitchen_optimizer import RecipeCandidate


@dataclass(frozen=True)
class TrialStep:
    heading: str
    instruction: str


@dataclass(frozen=True)
class RecipeTrial:
    candidate_id: str
    method: str
    steps: tuple[TrialStep, ...]
    evidence_gaps: tuple[str, ...]
    notes: tuple[str, ...]

    @property
    def cookbook_title(self) -> str:
        return f"{self.method} — Suya-inspired kitchen trial"

    def to_markdown(self, candidate: RecipeCandidate) -> str:
        """Printable cookbook-style trial card, with honest evidence disclosures.

        A cookbook structure does NOT make this a validated food-safe recipe.
        """
        lines = [
            f"# {self.cookbook_title}",
            "",
            "> **RESEARCH TEST RECIPE — Not approved for food service.**",
            "",
            "A suya-inspired awara preparation to test ingredient costs, skewer stability",
            "and practical serving yields under documented kitchen conditions.",
            "",
            "## At a glance",
            "- **Yield:** 1 experimental portion (final mass not measured)",
            f"- **Target finished mass:** {candidate.portion_g:.0f} g (model assumption)",
            f"- **Time:** {candidate.evaluation.prep_minutes:.0f} minutes (unmeasured estimate)",
            f"- **Listed ingredient + processing cost:** ₦{candidate.evaluation.cost_ngn:.2f}",
            f"- **Estimated protein:** {candidate.evaluation.protein_g:.1f} g (source-food proxy)",
            "- **Allergens:** Contains soy; additional seasoning/cross-contact review required.",
            "- **Equipment:** " + ", ".join(sorted(candidate.required_equipment)),
            "",
            "## Ingredients (purchased amounts, not measured finished quantities)",
        ]
        for ingredient in candidate.ingredient_lines:
            lines.append(f"- {ingredient.purchase_g:.1f} g {ingredient.name}")
        if candidate.oil_cl:
            lines.append(
                f"- {candidate.oil_cl:g} cl vegetable oil allowance for the fried variant "
                "(model input; oil absorption unmeasured)"
            )
        lines.extend([
            ("- **Yaji / suya spice mix:** Not specified by the verified dataset; obtain a "
             "reviewed, weighed formulation before any actual serving."),
            "",
            "## Method — numbered kitchen trial",
        ])
        for number, step in enumerate(self.steps, 1):
            lines.append(f"{number}. **{step.heading}.** {step.instruction}")
        lines.extend([
            "",
            "## Practical checks before tasting or serving",
            "- Record weighed raw, processed and final portions, cooking duration, oil uptake and fuel.",
            "- Confirm soy and peanut/yaji allergens, packaged seasoning labels and shared equipment.",
            ("- Use the food specialist's approved handling and cooking procedure; no invented "
             "temperature, storage or safety guarantees appear in this card."),
            "",
            "## Price and nutrition evidence",
        ])
        for ingredient in candidate.ingredient_lines:
            lines.extend([
                (f"- **{ingredient.name}** — estimated ₦{ingredient.estimated_cost_ngn:.2f} "
                 f"for {ingredient.purchase_g:.1f} g; "
                 f"~{ingredient.estimated_protein_g:.2f} g modelled protein"),
                f"  - Price: {ingredient.source}",
                (f"  - Nutrition: {ingredient.nutrition_source} "
                 f"({ingredient.nutrition_state}); label: {ingredient.allergen_labels or 'unreviewed'}"),
            ])
        lines.extend([
            "",
            "## Measurements needed for a real recipe",
        ])
        lines.extend(f"- {gap}" for gap in self.evidence_gaps)
        lines.extend(["", "## Limitations"])
        lines.extend(f"- {note}" for note in self.notes)
        return "\n".join(lines) + "\n"


METHOD_PROCEDURES = {
    "awara_firm": TrialStep(
        "Unpressed trial",
        "Cut a measured portion of firm awara; test whether pieces hold during "
        "handling and grilling. Record breakage and actual finished mass.",
    ),
    "awara_pressed": TrialStep(
        "Pressed trial",
        "Weigh curd before and after pressing, record drained liquid, and assess "
        "handling and chewiness. Pressing removes water; it does not create protein.",
    ),
    "awara_frozen": TrialStep(
        "Freeze–thaw trial",
        "Use the kitchen's documented safe cold-storage and thawing procedure; "
        "measure freeze/thaw time, lost liquid and skewer stability. The displayed "
        "time is NOT a measured full freeze–thaw cycle.",
    ),
    "awara_fried": TrialStep(
        "Fried trial",
        "Weigh the curd before and after frying and record oil used, oil retained, "
        "fuel and texture. Do not treat the generic fried-tofu nutrient profile as "
        "a measurement of this recipe.",
    ),
}


def build_trial(candidate: RecipeCandidate) -> RecipeTrial:
    """Generate a transparent test protocol only for a hard-constraint eligible option."""
    if not candidate.eligible:
        raise ValueError("Cannot create a suggested trial card for an ineligible recipe")
    method = candidate.evaluation.option_id
    if method not in METHOD_PROCEDURES:
        raise ValueError("Unknown or unsupported trial preparation method")
    steps = (
        TrialStep(
            "Verify stock and labels",
            "Check the physical ingredient packages, declared soy and seasoning "
            "allergens and actual availability. Check shared-surface cross-contact "
            "with the food-safety lead before preparing for anyone.",
        ),
        TrialStep(
            "Record starting material",
            "Weigh purchased awara and every selected spice/seasoning separately. "
            "Record actual local prices, date, market and package size.",
        ),
        METHOD_PROCEDURES[method],
        TrialStep(
            "Seasoning study",
            "Use only ingredients whose labels and quantities were reviewed by the "
            "team. A full suya yaji formulation is NOT yet validated by this dataset.",
        ),
        TrialStep(
            "Grill and record",
            "Have the food-science reviewer set a safe cooking and handling protocol. "
            "Record fuel use, time, skewering/basket stability, and finished portion mass.",
        ),
        TrialStep(
            "Blind sensory check",
            "Use an agreed scoring sheet for texture, aroma, appearance, flavour and "
            "acceptability. Record actual reviewer responses; do not infer taste from text.",
        ),
    )
    gaps = (
        "Local finished-awara supplier quote or measured soy-to-tofu batch manufacturing cost",
        "Measured purchased-to-finished yield (including pressing/freezing/frying losses)",
        "Method-specific electricity, gas/charcoal, labour, coagulant and packaging costs",
        "Measured oil uptake where fried; genuine prep duration including freeze/thaw",
        "Matched local food-form nutritional analysis and nutrient retention",
        "Yaji/seasoning recipe, source, animal-derived ingredients and allergen review",
        "Food-safety review and recorded blind sensory panel before any service claim",
    )
    notes = (
        "All numerical estimates may be incomplete; do not call this a retail price or full cost.",
        "Soy is present. Unreviewed ingredient labels and cross-contact cannot be certified safe.",
        "A modelled protein target is not a clinical or dietary adequacy claim.",
        "The option must be approved and tested by an appropriate food/kitchen professional.",
    )
    return RecipeTrial(candidate.identifier, candidate.method, steps, gaps, notes)
