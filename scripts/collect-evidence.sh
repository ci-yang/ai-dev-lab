#!/usr/bin/env bash
set -uo pipefail

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

profile_file="${CONSTRAINTS_FILE:-constraints/runtime-profile.txt}"
if [[ "$profile_file" != /* ]]; then
  profile_file="$root/$profile_file"
fi
if [[ ! -r "$profile_file" ]]; then
  echo "environment error: dependency profile is not readable" >&2
  exit 2
fi

run_id="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)-$$}"
if [[ ! "$run_id" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "environment error: RUN_ID contains unsupported characters" >&2
  exit 2
fi

dir="evidence/runs/$run_id"
if ! mkdir -p evidence/runs || ! mkdir "$dir"; then
  echo "environment error: evidence run already exists or cannot be created" >&2
  exit 2
fi

started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
code=0
exclude=':(exclude)evidence/runs/**'

git rev-parse HEAD >"$dir/repo-commit.txt" 2>"$dir/git-error.txt" || code=2
commit="$(tr -d '\n' <"$dir/repo-commit.txt")"
git status --short --untracked-files=all -- . "$exclude" \
  >"$dir/status.txt" 2>>"$dir/git-error.txt" || code=2
git diff --binary HEAD -- . "$exclude" \
  >"$dir/change.diff" 2>>"$dir/git-error.txt" || code=2
git ls-files --others --exclude-standard -- . "$exclude" \
  >"$dir/untracked-paths.txt" 2>>"$dir/git-error.txt" || code=2
[[ -s "$dir/status.txt" ]] && code=2
[[ -s "$dir/change.diff" ]] && code=2
[[ -s "$dir/untracked-paths.txt" ]] && code=2

if ((code == 0)); then
  "$root/scripts/verify.sh" "$mode" >"$dir/verifier.out" 2>&1 || {
    raw=$?
    if ((raw == 1)); then
      code=1
    else
      code=2
    fi
  }
else
  echo "verification not run: Git baseline is incomplete" >"$dir/verifier.out"
fi

printf '%s\n' "$code" >"$dir/exit-code.txt"
ended_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
if [[ -n "${PYTHON_BIN:-}" ]]; then
  python_bin="$PYTHON_BIN"
elif [[ -x "$root/.venv/bin/python" ]]; then
  python_bin="$root/.venv/bin/python"
else
  python_bin="python3"
fi
if ! "$python_bin" scripts/write_evidence_manifest.py \
  --output "$dir/manifest.json" \
  --profile "$profile_file" \
  --commit "$commit" \
  --run-id "$run_id" \
  --mode "$mode" \
  --started-at "$started_at" \
  --ended-at "$ended_at" \
  --exit-code "$code"
then
  code=2
  printf '%s\n' "$code" >"$dir/exit-code.txt"
  echo "environment error: could not write Evidence manifest" >&2
fi

echo "evidence: $dir (exit $code)"
exit "$code"
