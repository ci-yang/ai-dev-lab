import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

ROOT = Path(__file__).resolve().parents[1]
BOOK_PROFILE = {
    "black": "26.5.1",
    "click": "8.4.2",
    "coverage": "7.15.2",
    "iniconfig": "2.3.0",
    "isort": "8.0.1",
    "mypy_extensions": "1.1.0",
    "packaging": "26.2",
    "pathspec": "1.1.1",
    "pip": "26.1.2",
    "platformdirs": "4.11.0",
    "pluggy": "1.6.0",
    "Pygments": "2.20.0",
    "pytest": "9.1.1",
    "pytest-cov": "7.1.0",
    "pytokens": "0.4.1",
    "ruff": "0.15.22",
    "setuptools": "83.0.0",
    "wheel": "0.47.0",
}
JSON_COMPATIBLE_YAML = (
    ROOT / "tasks" / "delegations" / "task-board-validation.yaml",
    ROOT / "tasks" / "queue.yaml",
    ROOT / "policies" / "agent-authority.yaml",
    ROOT / ".ai-loop" / "loop-contract.yaml",
    ROOT / ".ai-loop" / "state.yaml",
)


@pytest.mark.parametrize("path", JSON_COMPATIBLE_YAML)
def test_yaml_artifact_is_valid_json_subset(path: Path) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))

    assert isinstance(value, dict)


def test_delegation_checker_cannot_write_tracked_or_durable_artifacts() -> None:
    raw: Dict[str, Any] = json.loads(
        (ROOT / "tasks" / "delegations" / "task-board-validation.yaml").read_text(
            encoding="utf-8"
        )
    )
    delegation = raw["delegation"]

    scope = delegation["scope"]
    ignore_patterns = {
        line.strip()
        for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#") and not line.startswith("!")
    }

    assert scope["writable_paths"] == []
    assert scope["tracked_artifact_writes"] == "deny"
    assert scope["verifier_ephemeral_writes"]["owner"] == "scripts/verify.sh"
    assert set(scope["verifier_ephemeral_writes"]["paths"]) <= ignore_patterns
    assert delegation["responsibility"]["human_owner"] == "lab-operator"
    assert delegation["termination"]["escalate"]


def test_loop_contract_is_bounded_and_local() -> None:
    raw: Dict[str, Any] = json.loads(
        (ROOT / ".ai-loop" / "loop-contract.yaml").read_text(encoding="utf-8")
    )
    loop = raw["loop"]

    assert loop["max_rounds"] == 3
    assert loop["same_failure_limit"] == 2
    assert "network" in loop["authority"]["prohibited_actions"]
    assert "deploy" in loop["authority"]["prohibited_actions"]


def test_authority_separates_maker_and_checker() -> None:
    raw: Dict[str, Any] = json.loads(
        (ROOT / "policies" / "agent-authority.yaml").read_text(encoding="utf-8")
    )

    assert raw["roles"]["maker"]["writable_paths"]
    assert "evidence/" in raw["roles"]["maker"]["readable_paths"]
    assert "scripts/guard-command.sh loop" in raw["roles"]["maker"]["allowed_commands"]
    assert (
        "scripts/guard-command.sh git-status"
        in raw["roles"]["maker"]["allowed_commands"]
    )
    assert raw["roles"]["maker"]["verifier_ephemeral_writes"]["owner"] == (
        "scripts/verify.sh"
    )
    assert raw["roles"]["checker"]["writable_paths"] == []
    assert raw["roles"]["checker"]["tracked_artifact_writes"] == "deny"
    assert raw["roles"]["checker"]["verifier_ephemeral_writes"]["owner"] == (
        "scripts/verify.sh"
    )
    assert raw["roles"]["checker"]["network"] == "deny"


def test_authority_readable_paths_cover_every_tracked_file() -> None:
    raw: Dict[str, Any] = json.loads(
        (ROOT / "policies" / "agent-authority.yaml").read_text(encoding="utf-8")
    )
    tracked_files = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()

    for role_name in ("maker", "checker"):
        readable_paths = raw["roles"][role_name]["readable_paths"]
        uncovered = [
            path
            for path in tracked_files
            if not any(
                path == allowed or (allowed.endswith("/") and path.startswith(allowed))
                for allowed in readable_paths
            )
        ]

        assert uncovered == [], f"{role_name} cannot read tracked files: {uncovered}"


