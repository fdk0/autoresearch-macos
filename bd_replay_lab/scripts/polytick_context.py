#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
LAB_ROOT = REPO_ROOT / "bd_replay_lab"
DEFAULT_CONFIG = LAB_ROOT / "local" / "polytick.paths.json"
DEFAULT_OUTPUT = LAB_ROOT / "out" / "polytick_context.json"


def load_config(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def run_bd_context(beads_dir: Path, repo_root: Path) -> dict[str, Any]:
    env = os.environ.copy()
    env["BEADS_DIR"] = str(beads_dir)
    proc = subprocess.run(
        ["bd", "--readonly", "context", "--json"],
        cwd=str(repo_root),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "bd context failed")
    return json.loads(proc.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate local PolyTick replay-lab source and analysis paths")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="JSON config path")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Where to write the context summary")
    args = parser.parse_args()

    config_path = Path(args.config)
    config = load_config(config_path)
    source_repo = Path(config["source_repo"]).resolve()
    source_beads = Path(config["source_beads"]).resolve()
    analysis_repo = Path(config["analysis_repo"]).resolve()

    summary = {
        "config_path": str(config_path.resolve()),
        "source_repo": str(source_repo),
        "source_beads": str(source_beads),
        "analysis_repo": str(analysis_repo),
        "checks": {},
    }

    summary["checks"]["source_repo_exists"] = source_repo.is_dir()
    summary["checks"]["source_beads_exists"] = source_beads.is_dir()
    summary["checks"]["analysis_repo_exists"] = analysis_repo.is_dir()
    summary["checks"]["analysis_beads_absent"] = not (analysis_repo / ".beads").exists()
    summary["checks"]["analysis_beads_disabled_present"] = (analysis_repo / ".beads.disabled").exists()

    if not all(summary["checks"].values()):
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 1

    summary["bd_context"] = run_bd_context(source_beads, analysis_repo)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
