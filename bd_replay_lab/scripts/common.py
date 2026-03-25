from __future__ import annotations

import json
import math
import shlex
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
LAB_ROOT = REPO_ROOT / "bd_replay_lab"
ALLOWED_LANES = {"review", "dispatcher", "hooks"}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def dump_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def iter_case_files(directory: Path) -> list[Path]:
    return sorted(p for p in directory.rglob("*.json") if p.is_file())


def approx_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


def resolve_path(path_str: str, base_path: Path) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve() if path_str.startswith("bd_replay_lab/") else (base_path.parent / path).resolve()


def load_candidate(candidate_path: Path) -> dict[str, Any]:
    manifest = load_json(candidate_path)
    candidate_id = manifest.get("candidate_id")
    lane = manifest.get("lane")
    prompt_files = manifest.get("prompt_files")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise ValueError(f"{candidate_path} missing candidate_id")
    if lane not in ALLOWED_LANES:
        raise ValueError(f"{candidate_path} has unsupported lane {lane!r}")
    if not isinstance(prompt_files, list) or not prompt_files:
        raise ValueError(f"{candidate_path} missing prompt_files")

    resolved_files: list[Path] = []
    prompt_sections: list[str] = []
    for prompt_file in prompt_files:
        if not isinstance(prompt_file, str) or not prompt_file:
            raise ValueError(f"{candidate_path} has invalid prompt file entry {prompt_file!r}")
        resolved = resolve_path(prompt_file, candidate_path)
        if not resolved.exists():
            raise FileNotFoundError(f"prompt file not found: {resolved}")
        resolved_files.append(resolved)
        prompt_sections.append(f"## {resolved.relative_to(REPO_ROOT)}\n\n{resolved.read_text(encoding='utf-8').strip()}")

    return {
        **manifest,
        "candidate_path": str(candidate_path.resolve()),
        "resolved_prompt_files": [str(p) for p in resolved_files],
        "prompt_text": "\n\n".join(prompt_sections).strip() + "\n",
    }


def validate_review_case(case: dict[str, Any], source_path: Path) -> None:
    required_top = {"case_id", "lane", "packet_version", "input", "expected"}
    missing_top = sorted(required_top - set(case))
    if missing_top:
        raise ValueError(f"{source_path} missing top-level keys: {missing_top}")
    if case["lane"] != "review":
        raise ValueError(f"{source_path} lane must be 'review'")
    required_input = {"pr_meta", "diff_summary", "verify_summary", "worker_status_v2", "scope_dod", "merge_state"}
    missing_input = sorted(required_input - set(case["input"]))
    if missing_input:
        raise ValueError(f"{source_path} missing review input keys: {missing_input}")
    required_expected = {"decision", "findings"}
    missing_expected = sorted(required_expected - set(case["expected"]))
    if missing_expected:
        raise ValueError(f"{source_path} missing review expected keys: {missing_expected}")


def validate_dispatcher_case(case: dict[str, Any], source_path: Path) -> None:
    required_top = {"case_id", "lane", "packet_version", "input", "expected"}
    missing_top = sorted(required_top - set(case))
    if missing_top:
        raise ValueError(f"{source_path} missing top-level keys: {missing_top}")
    if case["lane"] != "dispatcher":
        raise ValueError(f"{source_path} lane must be 'dispatcher'")
    required_input = {"queue_snapshot", "latest_worker_truth", "latest_review_truth", "pr_state", "freshness_state", "dispatchability"}
    missing_input = sorted(required_input - set(case["input"]))
    if missing_input:
        raise ValueError(f"{source_path} missing dispatcher input keys: {missing_input}")
    required_expected = {"next_action"}
    missing_expected = sorted(required_expected - set(case["expected"]))
    if missing_expected:
        raise ValueError(f"{source_path} missing dispatcher expected keys: {missing_expected}")


def run_predictor(predictor_command: str, payload: dict[str, Any], cwd: Path | None = None) -> dict[str, Any]:
    proc = subprocess.run(
        shlex.split(predictor_command),
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=str(cwd or REPO_ROOT),
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"predictor failed with exit code {proc.returncode}: "
            f"{proc.stderr.strip() or proc.stdout.strip() or predictor_command}"
        )
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"predictor returned invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("predictor must return a JSON object")
    return data


def build_payload(lane: str, candidate: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    return {
        "lane": lane,
        "candidate": {
            "candidate_id": candidate["candidate_id"],
            "lane": candidate["lane"],
            "candidate_path": candidate["candidate_path"],
            "resolved_prompt_files": candidate["resolved_prompt_files"],
        },
        "prompt_text": candidate["prompt_text"],
        "case": case,
    }


def severity_rank(value: str) -> int:
    return {"low": 1, "medium": 2, "high": 3}.get(value, 0)


def normalize_findings(findings: Any) -> dict[str, str]:
    normalized: dict[str, str] = {}
    if not isinstance(findings, list):
        return normalized
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        finding_type = finding.get("type")
        severity = finding.get("severity", "low")
        if not isinstance(finding_type, str) or not finding_type:
            continue
        current = normalized.get(finding_type)
        if current is None or severity_rank(str(severity)) > severity_rank(current):
            normalized[finding_type] = str(severity)
    return normalized