def test_lab_contains_no_private_path_or_key_shaped_value() -> None:
    private_paths = (
        "/" + "Users" + "/",
        "/" + "home" + "/",
    )
    key_patterns = (
        re.compile("gh" + r"p_[A-Za-z0-9]{20,}"),
        re.compile("sk" + r"-[A-Za-z0-9_-]{20,}"),
        re.compile("AI" + r"za[A-Za-z0-9_-]{20,}"),
        re.compile("xo" + r"x[baprs]-[A-Za-z0-9-]{20,}"),
    )
    text_suffixes = {
        "",
        ".json",
        ".jsonl",
        ".md",
        ".py",
        ".sh",
        ".toml",
        ".txt",
        ".yaml",
    }
    candidates = (
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.suffix in text_suffixes
        and ".git" not in path.parts
        and ".venv" not in path.parts
        and "__pycache__" not in path.parts
    )

    findings = []
    for path in candidates:
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        has_private_path = any(pattern in content for pattern in private_paths)
        has_key_shape = any(pattern.search(content) for pattern in key_patterns)
        if has_private_path or has_key_shape:
            findings.append(str(path.relative_to(ROOT)))

    assert findings == []


def test_readme_discloses_pedagogical_boundary() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "不是" in readme
    assert "production" in readme
    assert "47 passed" in readme
    assert "83.18%" in readme
    assert "GitHub Actions" in readme
    assert "Windows PowerShell" in readme


def test_task_and_spec_acceptance_use_distinct_namespaces() -> None:
    task = (ROOT / "tasks" / "task-contract.md").read_text(encoding="utf-8")
    spec = (ROOT / "specs" / "task-board.md").read_text(encoding="utf-8")

    assert "- TAC-01：" in task
    assert "| TAC-06 | Task-only verification gate" in task
    assert "- SAC-01：" in spec
    assert "\n- AC-" not in task
    assert "\n- AC-" not in spec


def test_runtime_profile_is_exact_and_bootstrap_uses_it_for_both_paths() -> None:
    profile_path = ROOT / "constraints" / "runtime-profile.txt"
    pins = {}
    for raw_line in profile_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.partition("#")[0].strip()
        if not line:
            continue
        name, separator, version = line.partition("==")
        assert separator == "=="
        assert name
        assert version
        pins[name] = version

    bootstrap = (ROOT / "scripts" / "bootstrap.sh").read_text(encoding="utf-8")
    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    verifier = (ROOT / "scripts" / "verify.sh").read_text(encoding="utf-8")

    assert pins == BOOK_PROFILE
    assert "version-locked teaching profile" in profile_path.read_text(encoding="utf-8")
    assert "not a hash-locked software supply-chain guarantee" in (
        profile_path.read_text(encoding="utf-8")
    )
    assert 'constraints_file="${CONSTRAINTS_FILE:-constraints/' in bootstrap
    assert bootstrap.count('--constraint "$constraints_file"') == 3
    assert bootstrap.count("--no-build-isolation") == 2
    assert "sys.version_info >= (3, 12)" in bootstrap
    assert 'requires-python = ">=3.12"' in project
    assert 'target-version = ["py312"]' in project
    assert 'target-version = "py312"' in project
    assert "sys.version_info >= (3, 12)" in verifier
    assert "requires Python 3.12+" in verifier


def test_evidence_manifest_records_reproducibility_identity(
    tmp_path: Path,
) -> None:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    output = tmp_path / "manifest.json"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/write_evidence_manifest.py",
            "--output",
            str(output),
            "--profile",
            "constraints/runtime-profile.txt",
            "--commit",
            commit,
            "--run-id",
            "schema-test",
            "--mode",
            "fast",
            "--started-at",
            "2000-01-01T00:00:00Z",
            "--ended-at",
            "2000-01-01T00:00:01Z",
            "--exit-code",
            "0",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    manifest = json.loads(output.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 2
    assert set(manifest["environment"]["os"]) == {"machine", "release", "system"}
    assert set(manifest["environment"]["python"]) == {
        "full",
        "implementation",
        "version",
    }
    assert manifest["repository"]["commit"] == commit
    assert manifest["repository"]["object_format"] in {"sha1", "sha256"}
    source = manifest["repository"]["source"]
    assert source["algorithm"] == "sha256-git-tree-content-v1"
    assert re.fullmatch(r"[0-9a-f]{64}", source["digest"])
    assert source["tracked_file_count"] > 0
    assert source["exclusions"] == ["evidence/runs/**"]
    profile = manifest["dependency_profile"]
    assert profile["path"] == "constraints/runtime-profile.txt"
    assert profile["kind"] == "version-locked"
    assert profile["hash_locked_supply_chain"] is False
    assert re.fullmatch(r"[0-9a-f]{64}", profile["sha256"])
    assert {
        name: details["expected"] for name, details in manifest["tools"].items()
    } == BOOK_PROFILE
    assert manifest["verification"] == {"exit_code": 0, "status": "pass"}


def test_docs_distinguish_scope_from_runtime_isolation() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    spec = (ROOT / "specs" / "task-board.md").read_text(encoding="utf-8")
    task = (ROOT / "tasks" / "task-contract.md").read_text(encoding="utf-8")

    assert "沒有 OS filesystem sandbox" in readme
    assert "不是 network isolation 證明" in readme
    assert "預設會連 Python package index" in readme
    assert "- SAC-09：" in spec
    assert "`--store` 接受使用者指定的本機路徑" in spec
    assert "不是 OS sandbox 證明" in task
