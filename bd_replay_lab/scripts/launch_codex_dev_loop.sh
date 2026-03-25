#!/usr/bin/env bash
set -euo pipefail

CODEX_BIN="/Users/fdk0/.local/share/codex-binaries/codex-wake-upstream-prep-release"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROFILE="bd-replay-loop"
BOOTSTRAP_SCRIPT="$REPO_ROOT/bd_replay_lab/scripts/bootstrap_polytick_lab.py"
CONTEXT_SCRIPT="$REPO_ROOT/bd_replay_lab/scripts/polytick_context.py"

DEFAULT_PROMPT=$(cat <<'EOF'
Read these files first:
- bd_replay_lab/codex_loop_prompt.md
- bd_replay_lab/program.md
- bd_replay_lab/out/polytick_runbook.md

Then:
1. validate the PolyTick replay context
2. begin the offline BD replay optimization loop
3. start with review-lane work first
4. if the review gold set is too small, extract real draft cases from PolyTick Beads state in read-only mode
5. curate or improve the review gold set
6. run baseline evaluation
7. propose and test one narrow rubric improvement

Do not touch the live PolyTick repo or its .beads workspace except through explicit bd --readonly reads.
EOF
)

NO_PROMPT=0
PRINT_PROMPT=0
PRINT_COMMAND=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-prompt)
      NO_PROMPT=1
      shift
      ;;
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

if [[ $PRINT_PROMPT -eq 1 ]]; then
  printf '%s\n' "$DEFAULT_PROMPT"
  exit 0
fi

if [[ $PRINT_COMMAND -eq 1 ]]; then
  printf '%q ' "$CODEX_BIN" --profile "$PROFILE" -C "$REPO_ROOT" "$@"
  printf '\n'
  exit 0
fi

python3 "$CONTEXT_SCRIPT" >/dev/null
python3 "$BOOTSTRAP_SCRIPT" >/dev/null

if [[ $NO_PROMPT -eq 1 ]]; then
  exec "$CODEX_BIN" --profile "$PROFILE" -C "$REPO_ROOT" "$@"
fi

if [[ $# -gt 0 ]]; then
  exec "$CODEX_BIN" --profile "$PROFILE" -C "$REPO_ROOT" "$@"
fi

exec "$CODEX_BIN" --profile "$PROFILE" -C "$REPO_ROOT" "$DEFAULT_PROMPT"
