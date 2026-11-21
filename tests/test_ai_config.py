"""Tests for the AI planner config loader and proposer factory.

Local mode must work with no environment and no network. Bedrock mode is
tested only up to construction: no model is ever invoked here.
"""
from pathlib import Path

import pytest

from menushift.agent_contract import (
    EQUIPMENT_REQUIREMENTS,
    KitchenBrief,
    evaluate_candidate,
    parse_proposals,
    run_agent,
)
from menushift.ai_config import AIConfig, get_ai_config
from menushift.kitchen_optimizer import INVENTORY_ITEMS
from menushift.proposer_factory import LocalExplorerProposer, build_proposer

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "sources"
FULL_EQUIPMENT = frozenset({"grill", "press", "freezer", "frying_pan"})


def feasible_brief(**overrides):
    settings = {
        "budget_ngn": 2000.0,
        "min_protein_g": 10.0,
        "max_prep_minutes": 200.0,
        "equipment": FULL_EQUIPMENT,
        "available_ingredients": frozenset(INVENTORY_ITEMS),
    }
    settings.update(overrides)
    return KitchenBrief(**settings)


# --- config loading -------------------------------------------------------


def test_defaults_are_local_offline_and_us_east_1():
    config = get_ai_config({})
    assert config == AIConfig(mode="local", bedrock_model_id=None,
                              aws_region="us-east-1", max_rounds=2)
    assert not config.bedrock_enabled


def test_mode_and_model_id_are_normalised():
    config = get_ai_config({"MENUSHIFT_AI_MODE": " Bedrock ",
                            "BEDROCK_MODEL_ID": "amazon.nova-micro-v1:0"})
    assert config.mode == "bedrock"
    assert config.bedrock_enabled
    assert config.bedrock_model_id == "amazon.nova-micro-v1:0"


def test_unknown_mode_rejected():
    with pytest.raises(ValueError, match="MENUSHIFT_AI_MODE"):
        get_ai_config({"MENUSHIFT_AI_MODE": "cloud"})


def test_non_us_east_1_region_rejected():
    with pytest.raises(ValueError, match="us-east-1"):
        get_ai_config({"AWS_REGION": "eu-west-2"})


def test_model_id_with_spaces_rejected():
    with pytest.raises(ValueError, match="BEDROCK_MODEL_ID"):
        get_ai_config({"BEDROCK_MODEL_ID": "not a model id"})


@pytest.mark.parametrize("raw,expected", [("1", 1), ("2", 2)])
def test_max_rounds_within_cap_accepted(raw, expected):
    assert get_ai_config({"MENUSHIFT_AI_MAX_ROUNDS": raw}).max_rounds == expected


@pytest.mark.parametrize("raw", ["0", "3", "two"])
def test_max_rounds_out_of_range_or_invalid_rejected(raw):
    with pytest.raises(ValueError, match="MENUSHIFT_AI_MAX_ROUNDS"):
        get_ai_config({"MENUSHIFT_AI_MAX_ROUNDS": raw})


def test_config_is_immutable():
    config = get_ai_config({})
    with pytest.raises(AttributeError):
        config.mode = "bedrock"


# --- factory behaviour ------------------------------------------------------


def test_factory_local_mode_needs_no_env_and_no_aws():
    proposer = build_proposer(get_ai_config({}), sources=SOURCES)
    assert isinstance(proposer, LocalExplorerProposer)


def test_factory_bedrock_without_model_id_gives_actionable_error():
    config = get_ai_config({"MENUSHIFT_AI_MODE": "bedrock"})
    with pytest.raises(RuntimeError, match="BEDROCK_MODEL_ID is not set"):
        build_proposer(config, sources=SOURCES)


def test_factory_bedrock_with_model_id_builds_existing_adapter(monkeypatch):
    pytest.importorskip("boto3")
    # Construction only: dummy session credentials keep boto3 away from the
    # instance-metadata endpoint; the client is never invoked in tests.
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    from menushift.bedrock_adapter import BedrockPlanner

    config = get_ai_config({"MENUSHIFT_AI_MODE": "bedrock",
                            "BEDROCK_MODEL_ID": "amazon.nova-micro-v1:0"})
    proposer = build_proposer(config, sources=SOURCES)
    assert isinstance(proposer, BedrockPlanner)
    assert proposer.model_id == "amazon.nova-micro-v1:0"


# --- local proposer against the real contract --------------------------------


def test_local_proposer_output_passes_strict_parser():
    proposer = build_proposer(get_ai_config({}), sources=SOURCES)
    payload = proposer.propose(brief=feasible_brief(), feedback=(), round_number=1)
    proposals = parse_proposals(payload)
    assert proposals, "feasible brief should produce at least one proposal"
    assert all(p["method_id"] in EQUIPMENT_REQUIREMENTS for p in proposals)
    assert len(proposals) <= 6


def test_local_proposals_are_accepted_by_the_real_gate():
    brief = feasible_brief()
    proposer = build_proposer(get_ai_config({}), sources=SOURCES)
    proposals = parse_proposals(proposer.propose(brief=brief, feedback=(), round_number=1))
    decisions = [evaluate_candidate(p, brief, SOURCES) for p in proposals]
    assert any(d.accepted for d in decisions), (
        "explorer-derived proposals must survive the same gate Bedrock faces"
    )


def test_local_agent_loop_runs_end_to_end_offline():
    brief = feasible_brief()
    proposer = build_proposer(get_ai_config({}), sources=SOURCES)
    run = run_agent(proposer, brief, SOURCES, max_rounds=2)
    assert run.planner_invoked
    assert run.accepted, "offline demo loop should accept at least one candidate"


def test_local_proposer_abstains_when_nothing_is_feasible():
    proposer = build_proposer(get_ai_config({}), sources=SOURCES)
    payload = proposer.propose(brief=feasible_brief(budget_ngn=1.0), feedback=(), round_number=1)
    assert parse_proposals(payload) == []


def test_local_proposer_does_not_repeat_rejected_candidates():
    brief = feasible_brief()
    proposer = build_proposer(get_ai_config({}), sources=SOURCES)
    first = parse_proposals(proposer.propose(brief=brief, feedback=(), round_number=1))
    rejected_id = f"{first[0]['method_id']}@{first[0]['portion_g']}g"
    second = parse_proposals(proposer.propose(
        brief=brief, feedback=(f"{rejected_id}: rejected in probe",), round_number=2,
    ))
    assert all(
        f"{p['method_id']}@{p['portion_g']}g" != rejected_id for p in second
    )
