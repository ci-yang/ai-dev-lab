import json
from pathlib import Path

import pytest

from task_board.cli import main


def test_cli_happy_path_is_observable(
    tmp_path: Path,
    capsys: object,
) -> None:
    store = tmp_path / "tasks.json"
    base = ["--store", str(store)]

    assert main([*base, "init"]) == 0
    assert main([*base, "add", "Map the repository", "--priority", "high"]) == 0
    assert main([*base, "list"]) == 0
    assert main([*base, "complete", "TB-001"]) == 0

    output = capsys.readouterr().out
    assert "store created" in output
    assert "TB-001 [todo] high | Map the repository" in output
    assert "TB-001 [done] high | Map the repository" in output
    assert json.loads(store.read_text(encoding="utf-8"))[0]["status"] == "done"


def test_cli_reports_domain_error_without_traceback(
    tmp_path: Path,
    capsys: object,
) -> None:
    code = main(
        [
            "--store",
            str(tmp_path / "tasks.json"),
            "complete",
            "TB-404",
        ]
    )

    captured = capsys.readouterr()
    assert code == 2
    assert captured.out == ""
    assert "task not found: TB-404" in captured.err
    assert "Traceback" not in captured.err


def test_repeated_init_preserves_existing_tasks(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    store = tmp_path / "tasks.json"
    base = ["--store", str(store)]

    assert main([*base, "init"]) == 0
    assert main([*base, "add", "First", "--priority", "high"]) == 0
    assert main([*base, "add", "Second", "--priority", "medium"]) == 0
    assert main([*base, "init"]) == 0
    assert main([*base, "list"]) == 0

    captured = capsys.readouterr()
    assert "store exists" in captured.out
    assert "TB-001 [todo] high | First" in captured.out
    assert "TB-002 [todo] medium | Second" in captured.out
    assert len(json.loads(store.read_text(encoding="utf-8"))) == 2


def test_cli_reports_non_utf8_store_without_traceback(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    store = tmp_path / "tasks.json"
    store.write_bytes(b"\xff")

    code = main(["--store", str(store), "list"])

    captured = capsys.readouterr()
    assert code == 2
    assert captured.out == ""
    assert "cannot read task store" in captured.err
    assert "Traceback" not in captured.err


def test_cli_reports_invalid_stored_id_without_traceback(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    store = tmp_path / "tasks.json"
    store.write_text(
        json.dumps(
            [
                {
                    "id": "TB-abc",
                    "title": "Invalid identity",
                    "priority": "medium",
                    "status": "todo",
                }
            ]
        ),
        encoding="utf-8",
    )

    code = main(["--store", str(store), "add", "Safe change"])

    captured = capsys.readouterr()
    assert code == 2
    assert captured.out == ""
    assert "at least three digits" in captured.err
    assert "Traceback" not in captured.err


def test_cli_reports_unwritable_parent_without_traceback(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(["--store", "/dev/null/tasks.json", "add", "Safe change"])

    captured = capsys.readouterr()
    assert code == 2
    assert captured.out == ""
    assert "cannot write task store" in captured.err
    assert "Traceback" not in captured.err


def test_cli_creates_custom_store_parent(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    store = tmp_path / "nested" / "runtime" / "tasks.json"

    code = main(["--store", str(store), "add", "Nested store"])

    captured = capsys.readouterr()
    assert code == 0
    assert "TB-001 [todo] medium | Nested store" in captured.out
    assert captured.err == ""
    assert store.exists()
