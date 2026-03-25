#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import STATE_PATH, current_branch, load_state, save_state, utc_now_iso


def cmd_arm(branch: str | None) -> int:
    branch = branch or current_branch()
    state = {
        "armed": True,
        "branch": branch,
        "armed_at": utc_now_iso(),
    }
    save_state(state)
    print(json.dumps({"status": "armed", "branch": branch, "state_path": str(STATE_PATH)}, indent=2))
    return 0


def cmd_disarm() -> int:
    state = load_state()
    state.update(
        {
            "armed": False,
            "disarmed_at": utc_now_iso(),
        }
    )
    save_state(state)
    print(json.dumps({"status": "disarmed", "branch": state.get("branch", ""), "state_path": str(STATE_PATH)}, indent=2))
    return 0


def cmd_status() -> int:
    state = load_state()
    print(json.dumps({"state_path": str(STATE_PATH), "state": state}, indent=2, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Control the Codex autoresearch stop guard")
    subparsers = parser.add_subparsers(dest="command", required=True)

    arm = subparsers.add_parser("arm", help="Arm the stop guard for the current or specified branch")
    arm.add_argument("--branch", default=None, help="Branch name to bind the guard to")

    subparsers.add_parser("disarm", help="Disarm the stop guard")
    subparsers.add_parser("status", help="Show current guard state")

    args = parser.parse_args()
    if args.command == "arm":
        return cmd_arm(args.branch)
    if args.command == "disarm":
        return cmd_disarm()
    if args.command == "status":
        return cmd_status()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
