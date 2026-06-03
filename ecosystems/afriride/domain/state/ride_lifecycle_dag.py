"""Canonical AfriRide ride lifecycle DAG.

The DAG defines execution structure only. It does not mutate rides, dispatch
drivers, calculate prices, or choose routes.
"""

from __future__ import annotations

import json
from enum import Enum
from hashlib import sha256
from typing import Any


class RideLifecycleViolation(ValueError):
    """Raised when lifecycle structure or transition input is invalid."""


class RideLifecycleState(str, Enum):
    """Canonical AfriRide execution states."""

    REQUESTED = "REQUESTED"
    MATCHED = "MATCHED"
    DRIVER_ACCEPTED = "DRIVER_ACCEPTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


CANONICAL_RIDE_LIFECYCLE_ORDER: tuple[RideLifecycleState, ...] = (
    RideLifecycleState.REQUESTED,
    RideLifecycleState.MATCHED,
    RideLifecycleState.DRIVER_ACCEPTED,
    RideLifecycleState.IN_PROGRESS,
    RideLifecycleState.COMPLETED,
)

RIDE_LIFECYCLE_TRANSITIONS: dict[
    RideLifecycleState,
    tuple[RideLifecycleState, ...],
] = {
    RideLifecycleState.REQUESTED: (RideLifecycleState.MATCHED,),
    RideLifecycleState.MATCHED: (RideLifecycleState.DRIVER_ACCEPTED,),
    RideLifecycleState.DRIVER_ACCEPTED: (RideLifecycleState.IN_PROGRESS,),
    RideLifecycleState.IN_PROGRESS: (RideLifecycleState.COMPLETED,),
    RideLifecycleState.COMPLETED: (),
}


def canonical_states() -> tuple[RideLifecycleState, ...]:
    """Return the deterministic topological state order."""

    return CANONICAL_RIDE_LIFECYCLE_ORDER


def canonical_edges() -> tuple[tuple[RideLifecycleState, RideLifecycleState], ...]:
    """Return transitions in deterministic DAG order."""

    edges: list[tuple[RideLifecycleState, RideLifecycleState]] = []
    for state in CANONICAL_RIDE_LIFECYCLE_ORDER:
        for target in RIDE_LIFECYCLE_TRANSITIONS[state]:
            edges.append((state, target))
    return tuple(edges)


def next_states(state: RideLifecycleState | str) -> tuple[RideLifecycleState, ...]:
    """Return allowed next states for a lifecycle state."""

    return RIDE_LIFECYCLE_TRANSITIONS[_normalize_state(state)]


def can_transition(
    current_state: RideLifecycleState | str,
    next_state: RideLifecycleState | str,
) -> bool:
    """Return whether a transition exists in the canonical DAG."""

    try:
        current = _normalize_state(current_state)
        target = _normalize_state(next_state)
    except RideLifecycleViolation:
        return False
    return target in RIDE_LIFECYCLE_TRANSITIONS[current]


def assert_transition(
    current_state: RideLifecycleState | str,
    next_state: RideLifecycleState | str,
) -> RideLifecycleState:
    """Validate a transition and return the normalized target state."""

    current = _normalize_state(current_state)
    target = _normalize_state(next_state)
    if target not in RIDE_LIFECYCLE_TRANSITIONS[current]:
        raise RideLifecycleViolation(
            f"Invalid ride lifecycle transition: {current.value} -> {target.value}"
        )
    return target


def as_canonical_dict() -> dict[str, Any]:
    """Return a deterministic JSON-ready DAG representation."""

    return {
        "edges": [
            {"from": source.value, "to": target.value}
            for source, target in canonical_edges()
        ],
        "states": [state.value for state in CANONICAL_RIDE_LIFECYCLE_ORDER],
    }


def canonical_json() -> str:
    """Return stable canonical JSON for lifecycle trace references."""

    return json.dumps(as_canonical_dict(), sort_keys=True, separators=(",", ":"))


def dag_hash() -> str:
    """Return a deterministic content hash for the lifecycle DAG."""

    return sha256(canonical_json().encode("utf-8")).hexdigest()


def validate_lifecycle_dag() -> bool:
    """Validate the static DAG structure."""

    seen = set()
    order_index = {
        state: index for index, state in enumerate(CANONICAL_RIDE_LIFECYCLE_ORDER)
    }
    for state in CANONICAL_RIDE_LIFECYCLE_ORDER:
        if state in seen:
            raise RideLifecycleViolation(f"Duplicate lifecycle state: {state.value}")
        seen.add(state)
        if state not in RIDE_LIFECYCLE_TRANSITIONS:
            raise RideLifecycleViolation(f"Missing transition entry: {state.value}")
        for target in RIDE_LIFECYCLE_TRANSITIONS[state]:
            if target not in order_index:
                raise RideLifecycleViolation(f"Unknown transition target: {target}")
            if order_index[target] <= order_index[state]:
                raise RideLifecycleViolation(
                    f"Non-forward transition: {state.value} -> {target.value}"
                )

    if set(RIDE_LIFECYCLE_TRANSITIONS) != seen:
        raise RideLifecycleViolation("Transition table contains undeclared states")
    return True


def _normalize_state(state: RideLifecycleState | str) -> RideLifecycleState:
    if isinstance(state, RideLifecycleState):
        return state
    try:
        return RideLifecycleState(state)
    except ValueError as exc:
        raise RideLifecycleViolation(f"Unknown ride lifecycle state: {state}") from exc
