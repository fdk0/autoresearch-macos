#!/usr/bin/env bash
set -euo pipefail

CODEX_BIN="/Users/fdk0/.local/share/codex-binaries/codex-wake-upstream-prep-release"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROFILE="bd-replay-loop"

if [[ "${1:-}" == "--print-command" ]]; then
  shift
  printf '%q ' "$CODEX_BIN" --profile "$PROFILE" -C "$REPO_ROOT" "$@"
  printf '\n'
  exit 0
fi

exec "$CODEX_BIN" --profile "$PROFILE" -C "$REPO_ROOT" "$@"
