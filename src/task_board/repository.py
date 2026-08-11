"""Atomic JSON persistence for the local task board."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable, Tuple

from task_board.domain import DataFormatError, Task


class TaskRepository:
    """Read and atomically replace one local JSON task store."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def initialize(self) -> bool:
        """Create an empty store once; never overwrite an existing store."""

        if self.path.exists():
            return False
        self.save(())
        return True

    def load(self) -> Tuple[Task, ...]:
        """Load and validate every stored task."""

        if not self.path.exists():
            return ()
        try:
            raw: Any = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DataFormatError(f"cannot read task store: {exc}") from exc
        if not isinstance(raw, list):
            raise DataFormatError("task store root must be a JSON array")
        if not all(isinstance(item, dict) for item in raw):
            raise DataFormatError("each task record must be a JSON object")
        tasks = tuple(Task.from_dict(item) for item in raw)
        return tuple(sorted(tasks, key=_task_number))

    def save(self, tasks: Iterable[Task]) -> None:
        """Atomically persist tasks in task-id order."""

        payload = [task.to_dict() for task in sorted(tasks, key=_task_number)]
        temporary_path: Path | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(
                dir=str(self.path.parent),
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                text=True,
            )
            temporary_path = Path(temporary_name)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(
                    payload,
                    handle,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, self.path)
        except OSError as exc:
            raise DataFormatError(f"cannot write task store: {exc}") from exc
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)


def _task_number(task: Task) -> int:
    try:
        return int(task.task_id.removeprefix("TB-"))
    except ValueError as exc:
        raise DataFormatError("task id suffix must be numeric") from exc
