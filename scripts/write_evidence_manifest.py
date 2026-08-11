#!/usr/bin/env python3
"""Write a portable, reproducibility-focused Evidence manifest."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Final

PROFILE_LINE: Final = re.compile(
    r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)==(?P<version>[^\s;]+)$"
)
SOURCE_EXCLUSIONS: Final = ("evidence/runs/**",)
STATUS_BY_EXIT_CODE: Final = {
    0: "pass",
    1: "fail",
    2: "environment-error",
}


def _git(root: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return completed.stdout


def _is_excluded_source(path: str) -> bool:
    return path.startswith("evidence/runs/")


def _source_digest(root: Path, commit: str) -> tuple[str, int]:
    """Hash tracked path, mode, type, and blob content at one commit.

    Hashing blob content instead of Git object IDs keeps this digest independent
    of whether the repository itself uses SHA-1 or SHA-256 object IDs.
    """

    listing = _git(root, "ls-tree", "-r", "-z", commit, "--", ".")
    digest = hashlib.sha256()
    included = 0

    for record in listing.split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", maxsplit=1)
        mode, object_type, object_id = metadata.split(b" ", maxsplit=2)
        path = raw_path.decode("utf-8", errors="surrogateescape")
        if _is_excluded_source(path):
            continue

        if object_type == b"blob":
            content = _git(root, "cat-file", "blob", object_id.decode("ascii"))
        else:
            content = object_id

        for field in (mode, object_type, raw_path, str(len(content)).encode("ascii")):
            digest.update(field)
            digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")
        included += 1

    return digest.hexdigest(), included


def _object_format(root: Path, commit: str) -> str:
    try:
        return _git(root, "rev-parse", "--show-object-format").decode().strip()
    except subprocess.CalledProcessError:
        if len(commit) == 40:
            return "sha1"
        if len(commit) == 64:
            return "sha256"
        return "unknown"


def _dependency_profile(path: Path) -> dict[str, str]:
    expected: dict[str, str] = {}
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.partition("#")[0].strip()
        if not line:
            continue
        match = PROFILE_LINE.fullmatch(line)
        if match is None:
            raise ValueError(
                f"dependency profile line {line_number} is not an exact pin"
            )
        expected[match.group("name")] = match.group("version")
    if not expected:
        raise ValueError("dependency profile has no exact pins")
    return expected


def _observed_versions(expected: dict[str, str]) -> dict[str, str | None]:
    observed: dict[str, str | None] = {}
    for name in expected:
        try:
            observed[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            observed[name] = None
    return observed


def _display_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return f"<external>/{path.name}"


def build_manifest(
    *,
    root: Path,
    profile_path: Path,
    commit: str,
    run_id: str,
    mode: str,
    started_at: str,
    ended_at: str,
    exit_code: int,
) -> dict[str, object]:
    expected = _dependency_profile(profile_path)
    observed = _observed_versions(expected)
    source_sha256, tracked_file_count = _source_digest(root, commit)
    tools = {
        name: {
            "expected": expected[name],
            "matches_profile": observed[name] == expected[name],
            "observed": observed[name],
        }
        for name in sorted(expected, key=str.casefold)
    }

    return {
        "schema_version": 2,
        "run_id": run_id,
        "mode": mode,
        "started_at": started_at,
        "ended_at": ended_at,
        "environment": {
            "os": {
                "machine": platform.machine(),
                "release": platform.release(),
                "system": platform.system(),
            },
            "python": {
                "full": " ".join(sys.version.splitlines()),
                "implementation": platform.python_implementation(),
                "version": platform.python_version(),
            },
        },
        "repository": {
            "commit": commit,
            "object_format": _object_format(root, commit),
            "source": {
                "algorithm": "sha256-git-tree-content-v1",
                "digest": source_sha256,
                "exclusions": list(SOURCE_EXCLUSIONS),
                "tracked_file_count": tracked_file_count,
            },
        },
        "dependency_profile": {
            "hash_locked_supply_chain": False,
            "kind": "version-locked",
            "matches_environment": all(
                item["matches_profile"] for item in tools.values()
            ),
            "path": _display_path(root, profile_path),
            "sha256": hashlib.sha256(profile_path.read_bytes()).hexdigest(),
        },
        "tools": tools,
        "verification": {
            "exit_code": exit_code,
            "status": STATUS_BY_EXIT_CODE[exit_code],
        },
    }


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--mode", required=True, choices=("fast", "full"))
    parser.add_argument("--started-at", required=True)
    parser.add_argument("--ended-at", required=True)
    parser.add_argument("--exit-code", required=True, type=int, choices=(0, 1, 2))
    return parser.parse_args()


def main() -> int:
    arguments = _parse_arguments()
    root = Path(__file__).resolve().parents[1]
    manifest = build_manifest(
        root=root,
        profile_path=arguments.profile,
        commit=arguments.commit,
        run_id=arguments.run_id,
        mode=arguments.mode,
        started_at=arguments.started_at,
        ended_at=arguments.ended_at,
        exit_code=arguments.exit_code,
    )
    arguments.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
