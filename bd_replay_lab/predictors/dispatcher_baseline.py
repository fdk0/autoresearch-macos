#!/usr/bin/env python3
from __future__ import annotations

import json
import sys


def main() -> int:
    payload = json.loads(sys.stdin.read() or "{}")
    case = payload.get("case", {})
    packet = case.get("input", {})

    latest_review_truth = packet.get("latest_review_truth", {})
    pr_state = packet.get("pr_state", {})
    freshness_state = packet.get("freshness_state", {})
    queue_snapshot = packet.get("queue_snapshot", {})
    latest_worker_truth = packet.get("latest_worker_truth", {})

    if latest_review_truth.get("remediation_pending") and pr_state.get("same_pr_open"):
        result = {"next_action": "reuse_review", "reason_tags": ["same_pr_remediation", "continuity_preserved"]}
    elif freshness_state.get("requires_rebase"):
        result = {"next_action": "reconcile", "reason_tags": ["freshness_block"]}
    elif latest_worker_truth.get("terminal_status") == "done" and pr_state.get("review_requested"):
        result = {"next_action": "send_to_review", "reason_tags": ["review_ready"]}
    elif queue_snapshot.get("runnable_count", 0) > 0:
        result = {"next_action": "spawn_worker", "reason_tags": ["fresh_base", "runnable_work"]}
    else:
        result = {"next_action": "idle", "reason_tags": ["queue_idle"]}

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
