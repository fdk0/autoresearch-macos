#!/usr/bin/env bash
set -euo pipefail

CODEX_BIN="/Users/fdk0/.local/share/codex-binaries/codex-wake-upstream-prep-release"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROFILE="bd-replay-autoresearch"
CONTEXT_SCRIPT="$REPO_ROOT/bd_replay_lab/scripts/polytick_context.py"
BOOTSTRAP_SCRIPT="$REPO_ROOT/bd_replay_lab/scripts/bootstrap_polytick_lab.py"
INIT_SCRIPT="$REPO_ROOT/bd_replay_lab/scripts/init_autoresearch_loop.py"
STATE_FILE="$REPO_ROOT/bd_replay_lab/state/loop_state.json"
RESULTS_FILE="$REPO_ROOT/bd_replay_lab/results.tsv"
LAST_MESSAGE="$REPO_ROOT/bd_replay_lab/out/last_exec_message.txt"
LAST_SUMMARY="$REPO_ROOT/bd_replay_lab/out/last_cycle_summary.md"

PRINT_PROMPT=0
PRINT_COMMAND=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --print-prompt)
      PRINT_PROMPT=1
      shift
      ;;
    --print-command)
      PRINT_COMMAND=1
      shift
      ;;
    --)
      shift
      break
      ;;
    *)
      break
      ;;
  esac
done

PROMPT=$(cat <<'EOF'
Read these files first:
- bd_replay_lab/autoresearch_program.md
- bd_replay_lab/codex_loop_prompt.md
- bd_replay_lab/program.md
- bd_replay_lab/state/loop_state.json
- bd_replay_lab/results.tsv
- bd_replay_lab/out/polytick_runbook.md

Run exactly one autoresearch cycle for the BD replay lab.

Cycle contract:
1. inspect the current loop state and ledger
2. choose the smallest valid next step
3. perform exactly one cycle of real progress
4. update bd_replay_lab/state/loop_state.json
5. append exactly one row to bd_replay_lab/results.tsv
6. write a concise summary to bd_replay_lab/out/last_cycle_summary.md
7. if the cycle produced a real improvement, keep it and commit it
8. if not, revert the experiment before exiting
9. exit after the single cycle is complete

Allowed cycle types:
- extract one real draft case from PolyTick in read-only mode
- improve one gold-set case
- run baseline and record incumbent
- mutate one review/dispatcher prompt or candidate and evaluate it

Priorities:
- review lane first
- real PolyTick Beads data, not synthetic-only progress
- no writes to the live PolyTick repo or live .beads

Use bd --readonly for all source BD reads.
EOF
)

if [[ $PRINT_PROMPT -eq 1 ]]; then
  printf '%s\n' "$PROMPT"
  exit 0
fi

python3 "$CONTEXT_SCRIPT" >/dev/null
python3 "$BOOTSTRAP_SCRIPT" >/dev/null
python3 "$INIT_SCRIPT" >/dev/null

BEFORE_RESULTS_LINES="$(wc -l < "$RESULTS_FILE")"
BEFORE_STATE_HASH="$(shasum -a 256 "$STATE_FILE" | awk '{print $1}')"

if [[ $PRINT_COMMAND -eq 1 ]]; then
  printf '%q ' "$CODEX_BIN" exec --profile "$PROFILE" -C "$REPO_ROOT" -o "$LAST_MESSAGE" -
  printf '\n'
  exit 0
fi

printf '%s\n' "$PROMPT" | "$CODEX_BIN" exec --profile "$PROFILE" -C "$REPO_ROOT" -o "$LAST_MESSAGE" -

AFTER_RESULTS_LINES="$(wc -l < "$RESULTS_FILE")"
AFTER_STATE_HASH="$(shasum -a 256 "$STATE_FILE" | awk '{print $1}')"

if [[ ! -s "$LAST_SUMMARY" ]]; then
  echo "autoresearch cycle failed contract: $LAST_SUMMARY missing or empty" >&2
  exit 1
fi

if (( AFTER_RESULTS_LINES <= BEFORE_RESULTS_LINES )); then
  echo "autoresearch cycle failed contract: $RESULTS_FILE was not appended" >&2
  exit 1
fi

if [[ "$AFTER_STATE_HASH" == "$BEFORE_STATE_HASH" ]]; then
  echo "autoresearch cycle failed contract: $STATE_FILE was not updated" >&2
  exit 1
fi
