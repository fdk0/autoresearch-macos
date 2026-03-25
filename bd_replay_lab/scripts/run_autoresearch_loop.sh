#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ONE_CYCLE="$REPO_ROOT/bd_replay_lab/scripts/run_one_cycle_exec.sh"
SLEEP_SECONDS="${BD_REPLAY_LOOP_SLEEP_SECONDS:-2}"

while true; do
  "$ONE_CYCLE"
  sleep "$SLEEP_SECONDS"
done
