"""Canonical AfriRide ride execution trace.

The trace records the causal artifacts produced so far. It does not replay,
recompute, mutate ride state, or choose optimization outputs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from ecosystems.afriride.domain.models.canonical_ride import Ride
from ecosystems.afriride.domain.execution.ride_execution_engine import (
    RideExecutionStep,
    execution_steps_hash,
)
from ecosystems.afriride.domain.optimization.deterministic_matching import (
    DriverAssignment,
)
from ecosystems.afriride.domain.optimization.deterministic_pricing import PricePlan
from ecosystems.afriride.domain.optimization.deterministic_routing import RoutePlan
from ecosystems.afriride.domain.state.ride_lifecycle_dag import dag_hash


class RideExecutionTraceViolation(ValueError):
    """Raised when trace artifacts are missing or inconsistent."""


@dataclass(frozen=True)
class RideExecutionTrace:
    """Deterministic causal record for an AfriRide ride proof."""

    ride_id: str
    ride_hash: str
    dag_hash: str
    assignment_hash: str | None = None
    route_hash: str | None = None
    price_hash: str | None = None
    execution_steps_hash: str | None = None

    def to_canonical_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready trace representation."""

        return {
            "assignment_hash": self.assignment_hash,
            "dag_hash": self.dag_hash,
            "execution_steps_hash": self.execution_steps_hash,
            "price_hash": self.price_hash,
            "ride_hash": self.ride_hash,
            "ride_id": self.ride_id,
            "route_hash": self.route_hash,
        }

    def canonical_json(self) -> str:
        """Return stable canonical JSON for replay verification."""

        return json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
        )

    def trace_hash(self) -> str:
        """Return a deterministic content hash for this trace."""

        return sha256(self.canonical_json().encode("utf-8")).hexdigest()


def build_ride_execution_trace(
    ride: Ride,
    *,
    assignment: DriverAssignment | None = None,
    route: RoutePlan | None = None,
    price: PricePlan | None = None,
    execution_steps: tuple[RideExecutionStep, ...] = (),
) -> RideExecutionTrace:
    """Build a deterministic trace from declared ride artifacts."""

    if not isinstance(ride, Ride):
        raise RideExecutionTraceViolation("ride must be a canonical Ride")

    ride_hash = ride.ride_hash()
    _validate_assignment(ride, ride_hash, assignment)
    _validate_route(ride, ride_hash, route)
    _validate_price(ride, ride_hash, assignment, route, price)
    _validate_execution_steps(ride_hash, execution_steps)

    return RideExecutionTrace(
        ride_id=ride.id,
        ride_hash=ride_hash,
        dag_hash=dag_hash(),
        assignment_hash=assignment.assignment_hash() if assignment else None,
        route_hash=route.route_hash() if route else None,
        price_hash=price.price_hash() if price else None,
        execution_steps_hash=(
            execution_steps_hash(execution_steps) if execution_steps else None
        ),
    )


def verify_ride_execution_trace(
    trace: RideExecutionTrace,
    ride: Ride,
    *,
    assignment: DriverAssignment | None = None,
    route: RoutePlan | None = None,
    price: PricePlan | None = None,
    execution_steps: tuple[RideExecutionStep, ...] = (),
) -> bool:
    """Return whether the trace matches the supplied declared artifacts."""

    expected = build_ride_execution_trace(
        ride,
        assignment=assignment,
        route=route,
        price=price,
        execution_steps=execution_steps,
    )
    return trace.trace_hash() == expected.trace_hash()


def _validate_assignment(
    ride: Ride,
    ride_hash: str,
    assignment: DriverAssignment | None,
) -> None:
    if assignment is None:
        return
    if not isinstance(assignment, DriverAssignment):
        raise RideExecutionTraceViolation("assignment must be a DriverAssignment")
    if assignment.ride_id != ride.id:
        raise RideExecutionTraceViolation("assignment ride_id does not match ride")
    if assignment.ride_hash != ride_hash:
        raise RideExecutionTraceViolation("assignment ride_hash does not match ride")


def _validate_route(
    ride: Ride,
    ride_hash: str,
    route: RoutePlan | None,
) -> None:
    if route is None:
        return
    if not isinstance(route, RoutePlan):
        raise RideExecutionTraceViolation("route must be a RoutePlan")
    if route.ride_id != ride.id:
        raise RideExecutionTraceViolation("route ride_id does not match ride")
    if route.ride_hash != ride_hash:
        raise RideExecutionTraceViolation("route ride_hash does not match ride")


def _validate_price(
    ride: Ride,
    ride_hash: str,
    assignment: DriverAssignment | None,
    route: RoutePlan | None,
    price: PricePlan | None,
) -> None:
    if price is None:
        return
    if not isinstance(price, PricePlan):
        raise RideExecutionTraceViolation("price must be a PricePlan")
    if assignment is None:
        raise RideExecutionTraceViolation("price requires assignment artifact")
    if route is None:
        raise RideExecutionTraceViolation("price requires route artifact")
    if price.ride_id != ride.id:
        raise RideExecutionTraceViolation("price ride_id does not match ride")
    if price.ride_hash != ride_hash:
        raise RideExecutionTraceViolation("price ride_hash does not match ride")
    if price.assignment_hash != assignment.assignment_hash():
        raise RideExecutionTraceViolation("price assignment_hash does not match assignment")
    if price.route_hash != route.route_hash():
        raise RideExecutionTraceViolation("price route_hash does not match route")


def _validate_execution_steps(
    ride_hash: str,
    execution_steps: tuple[RideExecutionStep, ...],
) -> None:
    for expected_sequence, step in enumerate(execution_steps):
        if not isinstance(step, RideExecutionStep):
            raise RideExecutionTraceViolation(
                "execution_steps must contain RideExecutionStep values"
            )
        if step.ride_hash != ride_hash:
            raise RideExecutionTraceViolation("execution step ride_hash does not match ride")
        if step.sequence != expected_sequence:
            raise RideExecutionTraceViolation("execution step sequence is not canonical")
