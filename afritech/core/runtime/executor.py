"""Canonical runtime executor facade."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Iterable, Sequence

from afritech.core.runtime.engine.executor import ExecutionEngine, ExecutionError

__all__ = [
    "DeterministicCommandExecutor",
    "ExecutionEngine",
    "ExecutionError",
]


class DeterministicCommandExecutor:
    """Shared deterministic command execution loop for bounded domains."""

    @staticmethod
    def trace_hash(trace: list[dict[str, Any]]) -> str:
        payload = json.dumps(trace, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()

    @classmethod
    def execute_with_state(
        cls,
        *,
        state: Any,
        commands: Iterable[Any],
        epoch: int,
        allowed_commands: Sequence[type],
        canonical_key: Callable[[Any], tuple[str, str]],
        admissible: Callable[[Any, Any], bool],
        apply_mutation: Callable[[Any, Any], Any],
        refusal_driver: Callable[[Any], Any],
        observational_commands: Sequence[type] = (),
    ) -> tuple[list[dict[str, Any]], Any]:
        command_tuple = tuple(commands)

        for command in command_tuple:
            if not isinstance(command, tuple(allowed_commands)):
                raise AssertionError("NON-ADMISSIBLE COMMAND")

            if hasattr(command, "epoch") and command.epoch is not None:
                if command.epoch > epoch:
                    raise AssertionError("FUTURE-EPOCH COMMAND")

        trace: list[dict[str, Any]] = [
            {"type": "EXECUTION_CONTEXT", "epoch": epoch}
        ]
        current_state = state

        for command in sorted(command_tuple, key=canonical_key):
            if isinstance(command, tuple(observational_commands)):
                continue

            if not admissible(current_state, command):
                trace.append(
                    {
                        "type": "REFUSAL",
                        "command": command.__class__.__name__,
                        "driver": refusal_driver(command),
                    }
                )
                continue

            current_state = apply_mutation(current_state, command)
            trace.append(
                {
                    "type": command.__class__.__name__,
                    "driver": refusal_driver(command),
                }
            )

        return trace, current_state
