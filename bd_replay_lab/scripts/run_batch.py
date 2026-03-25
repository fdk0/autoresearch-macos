#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from common import dump_json
from eval_dispatcher import evaluate_dispatcher_dataset
from eval_review import evaluate_review_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate every candidate manifest in a directory and rank results")
    parser.add_argument("--lane", required=True, choices=["review", "dispatcher"])
    parser.add_argument("--cases", required=True, help="Case directory")
    parser.add_argument("--candidates-dir", required=True, help="Directory containing candidate manifest JSON files")
    parser.add_argument("--predictor-command", required=True, help="Predictor command")
    parser.add_argument("--output", default=None, help="Optional output JSON path")
    args = parser.parse_args()

    cases_dir = Path(args.cases)
    candidates_dir = Path(args.candidates_dir)
    candidate_paths = sorted(candidates_dir.glob("*.json"))
    if not candidate_paths:
        raise SystemExit(f"no candidate manifests found in {candidates_dir}")

    results = []
    for candidate_path in candidate_paths:
        if args.lane == "review":
            result = evaluate_review_dataset(cases_dir, candidate_path, args.predictor_command)
        else:
            result = evaluate_dispatcher_dataset(cases_dir, candidate_path, args.predictor_command)
        results.append(result)

    ranking = sorted(
        (
            {
                "candidate_id": result["candidate_id"],
                "candidate_path": result["candidate_path"],
                "summary": result["summary"],
            }
            for result in results
        ),
        key=lambda row: row["summary"]["score"],
        reverse=True,
    )

    payload = {
        "lane": args.lane,
        "ranking": ranking,
        "results": results,
    }
    if args.output:
        dump_json(Path(args.output), payload)
    else:
        dump_json(Path("/dev/stdout"), payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
