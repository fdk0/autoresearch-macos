#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import load_state, path_is_in_repo


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

    branch = state.get("branch", "")
    context = (
        "AUTORESEARCH_GUARD v1\n"
        f"State: armed\n"
        f"Branch: {branch or '<unknown>'}\n"
        "Policy:\n"
        "- Do not end the turn just because one experiment finished.\n"
        "- Continue the experiment loop until the operator explicitly disarms the guard.\n"
        "- If the operator asks to pause or stop, first run `python3 scripts/codex_hooks/autoresearch_guard.py disarm`, then end the turn.\n"
    )
    print(
        json.dumps(
            {
                "continue": True,
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": context,
                },
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
