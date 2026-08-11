import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[1]


def _environment() -> Dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    return environment


def test_guard_rejects_unlisted_action() -> None:
    completed = subprocess.run(
        ["bash", "scripts/guard-command.sh", "delete-everything"],
        cwd=ROOT,
        env=_environment(),
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "guard rejected" in completed.stderr


def test_guard_runs_task_board_without_shell_interpolation(
    tmp_path: Path,
) -> None:
    store = tmp_path / "tasks.json"
    title = "Keep $(commands) as plain text"
    completed = subprocess.run(
        [
            "bash",
            "scripts/guard-command.sh",
            "task-board",
            "--store",
            str(store),
            "add",
            title,
        ],
        cwd=ROOT,
        env=_environment(),
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert title in completed.stdout
    assert not (ROOT / "commands").exists()


def test_control_scripts_classify_failures_deterministically(
    tmp_path: Path,
) -> None:
    completed = subprocess.run(
        ["python3", "-m", "task_board.demo_verifier", "fail"],
        cwd=ROOT,
        env=_environment(),
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1
    assert completed.stdout == ""
    assert completed.stderr == ("PEDAGOGICAL_DEMO: repeated acceptance failure\n")

    isolated_python = tmp_path / "python-without-site-packages"
    isolated_python.write_text(
        "#!/usr/bin/env bash\n" f'exec {shlex.quote(sys.executable)} -S "$@"\n',
        encoding="utf-8",
    )
    isolated_python.chmod(0o755)
    environment = _environment()
    environment["PYTHON_BIN"] = str(isolated_python)

    missing_pytest = subprocess.run(
        ["bash", "scripts/verify.sh", "fast"],
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert missing_pytest.returncode == 2
    assert "environment error" in missing_pytest.stderr
    assert "missing pytest" in missing_pytest.stderr

    verify_script = (ROOT / "scripts" / "verify.sh").read_text(encoding="utf-8")
    assert '"$python_bin" -m compileall -q -f src tests' in verify_script
    assert 'PYTHONPYCACHEPREFIX="$root/runtime/pycache"' in verify_script

    pycache_root = tmp_path / "contained-pycache"
    cache_probe = _environment()
    cache_probe["PYTHONPYCACHEPREFIX"] = str(pycache_root)
    cache_path = subprocess.run(
        [
            sys.executable,
            "-c",
            "import importlib.util; "
            "print(importlib.util.cache_from_source('src/task_board/service.py'))",
        ],
        cwd=ROOT,
        env=cache_probe,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert Path(cache_path).is_relative_to(pycache_root)


def test_evidence_collector_rejects_tracked_dirty_source(tmp_path: Path) -> None:
    lab_copy = tmp_path / "ai-dev-lab"
    shutil.copytree(
        ROOT,
        lab_copy,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            "runtime",
            ".pytest_cache",
            ".ruff_cache",
            ".coverage",
            "htmlcov",
        ),
    )
    subprocess.run(["git", "init", "-q"], cwd=lab_copy, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Evidence Test"],
        cwd=lab_copy,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "evidence-test@localhost"],
        cwd=lab_copy,
        check=True,
    )
    subprocess.run(["git", "add", "."], cwd=lab_copy, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "test: establish collector baseline"],
        cwd=lab_copy,
        check=True,
    )
    readme = lab_copy / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8") + "\ntracked dirty probe\n",
        encoding="utf-8",
    )
    environment = _environment()
    environment["PYTHON_BIN"] = sys.executable
    environment["RUN_ID"] = "tracked-dirty-probe"

    completed = subprocess.run(
        ["bash", "scripts/collect-evidence.sh", "fast"],
        cwd=lab_copy,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    run = lab_copy / "evidence" / "runs" / "tracked-dirty-probe"
    assert completed.returncode == 2
    assert (run / "status.txt").read_text(encoding="utf-8").strip()
    assert (run / "change.diff").read_text(encoding="utf-8").strip()
    assert "verification not run" in (run / "verifier.out").read_text(encoding="utf-8")
