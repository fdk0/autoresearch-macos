#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
LAB_ROOT = REPO_ROOT / "bd_replay_lab"
STATE_TEMPLATE = LAB_ROOT / "state" / "loop_state.template.json"
STATE_PATH = LAB_ROOT / "state" / "loop_state.json"
RESULTS_PATH = LAB_ROOT / "results.tsv"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize local autoresearch loop state and results ledger")
    parser.add_argument("--force", action="store_true", help="Rewrite the local state file from template")
    args = parser.parse_args()

    ensure_dir(LAB_ROOT / "state")
    ensure_dir(LAB_ROOT / "logs")
    ensure_dir(LAB_ROOT / "out")
    ensure_dir(LAB_ROOT / "datasets" / "review_cases" / "drafts")
    ensure_dir(LAB_ROOT / "datasets" / "review_cases" / "gold")
    ensure_dir(LAB_ROOT / "datasets" / "dispatcher_cases" / "drafts")
    ensure_dir(LAB_ROOT / "datasets" / "dispatcher_cases" / "gold")

    if args.force or not STATE_PATH.exists():
        STATE_PATH.write_text(STATE_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")

    if args.force or not RESULTS_PATH.exists():
        RESULTS_PATH.write_text(
            "commit\tlane\tcandidate\tscore\tprompt_tokens\tinvariant_violations\tstatus\tdescription\n",
            encoding="utf-8",
        )

    payload = {
        "state_path": str(STATE_PATH),
        "results_path": str(RESULTS_PATH),
        "state_exists": STATE_PATH.exists(),
        "results_exists": RESULTS_PATH.exists(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
