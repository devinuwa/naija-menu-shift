"""Frozen synthetic benchmark for keyword vs TF-IDF vs cheapest baselines."""
import json

import pytest

from menushift.cli import main
from menushift.engine import compare_rankers, evaluate
from menushift.scenarios import SYNTHETIC_SCENARIOS, scenario_by_id


def _text(row):
    return dict(row.score_breakdown)["text_match"]


def test_frozen_set_has_a_change_and_a_no_change(demo):
    changed = 0
    unchanged = 0
    for scenario in SYNTHETIC_SCENARIOS:
        report = compare_rankers(demo, "suya", **scenario.as_constraints())
        rows = evaluate(demo, "suya", **scenario.as_constraints())
        assert all(not row.feasible for row in rows if not row.plant_only)
        assert report["keyword_hybrid"] != "beef_suya"
        assert report["tfidf_hybrid"] != "beef_suya"
        if scenario.expects_feasible:
            assert not report["abstained"]
            assert report["cheapest_feasible_plant"]
        else:
            assert report["abstained"]
            assert report["keyword_hybrid"] is None
            assert report["tfidf_hybrid"] is None
            assert report["text_changes_winner"] is False
        if report["text_changes_winner"]:
            changed += 1
        elif not report["abstained"]:
            unchanged += 1
    assert changed >= 1
    assert unchanged >= 1


def test_normal_serving_text_prefers_pressed_over_cheapest(demo):
    scenario = scenario_by_id("normal_serving")
    report = compare_rankers(demo, "suya", **scenario.as_constraints())
    assert report["abstained"] is False
    assert report["cheapest_feasible_plant"] == "tofu_plain"
    assert report["keyword_hybrid"] == "tofu_pressed"
    assert report["tfidf_hybrid"] == "tofu_pressed"
    assert report["text_changes_winner"] is True
    assert report["methods_disagree"] is False


def test_crispy_preference_moves_keyword_hybrid_off_cheapest(demo):
    scenario = scenario_by_id("preference_shift")
    report = compare_rankers(demo, "suya", **scenario.as_constraints())
    assert report["cheapest_plant_unconstrained"] == "tofu_plain"
    assert report["cheapest_feasible_plant"] == "tofu_plain"
    assert report["keyword_hybrid"] == "tofu_fried"
    assert report["tfidf_hybrid"] == "tofu_plain"
    assert report["methods_disagree"] is True
    assert report["text_changes_winner"] is True


def test_short_prep_leaves_only_plain_tofu(demo):
    scenario = scenario_by_id("short_prep")
    rows = evaluate(demo, "suya", **scenario.as_constraints())
    assert [row.option_id for row in rows if row.feasible] == ["tofu_plain"]
    report = compare_rankers(demo, "suya", **scenario.as_constraints())
    assert report["keyword_hybrid"] == report["tfidf_hybrid"] == "tofu_plain"
    assert report["methods_disagree"] is False


def test_impossible_budget_abstains(demo):
    scenario = scenario_by_id("no_feasible")
    report = compare_rankers(demo, "suya", **scenario.as_constraints())
    assert report["abstained"] is True
    assert report["cheapest_plant_unconstrained"] == "tofu_plain"
    assert report["cheapest_feasible_plant"] is None


def test_soy_exclusion_abstains_for_every_ranker(demo):
    report = compare_rankers(demo, "suya", budget_ngn=100000, protein_target_g=0,
                             avoid_allergens=["soy"])
    assert report["abstained"] is True
    assert report["keyword_hybrid"] is None
    assert report["tfidf_hybrid"] is None


def test_lexical_text_term_differs_from_tfidf_on_fried_option(demo):
    scenario = scenario_by_id("preference_shift")
    lexical = evaluate(demo, "suya", text_method="lexical", **scenario.as_constraints())
    tfidf = evaluate(demo, "suya", text_method="tfidf", **scenario.as_constraints())
    fried_lexical = next(row for row in lexical if row.option_id == "tofu_fried")
    fried_tfidf = next(row for row in tfidf if row.option_id == "tofu_fried")
    assert _text(fried_lexical) != _text(fried_tfidf)
    assert any("lexical" in reason for reason in fried_lexical.reasons)
    assert any("tfidf" in reason for reason in fried_tfidf.reasons)


def test_ranking_is_stable(demo):
    kwargs = scenario_by_id("preference_shift").as_constraints()
    first = evaluate(demo, "suya", **kwargs)
    second = evaluate(demo, "suya", **kwargs)
    assert [(row.option_id, row.score, row.feasible) for row in first] == [
        (row.option_id, row.score, row.feasible) for row in second
    ]


def test_unknown_text_method_rejected(demo):
    with pytest.raises(ValueError, match="text_method"):
        evaluate(demo, "suya", budget_ngn=1500, protein_target_g=10, text_method="taste")


def test_cli_includes_ranker_comparison(capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["menushift", "--dish", "suya", "--budget", "1500", "--protein", "10"])
    main()
    payload = json.loads(capsys.readouterr().out)
    comparison = payload["ranker_comparison"]
    assert set(comparison) >= {
        "cheapest_plant_unconstrained",
        "cheapest_feasible_plant",
        "keyword_hybrid",
        "tfidf_hybrid",
        "text_changes_winner",
        "abstained",
    }
    assert comparison["tfidf_hybrid"] != "beef_suya"
