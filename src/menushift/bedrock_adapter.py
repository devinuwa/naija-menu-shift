"""Optional Amazon Bedrock Converse planner; *never* called on Streamlit page load.

Uses temporary workshop credentials from the normal AWS SDK credential chain.
No keys stored, no data persistence, no autonomous external actions.
Tested only with a fake Converse client until workshop model access is granted.
"""
from __future__ import annotations

import json
from typing import Any

from .agent_contract import KitchenBrief, allowed_proposal_schema

SYSTEM_PROMPT = (
    "You are a bounded formulation-proposal planner for a Nigerian food research prototype. "
    "Return ONLY one JSON object with key 'proposals' following the schema given by the user. "
    "Use only the specified existing option IDs; no additional ingredients or methods. "
    "Do not invent prices, nutrients, cooking times, sensory outcomes, medical claims, "
    "food-safety approval, new data sources, customer preferences or ingredients. "
    "You are NOT deciding recipe feasibility. A separate local calculator will reject "
    "anything that fails constraints. Do not claim a recipe is safe or ready to sell. "
    "At most six proposals per call, no free-form instructions outside JSON."
)


class BedrockPlanner:
    """An adapter for the event sandbox in us-east-1; inject a fake client for tests."""

    def __init__(self, model_id: str, *, client: Any | None = None, region: str = "us-east-1"):
        if region != "us-east-1":
            raise ValueError("Hackathon AWS environment is restricted to us-east-1")
        if not model_id or len(model_id) > 180 or any(c.isspace() for c in model_id):
            raise ValueError("Select an enabled Bedrock model ID or inference profile")
        self.model_id = model_id
        if client is None:
            try:
                import boto3  # type: ignore[import-not-found]
            except ImportError as exc:
                raise RuntimeError(
                    "Install the optional aws extra in the workshop: pip install -e '.[aws]'"
                ) from exc
            client = boto3.client("bedrock-runtime", region_name=region)
        self.client = client

    def propose(self, *, brief: KitchenBrief, feedback: tuple[str, ...], round_number: int) -> str:
        brief.validate()
        # Only restricted fields, no raw uploaded data, customer names or private prices.
        payload = {
            "round": round_number,
            "budget_ngn": brief.budget_ngn,
            "min_estimated_protein_g": brief.min_protein_g,
            "max_prep_minutes": brief.max_prep_minutes,
            "equipment": sorted(brief.equipment),
            "available_ingredients": sorted(brief.available_ingredients),
            "allergen_exclusions": list(brief.avoid_allergens),
            "preference_keywords": brief.preference,
            "feedback": list(feedback[-8:]),
            "response_json_schema": allowed_proposal_schema(),
            "reminder": "Numbers are unvalidated estimates; no new prices or nutrition.",
        }
        try:
            response = self.client.converse(
                modelId=self.model_id,
                system=[{"text": SYSTEM_PROMPT}],
                messages=[
                    {"role": "user", "content": [{"text": json.dumps(payload, sort_keys=True)}]}
                ],
                inferenceConfig={"maxTokens": 900, "temperature": 0.0},
            )
            parts = response["output"]["message"]["content"]
            raw = "".join(item.get("text", "") for item in parts if isinstance(item, dict))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Unexpected Bedrock response; check workshop model support") from exc
        if not raw:
            raise ValueError("Model returned no plain-text JSON proposal")
        return raw
