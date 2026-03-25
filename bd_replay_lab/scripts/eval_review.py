#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from common import approx_tokens, build_payload, dump_json, iter_case_files, load_candidate, load_json, run_predictor, validate_review_case
from score import aggregate_review, review_case_metrics


def evaluate_review_dataset(cases_dir: Path, candidate_path: Path, predictor_command: str) -> dict[str, Any]:
    candidate = load_candidate(candidate_path)
    if candidate["lane"] != "review":
        raise ValueError(f"{candidate_path} is not a review candidate")

    rows: list[dict[str, Any]] = []
    prompt_tokens = approx_tokens(candidate["prompt_text"])
    for case_path in iter_case_files(cases_dir):
        case = load_json(case_path)
        validate_review_case(case, case_path)
        payload = build_payload("review", candidate, case)
        prediction = run_predictor(predictor_command, payload)
        row = review_case_metrics(case, prediction, prompt_tokens)
        row["case_path"] = str(case_path)
        rows.append(row)

    return {
        "lane": "review",
        "candidate_id": candidate["candidate_id"],
        "candidate_path": str(candidate_path.resolve()),
        "summary": aggregate_review(rows),
        "cases": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a review candidate against review replay cases")
    parser.add_argument("--cases", required=True, help="Directory containing review case JSON files")
    parser.add_argument("--candidate", required=True, help="Candidate manifest JSON file")
    parser.add_argument("--predictor-command", required=True, help="Command that reads JSON from stdin and returns JSON")
    parser.add_argument("--output", default=None, help="Optional output JSON path")
    args = parser.parse_args()

    result = evaluate_review_dataset(Path(args.cases), Path(args.candidate), args.predictor_command)
    if args.output:
        dump_json(Path(args.output), result)
    else:
        dump_json(Path("/dev/stdout"), result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
