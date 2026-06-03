"""HTTP exposure for AfriRide replay-governed proof core.

These endpoints are stateless wrappers around domain primitives. They declare
inputs, call deterministic core functions, and return artifacts; they do not
persist state or define execution truth.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ecosystems.afriride.domain.execution.ride_execution_engine import (
    RideExecutionStep,
    TransitionRequest,
    execute_lifecycle,
    execute_transition,
)
from ecosystems.afriride.domain.models.canonical_ride import Ride
from ecosystems.afriride.domain.optimization.deterministic_matching import (
    DriverAssignment,
    match_driver,
)
from ecosystems.afriride.domain.optimization.deterministic_pricing import (
    PricePlan,
    PricingConfig,
    compute_price,
)
from ecosystems.afriride.domain.optimization.deterministic_routing import (
    RoutePlan,
    compute_route,
)
from ecosystems.afriride.domain.replay.ride_replay_validator import (
    RideReplayViolation,
    replay_ride_execution,
)
from ecosystems.afriride.domain.trace.ride_execution_trace import (
    RideExecutionTrace,
    build_ride_execution_trace,
)


router = APIRouter(prefix="/proof", tags=["afriride-proof"])


@router.post("/rides")
def declare_ride(payload: dict[str, Any]) -> dict[str, Any]:
    """Declare a canonical ride input and return its deterministic identity."""

    try:
        ride = _ride_from_payload(payload)
        return {
            "canonical_ride": ride.to_canonical_dict(),
            "ride_hash": ride.ride_hash(),
        }
    except Exception as exc:
        raise _bad_request(exc) from exc


@router.post("/rides/{ride_hash}/optimize")
def optimize_ride(ride_hash: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Compute deterministic matching, routing, and pricing artifacts."""

    try:
        ride = _ride_from_payload(payload["ride"])
        _assert_ride_hash(ride, ride_hash)
        assignment = match_driver(
            ride,
            payload.get("drivers", ()),
            allow_cross_partition=bool(payload.get("allow_cross_partition", False)),
        )
        if assignment is None:
            raise ValueError("No admissible driver assignment")
        route = compute_route(ride, payload["map_graph"])
        price = compute_price(
            ride,
            assignment,
            route,
            _pricing_config_from_payload(payload["pricing_config"]),
        )
        return {
            "assignment": assignment.to_canonical_dict(),
            "assignment_hash": assignment.assignment_hash(),
            "price_hash": price.price_hash(),
            "price_plan": price.to_canonical_dict(),
            "route_hash": route.route_hash(),
            "route_plan": route.to_canonical_dict(),
        }
    except Exception as exc:
        raise _bad_request(exc) from exc


