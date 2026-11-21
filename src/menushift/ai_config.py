"""Configuration for the optional AI planner (local by default, Bedrock by config).

Switching to the AWS Workshop Studio sandbox is a configuration-only change:
set MENUSHIFT_AI_MODE=bedrock and BEDROCK_MODEL_ID to an organiser-enabled
model. No AWS keys are read here; boto3 uses the normal SDK credential chain.
With no environment set, the app runs fully offline in local mode.
"""
from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

from .agent_contract import MAX_ROUNDS

AI_MODES = ("local", "bedrock")
DEFAULT_REGION = "us-east-1"  # the workshop sandbox exists only in this region


@dataclass(frozen=True)
class AIConfig:
    """Validated planner settings. Contains no secrets."""

    mode: str = "local"
    bedrock_model_id: str | None = None
    aws_region: str = DEFAULT_REGION
    max_rounds: int = MAX_ROUNDS

    @property
    def bedrock_enabled(self) -> bool:
        return self.mode == "bedrock"


def _clean(env: Mapping[str, str], name: str) -> str:
    return (env.get(name) or "").strip()


def get_ai_config(env: Mapping[str, str] | None = None) -> AIConfig:
    """Load and validate planner settings from the environment (or a mapping).

    Raises ValueError with an actionable message for any invalid value, so a
    misconfigured workshop session fails fast instead of mid-demo.
    """
    values = os.environ if env is None else env

    mode = _clean(values, "MENUSHIFT_AI_MODE").lower() or "local"
    if mode not in AI_MODES:
        raise ValueError(
            f"MENUSHIFT_AI_MODE must be 'local' or 'bedrock' (got {mode!r}). "
            "Use 'local' for the offline demo or 'bedrock' inside the AWS sandbox."
        )

    region = _clean(values, "AWS_REGION") or DEFAULT_REGION
    if region != DEFAULT_REGION:
        raise ValueError(
            f"AWS_REGION must be {DEFAULT_REGION} for this project (got {region!r}). "
            "The Hack the Fork AWS sandbox and its Bedrock model allowlist exist only "
            f"in {DEFAULT_REGION}; unset AWS_REGION or set it to {DEFAULT_REGION}."
        )

    model_id = _clean(values, "BEDROCK_MODEL_ID") or None
    if model_id is not None and (len(model_id) > 180 or any(c.isspace() for c in model_id)):
        raise ValueError(
            "BEDROCK_MODEL_ID looks invalid: it must be a single model ID or inference "
            "profile ID with no spaces. Copy it exactly from the Bedrock console "
            "(Model access / Inference profiles, us-east-1)."
        )

    raw_rounds = _clean(values, "MENUSHIFT_AI_MAX_ROUNDS")
    if raw_rounds:
        try:
            max_rounds = int(raw_rounds)
        except ValueError:
            raise ValueError(
                f"MENUSHIFT_AI_MAX_ROUNDS must be a whole number (got {raw_rounds!r})."
            ) from None
        if not 1 <= max_rounds <= MAX_ROUNDS:
            raise ValueError(
                f"MENUSHIFT_AI_MAX_ROUNDS must be between 1 and {MAX_ROUNDS} "
                f"(the agent contract hard cap; got {max_rounds})."
            )
    else:
        max_rounds = MAX_ROUNDS

    return AIConfig(mode=mode, bedrock_model_id=model_id, aws_region=region, max_rounds=max_rounds)
