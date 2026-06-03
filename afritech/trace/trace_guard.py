"""Trace guard for Phase 0 constitutional replay.

No trace → no replay.
No replay → no legitimacy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


class TraceValidationError(RuntimeError):
    """Raised when an execution trace is invalid."""


@dataclass(frozen=True)
class TraceValidationResult:
    valid: bool
    reason: str

    def canonical_dict(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "reason": self.reason,
        }


REQUIRED_TRACE_FIELDS = {
    "surface",
    "input",
    "output",
    "hash",
}


def validate_trace(trace: Mapping[str, Any]) -> TraceValidationResult:
    """Validate that a trace is structurally replayable."""

    if not isinstance(trace, Mapping):
        raise TraceValidationError("trace must be a mapping")

    missing = sorted(REQUIRED_TRACE_FIELDS.difference(trace))

    if missing:
        raise TraceValidationError(
            f"trace missing required fields: {', '.join(missing)}"
        )

    if not isinstance(trace["surface"], str) or not trace["surface"]:
        raise TraceValidationError("trace surface must be a non-empty string")

    if not isinstance(trace["hash"], str) or not trace["hash"]:
        raise TraceValidationError("trace hash must be a non-empty string")

    return TraceValidationResult(
        valid=True,
        reason="trace_valid",
    )


def require_valid_trace(trace: Mapping[str, Any]) -> Mapping[str, Any]:
    """Fail-closed helper used before replay and proof generation."""

    validate_trace(trace)
    return trace