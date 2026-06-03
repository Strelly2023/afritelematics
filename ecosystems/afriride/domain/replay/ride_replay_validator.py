"""Replay validator for AfriRide domain proof artifacts.

Replay is the judgment layer. It recomputes declared deterministic artifacts and
compares them with the causal trace. It does not mutate rides, emit events,
advance lifecycle state, or choose undeclared inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from ecosystems.afriride.domain.execution.ride_execution_engine import (
    RideExecutionStep,
    execution_steps_hash,
)
from ecosystems.afriride.domain.models.canonical_ride import Ride
from ecosystems.afriride.domain.optimization.deterministic_matching import (
    match_driver,
)
from ecosystems.afriride.domain.optimization.deterministic_pricing import (
    PricingConfig,
    compute_price,
)
from ecosystems.afriride.domain.optimization.deterministic_routing import compute_route
from ecosystems.afriride.domain.state.ride_lifecycle_dag import dag_hash
from ecosystems.afriride.domain.trace.ride_execution_trace import (
    RideExecutionTrace,
    build_ride_execution_trace,
)


class RideReplayViolation(ValueError):
    """Raised when replay cannot reconstruct the traced execution."""


@dataclass(frozen=True)
class RideReplayReport:
    """Replay judgment for a traced AfriRide execution."""

    replay_valid: bool
    ride_hash_match: bool
    dag_hash_match: bool
    assignment_hash_match: bool
    route_hash_match: bool
    price_hash_match: bool
    execution_steps_hash_match: bool
    original_trace_hash: str
    replayed_trace_hash: str

    def assert_valid(self) -> "RideReplayReport":
        """Fail closed if replay did not reconstruct the original trace."""

        if not self.replay_valid:
            raise RideReplayViolation("AfriRide replay validation failed")
        return self


def replay_ride_execution(
    trace: RideExecutionTrace,
    ride: Ride,
    *,
    drivers: Sequence[Mapping[str, Any]] | None = None,
    map_graph: Mapping[str, Any] | None = None,
    pricing_config: PricingConfig | None = None,
    execution_steps: Sequence[RideExecutionStep] = (),
    allow_cross_partition: bool = False,
) -> RideReplayReport:
    """Recompute deterministic artifacts and compare them with a trace."""

    if not isinstance(trace, RideExecutionTrace):
        raise RideReplayViolation("trace must be a RideExecutionTrace")
    if not isinstance(ride, Ride):
        raise RideReplayViolation("ride must be a canonical Ride")

    assignment = None
    if trace.assignment_hash is not None:
        if drivers is None:
            raise RideReplayViolation("drivers are required to replay assignment")
        assignment = match_driver(
            ride,
            drivers,
            allow_cross_partition=allow_cross_partition,
        )
        if assignment is None:
            raise RideReplayViolation("replay could not reconstruct assignment")

    route = None
    if trace.route_hash is not None:
        if map_graph is None:
            raise RideReplayViolation("map_graph is required to replay route")
        route = compute_route(ride, map_graph)

    price = None
    if trace.price_hash is not None:
        if assignment is None:
            raise RideReplayViolation("assignment is required to replay price")
        if route is None:
            raise RideReplayViolation("route is required to replay price")
        if pricing_config is None:
            raise RideReplayViolation("pricing_config is required to replay price")
        price = compute_price(ride, assignment, route, pricing_config)

    if trace.execution_steps_hash is not None:
        if not execution_steps:
            raise RideReplayViolation("execution_steps are required to replay lifecycle")
        _validate_execution_steps(ride, execution_steps)

    replayed = build_ride_execution_trace(
        ride,
        assignment=assignment,
        route=route,
        price=price,
        execution_steps=tuple(execution_steps),
    )

    ride_hash_match = trace.ride_hash == replayed.ride_hash
    dag_hash_match = trace.dag_hash == dag_hash() == replayed.dag_hash
    assignment_hash_match = trace.assignment_hash == replayed.assignment_hash
    route_hash_match = trace.route_hash == replayed.route_hash
    price_hash_match = trace.price_hash == replayed.price_hash
    execution_steps_hash_match = (
        trace.execution_steps_hash == replayed.execution_steps_hash
    )
    original_trace_hash = trace.trace_hash()
    replayed_trace_hash = replayed.trace_hash()

    return RideReplayReport(
        replay_valid=all(
            (
                ride_hash_match,
                dag_hash_match,
                assignment_hash_match,
                route_hash_match,
                price_hash_match,
                execution_steps_hash_match,
                original_trace_hash == replayed_trace_hash,
            )
        ),
        ride_hash_match=ride_hash_match,
        dag_hash_match=dag_hash_match,
        assignment_hash_match=assignment_hash_match,
        route_hash_match=route_hash_match,
        price_hash_match=price_hash_match,
        execution_steps_hash_match=execution_steps_hash_match,
        original_trace_hash=original_trace_hash,
        replayed_trace_hash=replayed_trace_hash,
    )


def validate_ride_replay(
    trace: RideExecutionTrace,
    ride: Ride,
    *,
    drivers: Sequence[Mapping[str, Any]] | None = None,
    map_graph: Mapping[str, Any] | None = None,
    pricing_config: PricingConfig | None = None,
    execution_steps: Sequence[RideExecutionStep] = (),
    allow_cross_partition: bool = False,
) -> RideReplayReport:
    """Replay and raise if the trace cannot be reconstructed exactly."""

    return replay_ride_execution(
        trace,
        ride,
        drivers=drivers,
        map_graph=map_graph,
        pricing_config=pricing_config,
        execution_steps=execution_steps,
        allow_cross_partition=allow_cross_partition,
    ).assert_valid()


def _validate_execution_steps(
    ride: Ride,
    execution_steps: Sequence[RideExecutionStep],
) -> None:
    for expected_sequence, step in enumerate(execution_steps):
        if not isinstance(step, RideExecutionStep):
            raise RideReplayViolation(
                "execution_steps must contain RideExecutionStep values"
            )
        if step.ride_hash != ride.ride_hash():
            raise RideReplayViolation("execution step ride_hash does not match ride")
        if step.sequence != expected_sequence:
            raise RideReplayViolation("execution step sequence is not canonical")
    if execution_steps_hash(tuple(execution_steps)) is None:
        raise RideReplayViolation("execution step hash could not be reconstructed")
