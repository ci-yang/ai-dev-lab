"""Immutable domain objects and validation rules."""

import re
from dataclasses import dataclass, replace
from typing import Any, Dict

VALID_PRIORITIES = frozenset({"low", "medium", "high"})
VALID_STATUSES = frozenset({"todo", "done"})
TASK_ID_PATTERN = re.compile(r"TB-[0-9]{3,}")


class TaskBoardError(Exception):
    """Base class for expected task-board failures."""


class ValidationError(TaskBoardError):
    """Raised when user-controlled data violates the task contract."""


class TaskNotFoundError(TaskBoardError):
    """Raised when a requested task does not exist."""


class DataFormatError(TaskBoardError):
    """Raised when the local JSON store cannot be trusted."""


@dataclass(frozen=True)
class Task:
    """A task whose identity and state can be serialized deterministically."""

    task_id: str
    title: str
    priority: str
    status: str = "todo"

    def __post_init__(self) -> None:
        if TASK_ID_PATTERN.fullmatch(self.task_id) is None:
            raise ValidationError(
                "task id must use TB- followed by at least three digits"
            )
        if not self.title.strip():
            raise ValidationError("title must not be blank")
        if self.priority not in VALID_PRIORITIES:
            raise ValidationError("priority must be one of: high, low, medium")
        if self.status not in VALID_STATUSES:
            raise ValidationError("status must be one of: done, todo")

    def complete(self) -> "Task":
        """Return a completed copy without mutating the original task."""

        return replace(self, status="done")

    def to_dict(self) -> Dict[str, str]:
        """Return the stable JSON representation."""

        return {
            "id": self.task_id,
            "title": self.title,
            "priority": self.priority,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "Task":
        """Validate and restore a task from untrusted local JSON."""

        required = {"id", "title", "priority", "status"}
        if set(raw) != required:
            raise DataFormatError("task record has unexpected fields")
        if not all(isinstance(raw[key], str) for key in required):
            raise DataFormatError("task record fields must be strings")
        try:
            return cls(
                task_id=raw["id"],
                title=raw["title"],
                priority=raw["priority"],
                status=raw["status"],
            )
        except ValidationError as exc:
            raise DataFormatError(str(exc)) from exc
