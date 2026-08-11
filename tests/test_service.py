import json
from pathlib import Path

import pytest

from task_board.domain import DataFormatError, TaskNotFoundError, ValidationError
from task_board.repository import TaskRepository
from task_board.service import TaskService


def _service(path: Path) -> TaskService:
    return TaskService(TaskRepository(path))


def test_add_list_and_complete_round_trip(tmp_path: Path) -> None:
    store = tmp_path / "tasks.json"
    service = _service(store)

    first = service.add("  Verify the baseline  ", "high")
    second = service.add("Record evidence", "medium")
    completed = service.complete(first.task_id)

    assert first.task_id == "TB-001"
    assert first.title == "Verify the baseline"
    assert second.task_id == "TB-002"
    assert completed.status == "done"
    assert [task.task_id for task in service.list("todo")] == ["TB-002"]
    assert service.show("TB-001").status == "done"


def test_blank_title_does_not_create_store(tmp_path: Path) -> None:
    store = tmp_path / "tasks.json"

    with pytest.raises(ValidationError, match="must not be blank"):
        _service(store).add(" ", "low")

    assert not store.exists()


def test_missing_task_is_reported(tmp_path: Path) -> None:
    with pytest.raises(TaskNotFoundError, match="TB-999"):
        _service(tmp_path / "tasks.json").complete("TB-999")


def test_corrupt_store_is_not_overwritten(tmp_path: Path) -> None:
    store = tmp_path / "tasks.json"
    store.write_text('{"not": "a list"}', encoding="utf-8")

    with pytest.raises(DataFormatError, match="JSON array"):
        _service(store).add("Safe change", "low")

    assert json.loads(store.read_text(encoding="utf-8")) == {"not": "a list"}


def test_list_sorts_valid_records_loaded_out_of_order(tmp_path: Path) -> None:
    store = tmp_path / "tasks.json"
    store.write_text(
        json.dumps(
            [
                {
                    "id": "TB-002",
                    "title": "Second",
                    "priority": "medium",
                    "status": "todo",
                },
                {
                    "id": "TB-001",
                    "title": "First",
                    "priority": "high",
                    "status": "done",
                },
            ]
        ),
        encoding="utf-8",
    )

    assert [task.task_id for task in _service(store).list()] == [
        "TB-001",
        "TB-002",
    ]
