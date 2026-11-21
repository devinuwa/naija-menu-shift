"""Reproducible comparison against independently reviewed restaurant scenarios.

A source spreadsheet or a synthetic scenario does not count as restaurant validation.
This module refuses to report reviewer agreement unless explicitly approved labels exist.
"""

from __future__ import annotations

import csv
import math
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

from .engine import Dataset, compare_rankers, dish_options

REVIEW_COLUMNS = (
    "case_id", "reviewer_id", "reviewer_role", "reviewed_on", "evidence_reference",
    "approval_status", "dish_id", "budget_ngn", "protein_target_g",
    "max_prep_minutes", "preference", "avoid_allergens", "reviewer_preferred_option_id",
)


@dataclass(frozen=True)
class BenchmarkSummary:
    reviewed_cases: int
    cheapest_feasible_agreements: int
    keyword_agreements: int
    tfidf_agreements: int
    abstention_cases: int
    dataset_kind: str

    def to_dict(self) -> dict:
        return asdict(self)


def read_review_cases(path: str | Path) -> list[dict[str, str]]:
    """Read only approved, attributable assessments with explicit scenario labels."""
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError("Invalid reviewer CSV headers")
        if not set(REVIEW_COLUMNS).issubset(reader.fieldnames):
            raise ValueError("Missing reviewer CSV columns: " + ", ".join(sorted(set(REVIEW_COLUMNS) - set(reader.fieldnames))))
        rows = list(reader)
    if not rows:
        raise ValueError("No independently reviewed cases recorded; benchmark cannot be claimed")
    seen: set[str] = set()
    for row in rows:
        case = row.get("case_id", "").strip()
        if not case or case in seen or None in row or any(value is None for value in row.values()):
            raise ValueError("Missing, duplicate or malformed reviewer case")
        seen.add(case)
        if row["approval_status"].strip().lower() != "approved":
            raise ValueError(f"{case}: a reviewer must approve the case before benchmarking")
        if any(not row[field].strip() for field in (
            "reviewer_id", "reviewer_role", "reviewed_on", "evidence_reference",
            "dish_id", "reviewer_preferred_option_id",
        )):
            raise ValueError(f"{case}: reviewer identity, context, evidence and choice are required")
        try:
            date.fromisoformat(row["reviewed_on"].strip())
        except ValueError as exc:
            raise ValueError(f"{case}: reviewed_on must be YYYY-MM-DD") from exc
    return rows


def _number(row: dict[str, str], field: str, case: str, *, positive: bool = False) -> float:
    try:
        number = float(row[field])
    except (KeyError, ValueError, TypeError) as exc:
        raise ValueError(f"{case}: {field} must be numeric") from exc
    if not math.isfinite(number) or (number <= 0 if positive else number < 0):
        raise ValueError(f"{case}: {field} is invalid")
    return number


def benchmark_reviews(
    data: Dataset, cases: list[dict[str, str]], *, allow_synthetic_fixture: bool = False,
) -> BenchmarkSummary:
    """Compare methods against human labels; never tune or claim uplift from unreviewed rows."""
    if data.demo and not allow_synthetic_fixture:
        raise ValueError("Independent restaurant benchmark requires a verified, non-synthetic dataset")
    if not cases:
        raise ValueError("No independently reviewed cases recorded; benchmark cannot be claimed")
    matches = {"cheapest_feasible_plant": 0, "keyword_hybrid": 0, "tfidf_hybrid": 0}
    abstentions = 0
    for row in cases:
        case = row["case_id"].strip()
        if row["approval_status"].strip().lower() != "approved":
            raise ValueError(f"{case}: unapproved reviewer label")
        known = {option["option_id"]: option for option in dish_options(data, row["dish_id"])}
        selected = row["reviewer_preferred_option_id"].strip()
        if selected != "NONE" and (selected not in known or known[selected]["group"] != "plant"):
            raise ValueError(f"{case}: reviewer choice must be a plant option in the selected dish or NONE")
        report = compare_rankers(
            data, row["dish_id"],
            budget_ngn=_number(row, "budget_ngn", case, positive=True),
            protein_target_g=_number(row, "protein_target_g", case),
            max_prep_minutes=_number(row, "max_prep_minutes", case, positive=True),
            preference=row["preference"].strip(),
            avoid_allergens=[
                item.strip().lower() for item in row["avoid_allergens"].split(";") if item.strip()
            ],
        )
        if selected == "NONE":
            if not report["abstained"]:
                raise ValueError(f"{case}: reviewer marked NONE but the model has eligible options; reconcile constraints")
            abstentions += 1
            expected = None
        else:
            if report["abstained"]:
                raise ValueError(f"{case}: reviewer selected an option despite no feasible candidate")
            expected = selected
        for field in matches:
            matches[field] += int(report[field] == expected)
    return BenchmarkSummary(
        reviewed_cases=len(cases),
        cheapest_feasible_agreements=matches["cheapest_feasible_plant"],
        keyword_agreements=matches["keyword_hybrid"],
        tfidf_agreements=matches["tfidf_hybrid"],
        abstention_cases=abstentions,
        dataset_kind="SYNTHETIC TEST FIXTURE" if data.demo else "HUMAN REVIEWED (NOT SCIENTIFIC VALIDATION)",
    )
