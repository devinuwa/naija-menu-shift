"""Build the planner selected by AIConfig.

Local mode returns a deterministic offline proposer driven by the same
explorer the Streamlit studio uses, so the full agent loop (propose -> strict
parse -> deterministic gate) can be demonstrated with no AWS access. Bedrock
mode returns the existing BedrockPlanner adapter; the model is never trusted
and every proposal still passes the local gate in agent_contract.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from .agent_contract import MAX_PROPOSALS_PER_ROUND, KitchenBrief, Proposer
from .ai_config import AIConfig
from .kitchen_optimizer import explore

DEFAULT_SOURCES = Path(__file__).resolve().parents[2] / "data" / "sources"
DEFAULT_PORTIONS_G = (80, 100, 120, 140, 160, 180, 200)


class LocalExplorerProposer:
    """Deterministic offline Proposer backed by kitchen_optimizer.explore.

    Proposals are the explorer's own eligible candidates (Pareto frontier
    first), re-checked later by evaluate_candidate, so an accepted local
    proposal means exactly what an accepted Bedrock proposal means.
    Spice quantities are proposed as 0: the explorer's feasibility figures
    are computed at those amounts, keeping proposal and gate consistent.
    Candidates rejected in an earlier round (named in the feedback) are
    not proposed again.
    """

    def __init__(self, sources: str | Path, *, portions_g: tuple[int, ...] = DEFAULT_PORTIONS_G):
        self.sources = Path(sources)
        if not self.sources.is_dir():
            raise FileNotFoundError(
                f"Local menu data not found at {self.sources}. Run from the repo root "
                "or pass sources=<path to data/sources> to build_proposer()."
            )
        self.portions_g = portions_g

    def propose(self, *, brief: KitchenBrief, feedback: tuple[str, ...], round_number: int) -> str:
        brief.validate()
        rejected = {
            entry.split(":", 1)[0].strip()
            for entry in feedback
            if "@" in entry.split(":", 1)[0]
        }
        try:
            result = explore(
                self.sources,
                budget_ngn=brief.budget_ngn, protein_target_g=brief.min_protein_g,
                max_prep_minutes=brief.max_prep_minutes, equipment=brief.equipment,
                available_ingredients=brief.available_ingredients,
                portions_g=self.portions_g, preference=brief.preference,
                avoid_allergens=brief.avoid_allergens,
                wet_yield_kg_per_kg_dry=brief.wet_yield_kg_per_kg_dry, oil_cl=brief.oil_cl,
            )
        except OSError as exc:
            raise ValueError(f"Local exploration failed: {exc}") from exc
        frontier_ids = {c.identifier for c in result.frontier}
        ordered = sorted(
            result.eligible,
            key=lambda c: (c.identifier not in frontier_ids, c.identifier),
        )
        proposals = []
        for candidate in ordered:
            if candidate.identifier in rejected:
                continue
            proposals.append({
                "method_id": candidate.evaluation.option_id,
                "portion_g": int(candidate.portion_g),
                "onion_g": 0, "pepper_g": 0, "salt_g": 0, "seasoning_g": 0,
                "reason": (
                    f"Offline explorer candidate {candidate.identifier}: eligible under the "
                    "brief on modelled estimates; not kitchen validated"
                ),
            })
            if len(proposals) >= MAX_PROPOSALS_PER_ROUND:
                break
        return json.dumps({"proposals": proposals})


def build_proposer(config: AIConfig, *, sources: str | Path | None = None) -> Proposer:
    """Return the planner for the configured mode.

    Bedrock mode fails fast with an actionable message when the model ID or
    the optional boto3 dependency is missing, instead of failing mid-demo.
    """
    if config.mode == "local":
        return LocalExplorerProposer(sources if sources is not None else DEFAULT_SOURCES)
    if config.mode != "bedrock":
        raise ValueError(f"Unknown AI mode {config.mode!r}; expected 'local' or 'bedrock'")
    if not config.bedrock_model_id:
        raise RuntimeError(
            "MENUSHIFT_AI_MODE=bedrock but BEDROCK_MODEL_ID is not set. "
            "In the AWS sandbox (Bedrock console, us-east-1), confirm which model the "
            "organisers enabled, then set BEDROCK_MODEL_ID=<that model id>. "
            "To run offline instead, set MENUSHIFT_AI_MODE=local."
        )
    if importlib.util.find_spec("boto3") is None:
        raise RuntimeError(
            "boto3 is not installed, so Bedrock mode cannot start. Install the optional "
            "AWS extra inside the workshop environment: python -m pip install -e '.[aws]' "
            "(do not add it to the public Streamlit deployment). "
            "To run offline instead, set MENUSHIFT_AI_MODE=local."
        )
    from .bedrock_adapter import BedrockPlanner

    return BedrockPlanner(config.bedrock_model_id, region=config.aws_region)
