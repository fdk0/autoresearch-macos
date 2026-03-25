#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_bd_json(args: list[str]) -> Any:
    proc = subprocess.run(["bd", *args, "--json"], text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"bd {' '.join(args)} failed")
    return json.loads(proc.stdout)


def flatten_text(value: Any) -> str:
    chunks: list[str] = []
    if isinstance(value, dict):
        for nested in value.values():
            chunks.append(flatten_text(nested))
    elif isinstance(value, list):
        for nested in value:
            chunks.append(flatten_text(nested))
    elif isinstance(value, str):
        chunks.append(value)
    return "\n".join(chunk for chunk in chunks if chunk)


def heuristic_tags(issue: Any, comments: Any) -> dict[str, Any]:
    text = "\n".join(part for part in [flatten_text(issue), flatten_text(comments)] if part)
    return {
        "has_worker_status_v2": bool(re.search(r"\bworker STATUS v2\b", text, re.IGNORECASE)),
        "has_review_status_v2": bool(re.search(r"\breview STATUS v2\b", text, re.IGNORECASE)),
        "mentions_verify": bool(re.search(r"\bVERIFY\b|\bverify\b", text)),
        "mentions_remediation": bool(re.search(r"\bremediation\b", text, re.IGNORECASE)),
        "mentions_pr": bool(re.search(r"\bPR\b|pull request|github.com/.+/pull/", text, re.IGNORECASE)),
    }


def draft_case(lane: str, bead_id: str, issue: Any, comments: Any) -> dict[str, Any]:
    tags = heuristic_tags(issue, comments)
    skeleton_expected = {"decision": "", "findings": []} if lane == "review" else {"next_action": "", "reason_tags": []}
    return {
        "case_id": f"{lane}_{bead_id.lower().replace('-', '_')}",
        "lane": lane,
        "packet_version": f"{lane}_packet_v1",
        "input": {},
        "expected": skeleton_expected,
        "metadata": {
            "source": {
                "bd_id": bead_id,
                "extracted_at": utc_now_iso(),
                "extraction_mode": "bd show/comments --json",
            },
            "heuristics": tags,
            "todo": [
                "fill compact input packet from raw source",
                "set expected decision / next_action",
                "fill expected findings or reason_tags",
                "remove raw source once packet is finalized if desired"
            ],
            "raw_source": {
                "issue": issue,
                "comments": comments,
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract draft replay cases directly from local Beads state")
    parser.add_argument("--lane", required=True, choices=["review", "dispatcher"])
    parser.add_argument("--id", dest="ids", action="append", required=True, help="Bead ID to extract; repeat for multiple")
    parser.add_argument("--outdir", required=True, help="Output directory for draft case JSON files")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    for bead_id in args.ids:
        issue = run_bd_json(["show", "--long", bead_id])
        comments = run_bd_json(["comments", bead_id])
        payload = draft_case(args.lane, bead_id, issue, comments)
        out_path = outdir / f"{payload['case_id']}.json"
        out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(out_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
