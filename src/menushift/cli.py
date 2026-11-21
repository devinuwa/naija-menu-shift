"""CLI for testing calculations without starting Streamlit."""
import argparse
import json
from pathlib import Path

from .engine import baselines, compare_rankers, evaluate, load_dataset, sensitivity

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description="Naija MenuShift (demo data are fictional)")
    parser.add_argument("--data-dir", default=str(ROOT / "data" / "demo"))
    parser.add_argument("--verified", action="store_true", help="Disable synthetic-demo mode")
    parser.add_argument("--dish", default="suya")
    parser.add_argument("--budget", type=float, default=1500)
    parser.add_argument("--protein", type=float, default=10)
    parser.add_argument("--max-prep", type=float, default=180)
    parser.add_argument("--preference", default="chewy grilled")
    parser.add_argument("--sensitivity", action="store_true")
    args = parser.parse_args()
    data = load_dataset(args.data_dir, demo=not args.verified)
    kwargs = {
        "budget_ngn": args.budget,
        "protein_target_g": args.protein,
        "max_prep_minutes": args.max_prep,
        "preference": args.preference,
    }
    result = evaluate(data, args.dish, **kwargs)
    out = {"mode": "DEMO-SYNTHETIC" if data.demo else "VERIFIED-SOURCED",
           "dish": args.dish, "ranked_options": [r.to_dict() for r in result],
           "baseline": baselines(result),
           "ranker_comparison": compare_rankers(data, args.dish, **kwargs)}
    if args.sensitivity:
        out["price_sensitivity"] = {k: [r.to_dict() for r in v]
                                     for k, v in sensitivity(data, args.dish, **kwargs).items()}
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
