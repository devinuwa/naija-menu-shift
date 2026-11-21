"""Frozen synthetic decision cases for the recommendation benchmark.

These rows use the fictional demo dataset. They are a reproducible test matrix,
not restaurant observations and not a license to retune weights.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    label: str
    note: str
    budget_ngn: float
    protein_target_g: float
    max_prep_minutes: float
    preference: str
    avoid_allergens: tuple[str, ...] = ()
    expects_feasible: bool = True

    def as_constraints(self) -> dict:
        return {
            "budget_ngn": self.budget_ngn,
            "protein_target_g": self.protein_target_g,
            "max_prep_minutes": self.max_prep_minutes,
            "preference": self.preference,
            "avoid_allergens": self.avoid_allergens,
        }


# Weights stay 45% cost, 25% protein, 15% time, 15% text. Do not edit this tuple
# to chase a preferred winner; add a new dated set instead.
SYNTHETIC_SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        scenario_id="normal_serving",
        label="Normal serving",
        note="Synthetic demo. Budget 1500 naira, 10 g estimated protein, 120 minutes, preference 'chewy smoky grilled'. Both text methods pick pressed tofu over the cheaper plain option.",
        budget_ngn=1500,
        protein_target_g=10,
        max_prep_minutes=120,
        preference="chewy smoky grilled",
    ),
    Scenario(
        scenario_id="preference_shift",
        label="Crispy fried preference",
        note="Synthetic demo. Wide budget and preference 'crispy fried'. Keyword overlap selects fried tofu. TF-IDF still selects the cheaper plain option.",
        budget_ngn=5000,
        protein_target_g=5,
        max_prep_minutes=180,
        preference="crispy fried",
    ),
    Scenario(
        scenario_id="short_prep",
        label="Short preparation window",
        note="Synthetic demo. A 40 minute limit leaves only the faster plant option eligible.",
        budget_ngn=5000,
        protein_target_g=5,
        max_prep_minutes=40,
        preference="chewy smoky grilled",
    ),
    Scenario(
        scenario_id="no_feasible",
        label="No feasible plant option",
        note="Synthetic demo. A ₦1 budget is below every plant serving. Every ranker must abstain. Beef stays a reference.",
        budget_ngn=1,
        protein_target_g=10,
        max_prep_minutes=120,
        preference="chewy smoky grilled",
        expects_feasible=False,
    ),
)


def scenario_by_id(scenario_id: str) -> Scenario:
    for scenario in SYNTHETIC_SCENARIOS:
        if scenario.scenario_id == scenario_id:
            return scenario
    raise KeyError(scenario_id)
