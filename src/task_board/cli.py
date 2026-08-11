"""Command-line interface for the local task board."""

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from task_board.domain import Task, TaskBoardError
from task_board.repository import TaskRepository
from task_board.service import TaskService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="task-board",
        description="Local-only task board for the AI development lab.",
    )
    parser.add_argument(
        "--store",
        default="runtime/tasks.json",
        help="local JSON store path (default: runtime/tasks.json)",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="create an empty store without overwriting")

    add_parser = commands.add_parser("add", help="add one task")
    add_parser.add_argument("title")
    add_parser.add_argument(
        "--priority",
        choices=("low", "medium", "high"),
        default="medium",
    )

    list_parser = commands.add_parser("list", help="list tasks")
    list_parser.add_argument("--status", choices=("todo", "done"))

    show_parser = commands.add_parser("show", help="show one task")
    show_parser.add_argument("task_id")

    complete_parser = commands.add_parser("complete", help="complete one task")
    complete_parser.add_argument("task_id")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    repository = TaskRepository(Path(args.store))
    service = TaskService(repository)
    try:
        if args.command == "init":
            created = repository.initialize()
            state = "created" if created else "exists"
            _write_output(f"store {state}: {repository.path}")
            return 0
        if args.command == "add":
            task = service.add(args.title, args.priority)
            _write_output(f"created {_format_task(task)}")
            return 0
        if args.command == "list":
            tasks = service.list(args.status)
            _write_output("\n".join(_format_task(task) for task in tasks) or "no tasks")
            return 0
        if args.command == "show":
            _write_output(_format_task(service.show(args.task_id)))
            return 0
        if args.command == "complete":
            _write_output(f"completed {_format_task(service.complete(args.task_id))}")
            return 0
    except TaskBoardError as exc:
        sys.stderr.write(f"task-board error: {exc}\n")
        return 2
    sys.stderr.write("task-board error: unsupported command\n")
    return 2


def entrypoint() -> None:
    raise SystemExit(main())


def _format_task(task: Task) -> str:
    return f"{task.task_id} [{task.status}] " f"{task.priority} | {task.title}"


def _write_output(value: str) -> None:
    sys.stdout.write(f"{value}\n")
