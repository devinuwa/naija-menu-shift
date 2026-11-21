"""Human-reviewed benchmark rules. Fixtures in this file are SYNTHETIC."""

import csv
from datetime import date
from pathlib import Path

import pytest

from menushift.benchmark import (
    REVIEW_COLUMNS,
    benchmark_reviews,
    read_review_cases,
)
from menushift.engine import load_dataset

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def demo_data():
    return load_dataset(ROOT / "data" / "demo", demo=True)


def _case(case_id, *, option, budget=1500.0):
    return {
        "case_id": case_id,
        "reviewer_id": "TEST-ONLY-NOT-A-REAL-REVIEWER",
        "reviewer_role": "synthetic test fixture",
        "reviewed_on": date.today().isoformat(),
        "evidence_reference": "SYNTHETIC-UNIT-TEST",
        "approval_status": "approved",
        "dish_id": "suya",
        "budget_ngn": str(budget),
        "protein_target_g": "10",
        "max_prep_minutes": "120",
        "preference": "chewy smoky grilled",
        "avoid_allergens": "",
        "reviewer_preferred_option_id": option,
    }


def test_empty_reviewer_template_explicitly_blocks_metrics():
    with pytest.raises(ValueError, match="No independently reviewed"):
        read_review_cases(ROOT / "data" / "evaluation" / "reviewer_cases.csv")


def test_review_loader_rejects_unapproved_and_missing_source(tmp_path):
    file = tmp_path / "reviews.csv"
    row = _case("test", option="tofu_pressed")
    row["approval_status"] = "draft"
    with file.open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        writer.writerow(row)
    with pytest.raises(ValueError, match="approve"):
        read_review_cases(file)
    row["approval_status"] = "approved"
    row["evidence_reference"] = ""
    with file.open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        writer.writerow(row)
    with pytest.raises(ValueError, match="required"):
        read_review_cases(file)


def test_no_reviewed_protein_claims_from_demo_data(demo_data):
    with pytest.raises(ValueError, match="verified"):
        benchmark_reviews(demo_data, [_case("test", option="tofu_pressed")])


def test_fixture_comparison_reports_counts_not_model_uplift(demo_data):
    outcome = benchmark_reviews(
        demo_data,
        [_case("one", option="tofu_pressed")],
        allow_synthetic_fixture=True,
    )
    assert outcome.reviewed_cases == 1
    assert outcome.dataset_kind.startswith("SYNTHETIC")
    assert outcome.cheapest_feasible_agreements in (0, 1)
    assert outcome.keyword_agreements in (0, 1)
    assert outcome.tfidf_agreements in (0, 1)


def test_review_must_be_a_valid_plant_candidate(demo_data):
    with pytest.raises(ValueError, match="plant option"):
        benchmark_reviews(
            demo_data, [_case("beef", option="beef_suya")],
            allow_synthetic_fixture=True,
        )


def test_no_feasible_review_case_is_counted_as_abstention(demo_data):
    item = _case("abstain", option="NONE", budget=1.0)
    outcome = benchmark_reviews(demo_data, [item], allow_synthetic_fixture=True)
    assert outcome.abstention_cases == 1
    assert outcome.cheapest_feasible_agreements == 1
    assert outcome.tfidf_agreements == 1


def test_nonfinite_budget_is_rejected(demo_data):
    item = _case("bad", option="tofu_pressed", budget=float("nan"))
    with pytest.raises(ValueError, match="invalid"):
        benchmark_reviews(demo_data, [item], allow_synthetic_fixture=True)
