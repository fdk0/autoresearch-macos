#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from polytick_context import DEFAULT_CONFIG, DEFAULT_OUTPUT, load_config


REPO_ROOT = Path(__file__).resolve().parents[2]
LAB_ROOT = REPO_ROOT / "bd_replay_lab"
DEFAULT_RUNBOOK = LAB_ROOT / "out" / "polytick_runbook.md"


def ensure_dirs() -> None:
    for path in [
        LAB_ROOT / "out",
        LAB_ROOT / "datasets" / "review_cases" / "drafts",
        LAB_ROOT / "datasets" / "review_cases" / "gold",
        LAB_ROOT / "datasets" / "dispatcher_cases" / "drafts",
        LAB_ROOT / "datasets" / "dispatcher_cases" / "gold",
    ]:
        path.mkdir(parents=True, exist_ok=True)


def render_runbook(config: dict[str, str]) -> str:
    source_repo = config["source_repo"]
    source_beads = config["source_beads"]
    analysis_repo = config["analysis_repo"]
    return f"""# PolyTick BD replay lab runbook

This runbook is generated for the current local environment.

## Source paths

- Live source repo: `{source_repo}`
- Live source beads: `{source_beads}`
- Sanitized analysis repo: `{analysis_repo}`
- Replay lab repo: `{REPO_ROOT}`

## 1. Validate context

```bash
python3 bd_replay_lab/scripts/polytick_context.py
```

## 2. Extract draft review cases

```bash
python3 bd_replay_lab/scripts/extract_cases_from_bd.py \\
  --lane review \\
  --id <BD-ID> \\
  --beads-dir {source_beads} \\
  --repo-root {analysis_repo} \\
  --outdir bd_replay_lab/datasets/review_cases/drafts
```

## 3. Extract draft dispatcher cases

```bash
python3 bd_replay_lab/scripts/extract_cases_from_bd.py \\
  --lane dispatcher \\
  --id <BD-ID> \\
  --beads-dir {source_beads} \\
  --repo-root {analysis_repo} \\
  --outdir bd_replay_lab/datasets/dispatcher_cases/drafts
```

## 4. Curate compact gold cases

Move selected draft files into:

- `bd_replay_lab/datasets/review_cases/gold/`
- `bd_replay_lab/datasets/dispatcher_cases/gold/`

Replace `metadata.raw_source` with compact packets once labeling is complete.

## 5. Run baseline review eval

```bash
python3 bd_replay_lab/scripts/eval_review.py \\
  --cases bd_replay_lab/datasets/review_cases/gold \\
  --candidate bd_replay_lab/candidates/review/review_baseline.json \\
  --predictor-command "python3 bd_replay_lab/predictors/review_baseline.py"
```

## 6. Run baseline dispatcher eval

```bash
python3 bd_replay_lab/scripts/eval_dispatcher.py \\
  --cases bd_replay_lab/datasets/dispatcher_cases/gold \\
  --candidate bd_replay_lab/candidates/dispatcher/dispatcher_baseline.json \\
  --predictor-command "python3 bd_replay_lab/predictors/dispatcher_baseline.py"
```

## 7. Start the autoresearch loop

Focus on review first:

1. edit only `bd_replay_lab/prompts/review/*.md` and candidate manifests
2. evaluate
3. keep only score-improving, invariant-safe changes
4. commit winners, revert losers
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare local directories and exact runbook for PolyTick replay work")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="JSON config path")
    parser.add_argument("--context-json", default=str(DEFAULT_OUTPUT), help="Path to polytick context JSON")
    parser.add_argument("--runbook", default=str(DEFAULT_RUNBOOK), help="Path to write runbook markdown")
    args = parser.parse_args()

    ensure_dirs()
    config = load_config(Path(args.config))
    runbook = render_runbook(config)
    runbook_path = Path(args.runbook)
    runbook_path.parent.mkdir(parents=True, exist_ok=True)
    runbook_path.write_text(runbook, encoding="utf-8")

    payload = {
        "config_path": str(Path(args.config).resolve()),
        "context_json": str(Path(args.context_json).resolve()),
        "runbook": str(runbook_path.resolve()),
        "prepared_dirs": [
            "bd_replay_lab/out",
            "bd_replay_lab/datasets/review_cases/drafts",
            "bd_replay_lab/datasets/review_cases/gold",
            "bd_replay_lab/datasets/dispatcher_cases/drafts",
            "bd_replay_lab/datasets/dispatcher_cases/gold",
        ],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
