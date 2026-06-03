from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Iterable

from afritech.extensions.afriprog.validator_runner.command_result import (
    CommandResult,
)
#from afritech/extensions/afriprog/validator_runner/flutter_runner.py

class FlutterRunnerError(Exception):
    """Raised when Flutter command execution fails before completion."""


def _normalize_output(value: str | bytes | None) -> str:
    if value is None:
        return ""

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    return value


class FlutterRunner:
    """
    Read-only Flutter validator runner.

    Constitutional properties:
    - allowed Flutter commands only
    - no shell execution
    - captures stdout/stderr/exit_code
    - non-authoritative
    """

    DEFAULT_TIMEOUT_SECONDS = 180

    ALLOWED_COMMANDS = frozenset(
        {
            ("flutter", "analyze"),
            ("flutter", "test"),
        }
    )

    def __init__(
        self,
        root: str | Path,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ):
        self.root = Path(root).resolve()

        if not self.root.exists():
            raise FlutterRunnerError(f"root does not exist: {self.root}")

        if not self.root.is_dir():
            raise FlutterRunnerError(f"root is not a directory: {self.root}")

        if timeout_seconds <= 0:
            raise FlutterRunnerError("timeout_seconds must be positive")

        self.timeout_seconds = timeout_seconds

    def run_analyze(
        self,
        extra_args: Iterable[str] = (),
    ) -> CommandResult:
        command = ["flutter", "analyze"]
        command.extend(str(arg) for arg in extra_args)
        return self._run(command)

    def run_tests(
        self,
        extra_args: Iterable[str] = (),
    ) -> CommandResult:
        command = ["flutter", "test"]
        command.extend(str(arg) for arg in extra_args)
        return self._run(command)

    def _run(self, command: list[str]) -> CommandResult:
        if len(command) < 2:
            raise FlutterRunnerError("flutter command must include subcommand")

        command_prefix = tuple(command[:2])

        if command_prefix not in self.ALLOWED_COMMANDS:
            raise FlutterRunnerError(
                f"unsupported Flutter command: {' '.join(command)}"
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
                stderr=(
                    _normalize_output(exc.stderr)
                    or "flutter command timed out"
                ),
                duration_seconds=duration,
            )
        except OSError as exc:
            raise FlutterRunnerError(
                f"failed to execute Flutter command: {exc}"
            ) from exc

        duration = time.monotonic() - started

        return CommandResult(
            command=tuple(command),
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration_seconds=duration,
        )