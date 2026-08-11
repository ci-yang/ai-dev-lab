#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
if [[ -n "${PYTHON_BIN:-}" ]]; then
  python_bin="$PYTHON_BIN"
elif [[ -x "$root/.venv/bin/python" ]]; then
  python_bin="$root/.venv/bin/python"
else
  python_bin="python3"
fi
export PYTHONPATH="$root/src${PYTHONPATH:+:$PYTHONPATH}"

action="${1:-}"
[[ -n "$action" ]] && shift

case "$action" in
  task-board)
    exec "$python_bin" -m task_board "$@"
    ;;
  verify)
    exec "$root/scripts/verify.sh" "$@"
    ;;
  loop)
    exec "$root/scripts/bounded-loop.sh" "$@"
    ;;
  git-status)
    if (($# != 0)); then
      echo "guard rejected: git-status accepts no extra arguments" >&2
      exit 2
    fi
    exec git status --short -- .
    ;;
  *)
    echo "guard rejected: allowed actions are task-board, verify, loop, git-status" >&2
    exit 2
    ;;
esac
