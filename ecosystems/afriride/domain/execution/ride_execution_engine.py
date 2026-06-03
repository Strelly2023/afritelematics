"""Deterministic lifecycle execution over the canonical ride DAG.

The engine records explicit transition steps. It does not mutate rides, infer
transitions, run matching, compute routes, or define replay truth.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Sequence

from ecosystems.afriride.domain.models.canonical_ride import Ride
from ecosystems.afriride.domain.state.ride_lifecycle_dag import (
    RideLifecycleState,
    assert_transition,
)


class RideExecutionViolation(ValueError):
    """Raised when lifecycle execution input is invalid."""


@dataclass(frozen=True)
class TransitionRequest:
    """Explicit request to record one lifecycle transition."""

    ride_hash: str
    current_state: RideLifecycleState | str
    target_state: RideLifecycleState | str
    declared_at: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "ride_hash", _require_text("ride_hash", self.ride_hash))
        if self.declared_at is not None:
            object.__setattr__(
                self,
                "declared_at",
                _require_text("declared_at", self.declared_at),
            )


@dataclass(frozen=True)
class RideExecutionStep:
    """Immutable record of one validated lifecycle transition."""

    ride_hash: str
    from_state: RideLifecycleState
    to_state: RideLifecycleState
    sequence: int
    declared_at: str | None = None

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise RideExecutionViolation("sequence must be non-negative")

    def to_canonical_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready execution step."""

        return {
            "declared_at": self.declared_at,
            "from_state": self.from_state.value,
            "ride_hash": self.ride_hash,
            "sequence": self.sequence,
            "to_state": self.to_state.value,
        }

    def canonical_json(self) -> str:
        """Return stable canonical JSON for trace and replay."""

        return json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
        )

    def step_hash(self) -> str:
        """Return a deterministic content hash for this step."""

        return sha256(self.canonical_json().encode("utf-8")).hexdigest()


def execute_transition(
    ride: Ride,
    request: TransitionRequest,
    *,
    sequence: int,
) -> RideExecutionStep:
    """Validate and record one explicit transition request."""

    if not isinstance(ride, Ride):
        raise RideExecutionViolation("ride must be a canonical Ride")
    if not isinstance(request, TransitionRequest):
        raise RideExecutionViolation("request must be a TransitionRequest")
    if request.ride_hash != ride.ride_hash():
        raise RideExecutionViolation("transition request ride_hash does not match ride")

    target_state = assert_transition(request.current_state, request.target_state)
    from_state = RideLifecycleState(request.current_state)
    return RideExecutionStep(
        ride_hash=request.ride_hash,
        from_state=from_state,
        to_state=target_state,
        sequence=sequence,
        declared_at=request.declared_at,
    )


def execute_lifecycle(
    ride: Ride,
    requests: Sequence[TransitionRequest],
) -> tuple[RideExecutionStep, ...]:
    """Validate and record an ordered lifecycle execution history."""

    if not requests:
        return ()

    steps: list[RideExecutionStep] = []
    expected_current: RideLifecycleState | None = None
    for sequence, request in enumerate(requests):
        current = RideLifecycleState(request.current_state)
        if expected_current is not None and current != expected_current:
            raise RideExecutionViolation(
                f"transition sequence discontinuity: expected {expected_current.value}, "
                f"got {current.value}"
            )
        step = execute_transition(ride, request, sequence=sequence)
        steps.append(step)
        expected_current = step.to_state
    return tuple(steps)


def execution_steps_hash(steps: Sequence[RideExecutionStep]) -> str:
    """Return a deterministic hash of an ordered execution step sequence."""

    serialized = json.dumps(
        [step.to_canonical_dict() for step in steps],
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(serialized.encode("utf-8")).hexdigest()


def _require_text(field_name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RideExecutionViolation(f"{field_name} must be declared as non-empty text")
    return value
