#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import current_branch, load_state, path_is_in_repo


def main() -> int:
    try:
        event = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        event = {}

    state = load_state()
    if not state.get("armed"):
        print(json.dumps({"continue": True}))
        return 0

    if not path_is_in_repo(event.get("cwd")):
        print(json.dumps({"continue": True}))
        return 0

    guarded_branch = str(state.get("branch") or "").strip()
    try:
        branch = current_branch()
    except Exception:
        branch = guarded_branch

    if guarded_branch and branch != guarded_branch:
        print(json.dumps({"continue": True}))
        return 0

    if branch and not branch.startswith("autoresearch/"):
        print(json.dumps({"continue": True}))
        return 0

    reason = (
        "Autoresearch guard is armed for this run. Do not stop after a single experiment. "
        "Continue the loop: inspect git state, modify train.py, commit, run `uv run train.py > run.log 2>&1`, "
        "record results.tsv, keep or revert, and start the next experiment. "
        "If the operator wants to pause or finish, first run `python3 scripts/codex_hooks/autoresearch_guard.py disarm`."
    )
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
