"""Application operations for the task-board CLI."""

from typing import Optional, Tuple

from task_board.domain import (
    VALID_PRIORITIES,
    VALID_STATUSES,
    Task,
    TaskNotFoundError,
    ValidationError,
)
from task_board.repository import TaskRepository


class TaskService:
    """Apply task-board behavior without coupling it to terminal I/O."""

    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    def add(self, title: str, priority: str) -> Task:
        normalized_title = title.strip()
        if not normalized_title:
            raise ValidationError("title must not be blank")
        if priority not in VALID_PRIORITIES:
            raise ValidationError("priority must be one of: high, low, medium")
        tasks = self.repository.load()
        next_number = max((_task_number(task) for task in tasks), default=0) + 1
        task = Task(
            task_id=f"TB-{next_number:03d}",
            title=normalized_title,
            priority=priority,
        )
        self.repository.save((*tasks, task))
        return task

    def list(self, status: Optional[str] = None) -> Tuple[Task, ...]:
        if status is not None and status not in VALID_STATUSES:
            raise ValidationError("status must be one of: done, todo")
        tasks = self.repository.load()
        if status is None:
            return tasks
        return tuple(task for task in tasks if task.status == status)

    def show(self, task_id: str) -> Task:
        return _find_task(self.repository.load(), task_id)

    def complete(self, task_id: str) -> Task:
        tasks = self.repository.load()
        current = _find_task(tasks, task_id)
        completed = current.complete()
        self.repository.save(
            completed if task.task_id == task_id else task for task in tasks
        )
        return completed


def _task_number(task: Task) -> int:
    return int(task.task_id.removeprefix("TB-"))


def _find_task(tasks: Tuple[Task, ...], task_id: str) -> Task:
    for task in tasks:
        if task.task_id == task_id:
            return task
    raise TaskNotFoundError(f"task not found: {task_id}")
