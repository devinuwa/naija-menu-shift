"""Bedrock-ready agent contract with a bounded, deterministic safety/evidence gate.

A planner may propose only approved method IDs, portion masses and optional
ingredient quantities. The local evaluator is the sole authority on constraints.
This module works offline with fake proposers; AWS integration is optional.

No candidate is a kitchen-certified recipe or verified customer recommendation.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .kitchen_optimizer import EQUIPMENT_REQUIREMENTS, INVENTORY_ITEMS, RecipeCandidate, explore

MAX_ROUNDS = 2
MAX_PROPOSALS_PER_ROUND = 6
MAX_REASON_CHARS = 240
AMOUNT_LIMITS = {
    "onion_g": 60,
    "pepper_g": 25,
    "salt_g": 8,
    "seasoning_g": 12,
}
EXPECTED_KEYS = {"method_id", "portion_g", "onion_g", "pepper_g", "salt_g", "seasoning_g", "reason"}


@dataclass(frozen=True)
class KitchenBrief:
    budget_ngn: float
    min_protein_g: float
    max_prep_minutes: float
    equipment: frozenset[str]
    available_ingredients: frozenset[str]
    avoid_allergens: tuple[str, ...] = ()
    preference: str = ""
    wet_yield_kg_per_kg_dry: float = 1.75
    oil_cl: float = 1.0

    def validate(self) -> None:
        values = (
            self.budget_ngn, self.min_protein_g, self.max_prep_minutes,
            self.wet_yield_kg_per_kg_dry, self.oil_cl,
        )
        if any(not math.isfinite(float(value)) for value in values):
            raise ValueError("Non-finite brief number")
        if self.budget_ngn <= 0 or self.min_protein_g < 0 or self.max_prep_minutes <= 0:
            raise ValueError("Invalid budget/protein/time constraints")
        if not 0 < self.wet_yield_kg_per_kg_dry <= 10 or self.oil_cl < 0:
            raise ValueError("Unreasonable modelling assumptions")
        if not self.equipment <= set().union(*EQUIPMENT_REQUIREMENTS.values()):
            raise ValueError("Unknown equipment")
        if not self.available_ingredients <= set(INVENTORY_ITEMS):
            raise ValueError("Unknown inventory item")
        if len(self.preference) > 200:
            raise ValueError("Preference is too long")


@dataclass(frozen=True)
class AgentDecision:
    proposal_id: str
    accepted: bool
    reason: str
    candidate: RecipeCandidate | None = None


@dataclass(frozen=True)
class AgentRun:
    decisions: tuple[AgentDecision, ...]
    rounds: int
    planner_invoked: bool  # not evidence that an AWS or learned model was used

    @property
    def accepted(self) -> tuple[RecipeCandidate, ...]:
        return tuple(d.candidate for d in self.decisions if d.accepted and d.candidate is not None)


class Proposer(Protocol):
    """An optional, replaceable planning tool. Never trusted as a source of facts."""

    def propose(self, *, brief: KitchenBrief, feedback: tuple[str, ...], round_number: int) -> str:
        """Return JSON with key 'proposals' containing a list of bounded records."""
        ...


def _amount(value: Any, field: str, *, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be a number")
    n = float(value)
    if not math.isfinite(n) or n < 0 or n > maximum:
        raise ValueError(f"{field} outside permitted range")
    return n


def parse_proposals(payload: str) -> list[dict[str, Any]]:
    """Refuse markdown, unexpected object keys, non-finite values and oversized responses."""
    if len(payload) > 12000:
        raise ValueError("Proposal payload is too large")
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError("Planner response must be plain JSON, not Markdown") from exc
    if not isinstance(data, dict) or set(data) != {"proposals"} or not isinstance(data["proposals"], list):
        raise ValueError("Expected a single JSON object containing proposals")
    if len(data["proposals"]) > MAX_PROPOSALS_PER_ROUND:
        raise ValueError("Too many proposals in one model response")
    parsed = []
    for proposal in data["proposals"]:
        if not isinstance(proposal, dict) or set(proposal) != EXPECTED_KEYS:
            raise ValueError("Proposal schema mismatch")
        if proposal["method_id"] not in EQUIPMENT_REQUIREMENTS:
            raise ValueError("Unknown preparation method")
        portion = proposal["portion_g"]
        if isinstance(portion, bool) or not isinstance(portion, int) or not 50 <= portion <= 400:
            raise ValueError("portion_g must be a whole number from 50 to 400")
        for field, maximum in AMOUNT_LIMITS.items():
            _amount(proposal[field], field, maximum=maximum)
        reason = proposal["reason"]
        if not isinstance(reason, str) or len(reason) > MAX_REASON_CHARS:
            raise ValueError("Proposal rationale must be short text")
        parsed.append(proposal)
    return parsed


def evaluate_candidate(
    proposal: dict[str, Any],
    brief: KitchenBrief,
    sources: str | Path,
) -> AgentDecision:
    """A deterministic tool gate; model text never overrides measured input columns."""
    brief.validate()
    method = proposal["method_id"]
    portion = proposal["portion_g"]
    key = f"{method}@{portion}g"
    if method not in EQUIPMENT_REQUIREMENTS:
        return AgentDecision(key, False, "Unrecognised method")
    try:
        result = explore(
            sources,
            budget_ngn=brief.budget_ngn, protein_target_g=brief.min_protein_g,
            max_prep_minutes=brief.max_prep_minutes, equipment=brief.equipment,
            available_ingredients=brief.available_ingredients,
            portions_g=(portion,), preference=brief.preference,
            avoid_allergens=brief.avoid_allergens,
            wet_yield_kg_per_kg_dry=brief.wet_yield_kg_per_kg_dry, oil_cl=brief.oil_cl,
            onion_g=proposal["onion_g"], pepper_g=proposal["pepper_g"],
            salt_g=proposal["salt_g"], seasoning_g=proposal["seasoning_g"],
        )
    except (ValueError, OSError) as exc:
        return AgentDecision(key, False, "Calculation rejected: " + str(exc)[:220])
    item = next((c for c in result.candidates if c.identifier == key), None)
    if item is None:
        return AgentDecision(key, False, "Required equipment, ingredients or method unavailable")
    if not item.eligible:
        return AgentDecision(
            key, False,
            "; ".join(item.evaluation.reasons)[:280] or "Hard constraint violation",
        )
    return AgentDecision(
        key, True,
        "Numerically eligible under unverified price/yield/time assumptions; "
        "human kitchen and allergen review still required",
        item,
    )


def run_agent(
    proposer: Proposer, brief: KitchenBrief, sources: str | Path,
    *, max_rounds: int = MAX_ROUNDS,
) -> AgentRun:
    """Plan → check schema → evaluate with local engine → bounded feedback.

    At most two model calls and six proposals per call. Any failure abstains.
    No autonomous purchasing, deployment, external writes or secret exposure.
    """
    brief.validate()
    if not 1 <= max_rounds <= MAX_ROUNDS:
        raise ValueError("max_rounds cannot exceed the hard cap")
    feedback: list[str] = []
    decisions: list[AgentDecision] = []
    seen: set[str] = set()
    rounds = 0
    for round_number in range(1, max_rounds + 1):
        rounds = round_number
        try:
            payload = proposer.propose(
                brief=brief, feedback=tuple(feedback), round_number=round_number
            )
            proposals = parse_proposals(payload)
        except (ValueError, TypeError) as exc:
            decisions.append(AgentDecision("planner", False, "Invalid planner response: " + str(exc)[:250]))
            break
        for proposal in proposals:
            unique = json.dumps(proposal, sort_keys=True)
            if unique in seen:
                continue
            seen.add(unique)
            decision = evaluate_candidate(proposal, brief, sources)
            decisions.append(decision)
            if not decision.accepted:
                feedback.append(f"{decision.proposal_id}: {decision.reason}")
        if len([d for d in decisions if d.accepted]) >= 3 or not feedback:
            break
    return AgentRun(tuple(decisions), rounds=rounds, planner_invoked=True)


def allowed_proposal_schema() -> dict[str, Any]:
    """JSON Schema for the model-facing response; local parser remains authoritative."""
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["proposals"],
        "properties": {
            "proposals": {
                "type": "array", "maxItems": MAX_PROPOSALS_PER_ROUND,
                "items": {
                    "type": "object", "required": sorted(EXPECTED_KEYS),
                    "additionalProperties": False,
                    "properties": {
                        "method_id": {"type": "string", "enum": sorted(EQUIPMENT_REQUIREMENTS)},
                        "portion_g": {"type": "integer", "minimum": 50, "maximum": 400},
                        **{
                            key: {"type": "number", "minimum": 0, "maximum": limit}
                            for key, limit in AMOUNT_LIMITS.items()
                        },
                        "reason": {"type": "string", "maxLength": MAX_REASON_CHARS},
                    },
                },
            }
        },
    }
