from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class CommandResultError(Exception):
    """Raised when command result construction fails."""


@dataclass(frozen=True)
class CommandResult:
    """
    Canonical read-only validator command result.

    Constitutional properties:
    - immutable
    - deterministic
    - evidence-ready
    - non-authoritative
    """

    command: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float

    def __post_init__(self) -> None:
        if not self.command:
            raise CommandResultError("command must not be empty")

        if not all(isinstance(part, str) and part.strip() for part in self.command):
            raise CommandResultError("command parts must be non-empty strings")

        if not isinstance(self.exit_code, int):
            raise CommandResultError("exit_code must be an integer")

        if self.duration_seconds < 0:
            raise CommandResultError("duration_seconds must not be negative")

    @property
    def passed(self) -> bool:
        return self.exit_code == 0

    @property
    def failed(self) -> bool:
        return not self.passed

    @property
    def command_string(self) -> str:
        return " ".join(self.command)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "command": list(self.command),
            "command_string": self.command_string,
            "exit_code": self.exit_code,
            "passed": self.passed,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_seconds": round(self.duration_seconds, 6),
        }

    def to_dict(self) -> dict[str, Any]:
        return self.canonical_dict()