from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Iterable

from afritech.extensions.afriprog.validator_runner.command_result import (
    CommandResult,
)


class CIRunnerError(Exception):
    """Raised when CI validator execution fails before completion."""


def _normalize_output(value: str | bytes | None) -> str:
    if value is None:
        return ""

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    return value


class CIRunner:
    """
    Read-only AfriTech CI validator runner.

    Constitutional properties:
    - allowed python module commands only
    - no shell execution
    - captures stdout/stderr/exit_code
    - non-authoritative
    - does not patch, write, commit, or mutate
    """

    DEFAULT_TIMEOUT_SECONDS = 180

    ALLOWED_MODULES = frozenset(
        {
            "afritech.ci.constitutional_validation",
            "afritech.extensions.afriprog.repository_intelligence.orchestrator_preview",
            "afritech.extensions.afriprog.orchestrator",
        }
    )

    def __init__(
        self,
        root: str | Path = ".",
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ):
        self.root = Path(root).resolve()

        if not self.root.exists():
            raise CIRunnerError(f"root does not exist: {self.root}")

        if not self.root.is_dir():
            raise CIRunnerError(f"root is not a directory: {self.root}")

        if timeout_seconds <= 0:
            raise CIRunnerError("timeout_seconds must be positive")

        self.timeout_seconds = timeout_seconds

    def run_module(
        self,
        module_name: str,
        extra_args: Iterable[str] = (),
    ) -> CommandResult:
        if module_name not in self.ALLOWED_MODULES:
            raise CIRunnerError(
                f"unsupported CI module: {module_name}"
            )

        command = ["python3", "-m", module_name]
        command.extend(str(arg) for arg in extra_args)

        return self._run(command)

    def run_constitutional_validation(self) -> CommandResult:
        return self.run_module(
            "afritech.ci.constitutional_validation"
        )

    def run_repository_intelligence_preview(self) -> CommandResult:
        return self.run_module(
            "afritech.extensions.afriprog.repository_intelligence.orchestrator_preview"
        )

    def run_phase_2_orchestrator_preview(self) -> CommandResult:
        return self.run_module(
            "afritech.extensions.afriprog.orchestrator"
        )

    def run_many(
        self,
        module_names: Iterable[str],
    ) -> tuple[CommandResult, ...]:
        return tuple(
            self.run_module(module_name)
            for module_name in module_names
        )

    def _run(self, command: list[str]) -> CommandResult:
        if len(command) < 3:
            raise CIRunnerError("CI command must include python module")

        if command[0:2] != ["python3", "-m"]:
            raise CIRunnerError(
                f"unsupported CI command: {' '.join(command)}"
            )

        module_name = command[2]

        if module_name not in self.ALLOWED_MODULES:
            raise CIRunnerError(
                f"unsupported CI module: {module_name}"
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
                    or "CI command timed out"
                ),
                duration_seconds=duration,
            )
        except OSError as exc:
            raise CIRunnerError(
                f"failed to execute CI command: {exc}"
            ) from exc

        duration = time.monotonic() - started

        return CommandResult(
            command=tuple(command),
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration_seconds=duration,
        )