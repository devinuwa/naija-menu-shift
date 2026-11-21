"""Manual smoke test for the AI planner integration layer (never runs in CI).

  python scripts/ai_connection_smoke.py
      Local mode (default): runs the full agent loop offline and prints the
      gate's accept/reject decisions for a sample brief.

  MENUSHIFT_AI_MODE=bedrock BEDROCK_MODEL_ID=<enabled-model-id> \
      python scripts/ai_connection_smoke.py
      Bedrock mode: makes ONE Converse call through the adapter and reports
      latency plus whether the strict proposal parser accepted the output.

Prints the resolved configuration only. Credentials are never read or printed
here; boto3 resolves them from the normal AWS SDK chain in the workshop.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from menushift.agent_contract import KitchenBrief, parse_proposals, run_agent
from menushift.ai_config import get_ai_config
from menushift.kitchen_optimizer import INVENTORY_ITEMS
from menushift.proposer_factory import build_proposer

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "sources"

try:  # botocore ships with the optional aws extra; bedrock mode implies it
    from botocore.exceptions import BotoCoreError

    INVOKE_ERRORS: tuple[type[Exception], ...] = (BotoCoreError, ValueError, RuntimeError, OSError)
except ImportError:  # pragma: no cover - local mode without the aws extra
    INVOKE_ERRORS = (ValueError, RuntimeError, OSError)

SAMPLE_BRIEF = KitchenBrief(
    budget_ngn=2000, min_protein_g=10, max_prep_minutes=200,
    equipment=frozenset({"grill", "press", "freezer", "frying_pan"}),
    available_ingredients=frozenset(INVENTORY_ITEMS),
    preference="chewy smoky",
)


def main() -> int:
    try:
        config = get_ai_config()
    except ValueError as exc:
        print(f"CONFIG ERROR: {exc}")
        return 2
    print("MenuShift AI integration smoke test")
    print(f"  mode:        {config.mode}")
    print(f"  aws_region:  {config.aws_region}")
    print(f"  model_id:    {config.bedrock_model_id or '(unset)'}")
    print(f"  max_rounds:  {config.max_rounds}")
    print("  credentials: resolved by boto3 from the session only; never printed")

    try:
        proposer = build_proposer(config, sources=SOURCES)
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"SETUP ERROR: {exc}")
        print("Fallback: set MENUSHIFT_AI_MODE=local and re-run for the offline demo.")
        return 2

    if config.mode == "local":
        run = run_agent(proposer, SAMPLE_BRIEF, SOURCES, max_rounds=config.max_rounds)
        print(f"Agent loop finished in {run.rounds} round(s); "
              f"{len(run.decisions)} proposal(s) evaluated:")
        for decision in run.decisions:
            verdict = "ACCEPT" if decision.accepted else "REJECT"
            print(f"  [{verdict}] {decision.proposal_id} - {decision.reason}")
        print(f"Accepted candidates: {[c.identifier for c in run.accepted] or 'none'}")
        print("Local mode OK: the full propose -> parse -> gate loop works offline.")
        return 0

    print("Bedrock mode: making ONE Converse call through the adapter...")
    started = time.perf_counter()
    try:
        payload = proposer.propose(brief=SAMPLE_BRIEF, feedback=(), round_number=1)
    except INVOKE_ERRORS as exc:  # connection/model errors must be reported, not hidden
        print(f"INVOKE ERROR ({type(exc).__name__}): {exc}")
        print("Check: model access enabled in us-east-1, BEDROCK_MODEL_ID matches an "
              "organiser-enabled model, and the workshop session credentials are active. "
              "Fallback: MENUSHIFT_AI_MODE=local.")
        return 1
    latency = time.perf_counter() - started
    print(f"  latency: {latency:.2f}s; response {len(payload)} chars")
    try:
        proposals = parse_proposals(payload)
    except ValueError as exc:
        print(f"  parser: REJECTED model output - {exc}")
        print("The strict gate worked as designed: unusable model output is refused, "
              "not repaired. Record this as the reject example for the demo log.")
        return 0
    print(f"  parser: ACCEPTED {len(proposals)} proposal(s): "
          f"{[p['method_id'] + '@' + str(p['portion_g']) + 'g' for p in proposals]}")
    print("Bedrock mode OK: model reachable and its output passed the strict schema. "
          "Run scripts/bedrock_agent_smoke.py for the full gated agent loop.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
