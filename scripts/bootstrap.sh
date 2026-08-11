#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

python_bin="${PYTHON_BIN:-python3}"
venv_dir="${VENV_DIR:-.venv}"
constraints_file="${CONSTRAINTS_FILE:-constraints/runtime-profile.txt}"
if [[ "$constraints_file" != /* ]]; then
  constraints_file="$root/$constraints_file"
fi
if [[ ! -r "$constraints_file" ]]; then
  echo "environment error: dependency profile is not readable" >&2
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

"$python_bin" -m venv "$venv_dir"

venv_python="$venv_dir/bin/python"
if [[ ! -x "$venv_python" ]]; then
  echo "environment error: expected $venv_python" >&2
  exit 2
fi

export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_CONSTRAINT="$constraints_file"
"$venv_python" -m pip install \
  --upgrade \
  --constraint "$constraints_file" \
  "pip==26.1.2" \
  "setuptools==83.0.0" \
  "wheel==0.47.0"

if ! "$venv_python" -m pip install \
  --constraint "$constraints_file" \
  --no-build-isolation \
  -e '.[dev]'
then
  echo "editable install unavailable; trying a non-editable install" >&2
  "$venv_python" -m pip install \
    --constraint "$constraints_file" \
    --no-build-isolation \
    '.[dev]'
fi

profile_display="$(basename "$constraints_file")"
echo "bootstrap complete: $venv_python (profile: $profile_display)"
