"""Report independently reviewed benchmark metrics. No fake default success.

Usage:
    python scripts/benchmark_reviews.py data/evaluation/reviewer_cases.csv

Do not use a synthetic dataset to claim reviewer agreement.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from menushift.benchmark import benchmark_reviews, read_review_cases
from menushift.engine import load_dataset


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare recommendation rankings to approved human labels")
    parser.add_argument("cases", type=Path)
    args = parser.parse_args()
    data = load_dataset(ROOT / "data" / "verified", demo=False)
    cases = read_review_cases(args.cases)
    print(json.dumps(benchmark_reviews(data, cases).to_dict(), indent=2))


if __name__ == "__main__":
    main()