@router.post("/rides/{ride_hash}/transition")
def execute_ride_transition(ride_hash: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Validate one explicit lifecycle transition and return an execution step."""

    try:
        ride = _ride_from_payload(payload["ride"])
        _assert_ride_hash(ride, ride_hash)
        step = execute_transition(
            ride,
            _transition_request_from_payload(payload, ride_hash),
            sequence=int(payload.get("sequence", 0)),
        )
        return {
            "execution_step": step.to_canonical_dict(),
            "step_hash": step.step_hash(),
        }
    except Exception as exc:
        raise _bad_request(exc) from exc


@router.post("/rides/{ride_hash}/trace")
def build_trace(ride_hash: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic causal trace from declared inputs."""

    try:
        ride = _ride_from_payload(payload["ride"])
        _assert_ride_hash(ride, ride_hash)
        assignment, route, price = _optional_optimization_artifacts(ride, payload)
        steps = _execution_steps_from_payload(ride, payload.get("execution_requests", ()))
        trace = build_ride_execution_trace(
            ride,
            assignment=assignment,
            route=route,
            price=price,
            execution_steps=steps,
        )
        return {
            "trace": trace.to_canonical_dict(),
            "trace_hash": trace.trace_hash(),
        }
    except Exception as exc:
        raise _bad_request(exc) from exc


@router.post("/replay")
def replay_trace(payload: dict[str, Any]) -> dict[str, Any]:
    """Replay declared artifacts and report whether truth reconstructs."""

    try:
        ride = _ride_from_payload(payload["ride"])
        steps = _execution_steps_from_payload(ride, payload.get("execution_requests", ()))
        trace = _trace_from_payload(payload["trace"])
        report = replay_ride_execution(
            trace,
            ride,
            drivers=payload.get("drivers"),
            map_graph=payload.get("map_graph"),
            pricing_config=(
                _pricing_config_from_payload(payload["pricing_config"])
                if "pricing_config" in payload
                else None
            ),
            execution_steps=steps,
            allow_cross_partition=bool(payload.get("allow_cross_partition", False)),
        )
        return {
            "assignment_hash_match": report.assignment_hash_match,
            "dag_hash_match": report.dag_hash_match,
            "execution_steps_hash_match": report.execution_steps_hash_match,
            "original_trace_hash": report.original_trace_hash,
            "price_hash_match": report.price_hash_match,
            "replay_valid": report.replay_valid,
            "replayed_trace_hash": report.replayed_trace_hash,
            "ride_hash_match": report.ride_hash_match,
            "route_hash_match": report.route_hash_match,
        }
    except RideReplayViolation as exc:
        return {
            "error": str(exc),
            "replay_valid": False,
        }
    except Exception as exc:
        raise _bad_request(exc) from exc


@router.post("/audit")
def build_audit_report(payload: dict[str, Any]) -> dict[str, Any]:
    """Build a read-only deterministic audit report from declared inputs."""

    try:
        ride = _ride_from_payload(payload["ride"])
        assignment = match_driver(
            ride,
            payload.get("drivers", ()),
            allow_cross_partition=bool(payload.get("allow_cross_partition", False)),
        )
        if assignment is None:
            raise ValueError("No admissible driver assignment")
        route = compute_route(ride, payload["map_graph"])
        price = compute_price(
            ride,
            assignment,
            route,
            _pricing_config_from_payload(payload["pricing_config"]),
        )
        steps = _execution_steps_from_payload(ride, payload.get("execution_requests", ()))
        trace = build_ride_execution_trace(
            ride,
            assignment=assignment,
            route=route,
            price=price,
            execution_steps=steps,
        )
        replay_report = replay_ride_execution(
            trace,
            ride,
            drivers=payload.get("drivers"),
            map_graph=payload.get("map_graph"),
            pricing_config=_pricing_config_from_payload(payload["pricing_config"]),
            execution_steps=steps,
            allow_cross_partition=bool(payload.get("allow_cross_partition", False)),
        )
        return {
            "assignment": assignment.to_canonical_dict(),
            "assignment_hash": assignment.assignment_hash(),
            "canonical_ride": ride.to_canonical_dict(),
            "execution_steps": [
                {
                    "step": step.to_canonical_dict(),
                    "step_hash": step.step_hash(),
                }
                for step in steps
            ],
            "price_hash": price.price_hash(),
            "price_plan": price.to_canonical_dict(),
            "replay": _replay_report_dict(replay_report),
            "ride_hash": ride.ride_hash(),
            "route_hash": route.route_hash(),
            "route_plan": route.to_canonical_dict(),
            "trace": trace.to_canonical_dict(),
            "trace_hash": trace.trace_hash(),
        }
    except Exception as exc:
        raise _bad_request(exc) from exc


@router.post("/replay-report")
def build_replay_report(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a read-only replay report for a supplied trace and inputs."""

    result = replay_trace(payload)
    if result.get("replay_valid") is False and "error" in result:
        return result
    return {
        "replay": result,
        "replay_valid": result["replay_valid"],
    }


@router.post("/explain")
def explain_audit_report(payload: dict[str, Any]) -> dict[str, Any]:
    """Return deterministic explanations derived from the audit report."""

    audit = build_audit_report(payload)
    assignment = audit["assignment"]
    route = audit["route_plan"]
    price = audit["price_plan"]
    replay_valid = audit["replay"]["replay_valid"]
    return {
        "assignment_reason": (
            f"Driver {assignment['driver_id']} selected by deterministic score "
            f"{assignment['score']} with locality {assignment['locality']}."
        ),
        "price_reason": (
            "Price computed as base fare plus distance cost plus time cost "
            f"for total {price['total_cost']} {price['currency']}."
        ),
        "replay_reason": (
            "Replay reconstructed all traced artifacts."
            if replay_valid
            else "Replay failed to reconstruct one or more traced artifacts."
        ),
        "replay_valid": replay_valid,
        "route_reason": (
            "Route selected by deterministic shortest path with "
            "distance, estimated time, then path as tie-breakers."
        ),
        "summary": (
            f"Ride {audit['ride_hash']} assigned to {assignment['driver_id']} "
            f"over path {route['path']} with replay_valid={replay_valid}."
        ),
    }


def _optional_optimization_artifacts(
    ride: Ride,
    payload: dict[str, Any],
) -> tuple[DriverAssignment | None, RoutePlan | None, PricePlan | None]:
    assignment = None
    if "drivers" in payload:
        assignment = match_driver(
            ride,
            payload["drivers"],
            allow_cross_partition=bool(payload.get("allow_cross_partition", False)),
        )
        if assignment is None:
            raise ValueError("No admissible driver assignment")

    route = compute_route(ride, payload["map_graph"]) if "map_graph" in payload else None

    price = None
    if "pricing_config" in payload:
        if assignment is None:
            raise ValueError("Pricing requires matching inputs")
        if route is None:
            raise ValueError("Pricing requires routing inputs")
        price = compute_price(
            ride,
            assignment,
            route,
            _pricing_config_from_payload(payload["pricing_config"]),
        )
    return assignment, route, price


def _ride_from_payload(payload: dict[str, Any]) -> Ride:
    return Ride(
        id=payload["id"],
        passenger_id=payload["passenger_id"],
        pickup_location=payload["pickup_location"],
        dropoff_location=payload["dropoff_location"],
        requested_at=payload["requested_at"],
        assigned_driver=payload.get("assigned_driver"),
        route_plan=payload.get("route_plan"),
        price_plan=payload.get("price_plan"),
        status=payload.get("status", "REQUESTED"),
    )


def _pricing_config_from_payload(payload: dict[str, Any]) -> PricingConfig:
    return PricingConfig(
        base_fare=payload["base_fare"],
        per_distance_rate=payload["per_distance_rate"],
        per_time_rate=payload["per_time_rate"],
        currency=payload["currency"],
    )


def _transition_request_from_payload(
    payload: dict[str, Any],
    ride_hash: str,
) -> TransitionRequest:
    return TransitionRequest(
        ride_hash=ride_hash,
        current_state=payload["current_state"],
        target_state=payload["target_state"],
        declared_at=payload.get("declared_at"),
    )


def _execution_steps_from_payload(
    ride: Ride,
    requests: list[dict[str, Any]] | tuple[dict[str, Any], ...],
) -> tuple[RideExecutionStep, ...]:
    return execute_lifecycle(
        ride,
        tuple(
            _transition_request_from_payload(request, ride.ride_hash())
            for request in requests
        ),
    )


def _trace_from_payload(payload: dict[str, Any]) -> RideExecutionTrace:
    return RideExecutionTrace(
        ride_id=payload["ride_id"],
        ride_hash=payload["ride_hash"],
        dag_hash=payload["dag_hash"],
        assignment_hash=payload.get("assignment_hash"),
        route_hash=payload.get("route_hash"),
        price_hash=payload.get("price_hash"),
        execution_steps_hash=payload.get("execution_steps_hash"),
    )


def _assert_ride_hash(ride: Ride, ride_hash: str) -> None:
    if ride.ride_hash() != ride_hash:
        raise ValueError("ride_hash does not match canonical ride")


def _bad_request(exc: Exception) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


def _replay_report_dict(report: Any) -> dict[str, Any]:
    return {
        "assignment_hash_match": report.assignment_hash_match,
        "dag_hash_match": report.dag_hash_match,
        "execution_steps_hash_match": report.execution_steps_hash_match,
        "original_trace_hash": report.original_trace_hash,
        "price_hash_match": report.price_hash_match,
        "replay_valid": report.replay_valid,
        "replayed_trace_hash": report.replayed_trace_hash,
        "ride_hash_match": report.ride_hash_match,
        "route_hash_match": report.route_hash_match,
    }
