"""Manual AWS Workshop Studio smoke test (never runs in normal CI or app startup).

Example inside authorised workshop account:
  BEDROCK_MODEL_ID=<enabled-model-id> python scripts/bedrock_agent_smoke.py

Only JSON allowed candidate IDs and numerical constraints are sent to Bedrock.
No credentials, local research files, customers or contact information sent.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from menushift.agent_contract import KitchenBrief, run_agent
from menushift.bedrock_adapter import BedrockPlanner
from menushift.kitchen_optimizer import INVENTORY_ITEMS

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    model_id = os.environ.get("BEDROCK_MODEL_ID", "")
    if not model_id:
        raise SystemExit("BEDROCK_MODEL_ID is not set. Select a model enabled by the workshop.")
    brief = KitchenBrief(
        budget_ngn=1800, min_protein_g=12, max_prep_minutes=180,
        equipment=frozenset({"grill", "press", "frying_pan"}),
        available_ingredients=frozenset(INVENTORY_ITEMS),
        preference="chewy smoky",
    )
    result = run_agent(
        BedrockPlanner(model_id),
        brief,
        ROOT / "data" / "sources",
    )
    print(json.dumps({
        "planner_invocations": result.rounds,
        "proposals_evaluated": len(result.decisions),
        "accepted": [item.identifier for item in result.accepted],
        "rejected": [
            {"id": item.proposal_id, "reason": item.reason}
            for item in result.decisions if not item.accepted
        ],
        "research_only": True,
        "human_kitchen_approval_required": True,
    }, indent=2))


if __name__ == "__main__":
    main()
