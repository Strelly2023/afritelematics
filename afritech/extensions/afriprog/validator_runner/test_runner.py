from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Iterable

from afritech.extensions.afriprog.validator_runner.command_result import (
    CommandResult,
)


class TestRunnerError(Exception):
    """Raised when pytest execution fails before command completion."""


def _normalize_output(value: str | bytes | None) -> str:
    if value is None:
        return ""

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    return value


class TestRunner:
    """
    Read-only pytest runner.

    Constitutional properties:
    - allowed command only
    - isolated pytest config
    - plugin autoload disabled
    - no shell execution
    - no filesystem mutation by this class
    - captures stdout/stderr/exit_code
    - non-authoritative
    """

    DEFAULT_TIMEOUT_SECONDS = 120
    PYTEST_COMMAND_PREFIX = (
        "python3",
        "-m",
        "pytest",
        "-c",
        "/dev/null",
    )

    def __init__(
        self,
        root: str | Path = ".",
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ):
        self.root = Path(root).resolve()

        if not self.root.exists():
            raise TestRunnerError(f"root does not exist: {self.root}")

        if not self.root.is_dir():
            raise TestRunnerError(f"root is not a directory: {self.root}")

        if timeout_seconds <= 0:
            raise TestRunnerError("timeout_seconds must be positive")

        self.timeout_seconds = timeout_seconds

    def run_pytest(
        self,
        targets: Iterable[str] = (),
        quiet: bool = True,
    ) -> CommandResult:
        command: list[str] = [
            "python3",
            "-m",
            "pytest",
            "-c",
            "/dev/null",
        ]

        if quiet:
            command.append("-q")

        command.extend(str(target) for target in targets)

        return self._run(command)

    def run_file(self, test_file: str | Path) -> CommandResult:
        return self.run_pytest(
            targets=(str(test_file),),
            quiet=True,
        )

    def _run(self, command: list[str]) -> CommandResult:
        if not command:
            raise TestRunnerError("command must not be empty")

        if tuple(command[:5]) != self.PYTEST_COMMAND_PREFIX:
            raise TestRunnerError(
                f"unsupported command for TestRunner: {' '.join(command)}"
            )

        env = dict(os.environ)
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"

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
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            duration = time.monotonic() - started

            return CommandResult(
                command=tuple(command),
                exit_code=124,
                stdout=_normalize_output(exc.stdout),
                stderr=(
                    _normalize_output(exc.stderr)
                    or "pytest command timed out"
                ),
                duration_seconds=duration,
            )
        except OSError as exc:
            raise TestRunnerError(
                f"failed to execute pytest command: {exc}"
            ) from exc

        duration = time.monotonic() - started

        return CommandResult(
            command=tuple(command),
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration_seconds=duration,
        )