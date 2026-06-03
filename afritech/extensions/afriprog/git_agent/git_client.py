from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from afritech.extensions.afriprog.validator_runner.command_result import (
    CommandResult,
)


class GitClientError(Exception):
    """Raised when read-only git inspection cannot be completed."""


@dataclass(frozen=True)
class GitSnapshot:
    """
    Deterministic read-only git repository snapshot.

    Constitutional properties:
    - no staging
    - no committing
    - no pushing
    - no branch mutation
    - evidence-ready
    """

    branch: str
    status_short: tuple[str, ...]
    changed_files: tuple[str, ...]
    head_sha: str

    @property
    def dirty(self) -> bool:
        return bool(self.status_short)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "branch": self.branch,
            "dirty": self.dirty,
            "status_short": list(self.status_short),
            "changed_files": list(self.changed_files),
            "head_sha": self.head_sha,
        }


class GitClient:
    """
    Proposal-only git adapter for AfriProgramming.

    This client intentionally exposes read-only inspection only. It can observe
    branch, status, diff, and HEAD state, but it cannot stage, commit, push, or
    create pull requests.
    """

    DEFAULT_TIMEOUT_SECONDS = 30
    ALLOWED_COMMANDS = frozenset(
        {
            ("git", "status", "--short"),
            ("git", "branch", "--show-current"),
            ("git", "rev-parse", "HEAD"),
            ("git", "diff", "--"),
        }
    )

    def __init__(
        self,
        root: str | Path = ".",
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.root = Path(root).resolve()

        if not self.root.exists():
            raise GitClientError(f"root does not exist: {self.root}")

        if not self.root.is_dir():
            raise GitClientError(f"root is not a directory: {self.root}")

        if timeout_seconds <= 0:
            raise GitClientError("timeout_seconds must be positive")

        self.timeout_seconds = timeout_seconds

    def status_short(self) -> CommandResult:
        return self._run(["git", "status", "--short"])

    def current_branch(self) -> CommandResult:
        return self._run(["git", "branch", "--show-current"])

    def head_sha(self) -> CommandResult:
        return self._run(["git", "rev-parse", "HEAD"])

    def diff(self) -> CommandResult:
        return self._run(["git", "diff", "--"])

    def snapshot(self) -> GitSnapshot:
        status = self.status_short()
        branch = self.current_branch()
        head = self.head_sha()

        status_lines = tuple(
            line.rstrip()
            for line in status.stdout.splitlines()
            if line.strip()
        )

        changed_files = tuple(
            sorted(
                line[3:].strip()
                for line in status_lines
                if len(line) > 3
            )
        )

        return GitSnapshot(
            branch=branch.stdout.strip(),
            status_short=status_lines,
            changed_files=changed_files,
            head_sha=head.stdout.strip(),
        )

    def _run(self, command: list[str]) -> CommandResult:
        if tuple(command) not in self.ALLOWED_COMMANDS:
            raise GitClientError(
                f"unsupported git command: {' '.join(command)}"
            )

        started = time.monotonic()

        try:
            completed = subprocess.run(
                command,
                cwd=self.root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout_seconds,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            duration = time.monotonic() - started
            return CommandResult(
                command=tuple(command),
                exit_code=124,
                stdout=_normalize_output(exc.stdout),
                stderr=_normalize_output(exc.stderr) or "git command timed out",
                duration_seconds=duration,
            )
        except OSError as exc:
            raise GitClientError(f"failed to execute git command: {exc}") from exc

        return CommandResult(
            command=tuple(command),
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration_seconds=time.monotonic() - started,
        )


def _normalize_output(value: str | bytes | None) -> str:
    if value is None:
        return ""

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    return value
