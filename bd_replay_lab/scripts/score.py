from __future__ import annotations

from typing import Any

from common import normalize_findings


ALLOWED_REVIEW_DECISIONS = {"approve", "request_changes", "block_merge"}
ALLOWED_DISPATCHER_ACTIONS = {"reuse_worker", "reuse_review", "spawn_worker", "send_to_review", "reconcile", "idle"}


def review_case_metrics(case: dict[str, Any], prediction: dict[str, Any], prompt_tokens: int) -> dict[str, Any]:
    expected = case["expected"]
    expected_findings = normalize_findings(expected.get("findings", []))
    predicted_findings = normalize_findings(prediction.get("findings", []))

    expected_types = set(expected_findings)
    predicted_types = set(predicted_findings)
    tp = len(expected_types & predicted_types)
    fp = len(predicted_types - expected_types)
    fn = len(expected_types - predicted_types)

    precision = 1.0 if not predicted_types and not expected_types else (tp / len(predicted_types) if predicted_types else 0.0)
    recall = 1.0 if not expected_types and not predicted_types else (tp / len(expected_types) if expected_types else 0.0)

    matched_types = expected_types & predicted_types
    if matched_types:
        severity_alignment = sum(
            1 for finding_type in matched_types if expected_findings[finding_type] == predicted_findings.get(finding_type)
        ) / len(matched_types)
    else:
        severity_alignment = 1.0 if not expected_types and not predicted_types else 0.0

    invalid_decision = prediction.get("decision") not in ALLOWED_REVIEW_DECISIONS
    high_severity_miss = any(
        severity == "high" and finding_type not in predicted_types for finding_type, severity in expected_findings.items()
    )

    return {
        "case_id": case["case_id"],
        "decision_correct": prediction.get("decision") == expected.get("decision"),
        "precision": precision,
        "recall": recall,
        "severity_alignment": severity_alignment,
        "high_severity_miss": high_severity_miss,
        "invariant_violation": invalid_decision,
        "prompt_tokens": prompt_tokens,
        "prediction": prediction,
    }


def dispatcher_case_metrics(case: dict[str, Any], prediction: dict[str, Any], prompt_tokens: int) -> dict[str, Any]:
    expected = case["expected"]
    predicted_action = prediction.get("next_action")
    expected_tags = set(expected.get("reason_tags", []))
    predicted_tags = set(prediction.get("reason_tags", [])) if isinstance(prediction.get("reason_tags"), list) else set()

    tag_overlap = 1.0
    if expected_tags:
        tag_overlap = len(expected_tags & predicted_tags) / len(expected_tags)

    invalid_action = predicted_action not in ALLOWED_DISPATCHER_ACTIONS
    continuity_expected = expected.get("next_action") in {"reuse_worker", "reuse_review"}
    continuity_correct = (predicted_action in {"reuse_worker", "reuse_review"}) == continuity_expected

    freshness_expected = expected.get("next_action") != "spawn_worker" or not case["input"]["freshness_state"].get("requires_rebase", False)
    freshness_correct = not (
        case["input"]["freshness_state"].get("requires_rebase", False) and predicted_action == "spawn_worker"
    )

    return {
        "case_id": case["case_id"],
        "next_action_correct": predicted_action == expected.get("next_action"),
        "continuity_correct": continuity_correct,
        "freshness_correct": freshness_correct and freshness_expected,
        "reason_tag_overlap": tag_overlap,
        "invariant_violation": invalid_action,
        "prompt_tokens": prompt_tokens,
        "prediction": prediction,
    }


def _mean(rows: list[dict[str, Any]], key: str) -> float:
    if not rows:
        return 0.0
    return sum(float(row[key]) for row in rows) / len(rows)


def aggregate_review(rows: list[dict[str, Any]]) -> dict[str, Any]:
    avg_prompt_tokens = _mean(rows, "prompt_tokens")
    summary = {
        "num_cases": len(rows),
        "decision_accuracy": _mean(rows, "decision_correct"),
        "finding_precision": _mean(rows, "precision"),
        "finding_recall": _mean(rows, "recall"),
        "severity_alignment": _mean(rows, "severity_alignment"),
        "high_severity_miss_rate": _mean(rows, "high_severity_miss"),
        "invariant_violation_rate": _mean(rows, "invariant_violation"),
        "avg_prompt_tokens": avg_prompt_tokens,
    }
    summary["score"] = (
        0.30 * summary["decision_accuracy"]
        + 0.30 * summary["finding_recall"]
        + 0.15 * summary["finding_precision"]
        + 0.15 * summary["severity_alignment"]
        - 0.10 * summary["high_severity_miss_rate"]
        - 1.00 * summary["invariant_violation_rate"]
        - 0.0005 * avg_prompt_tokens
    )
    return summary


def aggregate_dispatcher(rows: list[dict[str, Any]]) -> dict[str, Any]:
    avg_prompt_tokens = _mean(rows, "prompt_tokens")
    summary = {
        "num_cases": len(rows),
        "next_action_accuracy": _mean(rows, "next_action_correct"),
        "continuity_accuracy": _mean(rows, "continuity_correct"),
        "freshness_accuracy": _mean(rows, "freshness_correct"),
        "reason_tag_overlap": _mean(rows, "reason_tag_overlap"),
        "invariant_violation_rate": _mean(rows, "invariant_violation"),
        "avg_prompt_tokens": avg_prompt_tokens,
    }
    summary["score"] = (
        0.45 * summary["next_action_accuracy"]
        + 0.20 * summary["continuity_accuracy"]
        + 0.20 * summary["freshness_accuracy"]
        + 0.15 * summary["reason_tag_overlap"]
        - 1.00 * summary["invariant_violation_rate"]
        - 0.0005 * avg_prompt_tokens
    )
    return summary
