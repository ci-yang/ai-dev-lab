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

command="${1:-status}"
case "$command" in
  run|demo-repeated-failure|reset|status)
    exec "$python_bin" -m task_board.loop --root "$root" "$command"
    ;;
  *)
    echo "usage: $0 {run|demo-repeated-failure|reset|status}" >&2
    exit 2
    ;;
esac
