#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from typing import Any


def main() -> int:
    payload = json.loads(sys.stdin.read() or "{}")
    case = payload.get("case", {})
    packet = case.get("input", {})

    findings: list[dict[str, Any]] = []
    verify = packet.get("verify_summary", {})
    worker = packet.get("worker_status_v2", {})
    scope_dod = packet.get("scope_dod", {})
    merge_state = packet.get("merge_state", {})

    if verify.get("missing_required_evidence") or not verify.get("required_commands_passed", False):
        findings.append({"type": "missing_verify_evidence", "severity": "high"})
    if not worker.get("present", False):
        findings.append({"type": "missing_worker_status_v2", "severity": "high"})
    if scope_dod.get("out_of_scope_files"):
        findings.append({"type": "out_of_scope_change", "severity": "high"})
    if merge_state.get("block_reason") == "stale_base":
        findings.append({"type": "stale_base", "severity": "medium"})

    decision = "approve" if not findings else "request_changes"
    print(json.dumps({"decision": decision, "findings": findings, "notes": "deterministic baseline"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
