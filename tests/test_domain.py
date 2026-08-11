import pytest

from task_board.domain import DataFormatError, Task, ValidationError


def test_complete_returns_new_immutable_task() -> None:
    original = Task("TB-001", "Write a test", "high")

    completed = original.complete()

    assert original.status == "todo"
    assert completed.status == "done"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("task_id", "001"),
        ("task_id", "TB-abc"),
        ("task_id", "TB-1"),
        ("title", "   "),
        ("priority", "urgent"),
        ("status", "running"),
    ],
)
def test_invalid_task_fields_are_rejected(field: str, value: str) -> None:
    values = {
        "task_id": "TB-001",
        "title": "Write a test",
        "priority": "medium",
        "status": "todo",
    }
    values[field] = value

    with pytest.raises(ValidationError):
        Task(**values)


def test_unexpected_json_fields_are_rejected() -> None:
    with pytest.raises(DataFormatError, match="unexpected fields"):
        Task.from_dict(
            {
                "id": "TB-001",
                "title": "Write a test",
                "priority": "medium",
                "status": "todo",
                "secret": "not-allowed",
            }
        )


def test_invalid_stored_task_id_is_reported_as_data_error() -> None:
    with pytest.raises(DataFormatError, match="at least three digits"):
        Task.from_dict(
            {
                "id": "TB-abc",
                "title": "Untrusted record",
                "priority": "medium",
                "status": "todo",
            }
        )
