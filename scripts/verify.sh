#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

mode="${1:-fast}"
case "$mode" in
  fast|full) ;;
  *)
    echo "usage: $0 {fast|full}" >&2
    exit 2
    ;;
esac

if [[ -n "${PYTHON_BIN:-}" ]]; then
  python_bin="$PYTHON_BIN"
elif [[ -x "$root/.venv/bin/python" ]]; then
  python_bin="$root/.venv/bin/python"
else
  python_bin="python3"
fi
export PYTHONPATH="$root/src${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONPYCACHEPREFIX="$root/runtime/pycache"

if ! "$python_bin" -c 'import sys' >/dev/null 2>&1; then
  echo "environment error: Python cannot run: $python_bin" >&2
  exit 2
fi
if ! "$python_bin" - <<'PY'
import sys

raise SystemExit(0 if sys.version_info >= (3, 12) else 1)
PY
then
  echo "environment error: ai-dev-lab requires Python 3.12+" >&2
  exit 2
fi

require_module() {
  local module="$1"
  if ! "$python_bin" - "$module" <<'PY'
import importlib.util
import sys

raise SystemExit(0 if importlib.util.find_spec(sys.argv[1]) else 1)
PY
  then
    echo "environment error: install the dev dependencies; missing $module" >&2
    exit 2
  fi
}

bash -n scripts/*.sh
"$python_bin" -m compileall -q -f src tests
require_module pytest

if [[ "$mode" == "fast" ]]; then
  "$python_bin" -m pytest -q
  exit 0
fi

for module in ruff black isort coverage pytest_cov; do
  require_module "$module"
done

"$python_bin" -m ruff check .
"$python_bin" -m black --check src tests
"$python_bin" -m isort --check-only src tests
"$python_bin" -m pytest \
  --cov=task_board \
  --cov-report=term-missing \
  --cov-fail-under=80
