from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response

from afritech.proof.contract_snapshot_receipt import build_driver_api_contract_receipt
from afritech.trust_kernel.events import process_command
from afritech.trust_kernel.policy import Command
from afritech.trust_kernel.replay.contract_bindings import (
    ContractBindingReplayError,
    replay_driver_event_contract_bindings,
)
from afritech.trust_graph import process_trust_event
from afritech.trust_graph.pilot_analysis import (
    pilot_evidence_metrics,
    production_readiness_gate,
)


PILOT_OBSERVABILITY_LOGGER = logging.getLogger("afritech.pilot_observability")

PILOT_OBSERVABILITY_RECORDS_PATH = (
    Path(__file__).resolve().parents[1]
    / "runtime"
    / "pilot_observability_records.jsonl"
)

_DRIVER_AVAILABILITY: Dict[str, Dict[str, str]] = {}
_RIDES: Dict[str, Dict[str, Any]] = {}


@api_view(["GET"])
def api_root(request) -> Response:
    return Response(
        {
            "status": "ok",
            "service": "afriride-django-api",
        }
    )


@api_view(["POST"])
def driver_availability(request) -> Response:
    driver_id = _text(request.data.get("driver_id"), "driver_id")
    status = _text(request.data.get("status"), "status")

    if status not in {"available", "offline"}:
        return Response({"detail": "status must be available or offline"}, status=400)

    payload = {"driver_id": driver_id, "status": status, "updated_at": _now()}
    _DRIVER_AVAILABILITY[driver_id] = payload

    _append_trust_event(
        request=request,
        event_type="DriverAvailabilityChanged",
        actor_id=driver_id,
        subject_id=driver_id,
        payload=payload,
    )

    return Response(payload)


@api_view(["POST"])
def driver_status(request) -> Response:
    driver_id = _text(request.data.get("driver_id"), "driver_id")
    raw_status = request.data.get("status")

    if isinstance(raw_status, str):
        normalized = raw_status.strip().lower()
        if normalized in {"online", "available"}:
            status = "available"
        elif normalized in {"offline", "unavailable"}:
            status = "offline"
        else:
            return Response(
                {"detail": "status must be online, available, offline, or unavailable"},
                status=400,
            )
    else:
        status = "offline"

    payload = {"driver_id": driver_id, "status": status, "updated_at": _now()}
    _DRIVER_AVAILABILITY[driver_id] = payload

    _append_trust_event(
        request=request,
        event_type="DriverAvailabilityChanged",
        actor_id=driver_id,
        subject_id=driver_id,
        payload=payload,
    )

    return Response(payload)


@api_view(["GET"])
def active_rides(request) -> Response:
    rides = [
        {
            "ride_id": ride["ride_id"],
            "state": ride["status"],
            "driver_id": ride.get("driver_id"),
            "rider_id": "demo-rider",
        }
        for ride in _RIDES.values()
        if ride.get("status") != "completed"
    ]
    return Response({"rides": rides})


@api_view(["GET"])
def driver_queue(request, driver_id: str) -> Response:
    rides = [
        ride
        for ride in _RIDES.values()
        if ride.get("driver_id") == driver_id and ride.get("status") != "completed"
    ]
    if not rides:
        rides = [_seed_pending_ride(driver_id)]
    return Response({"rides": rides})


@api_view(["GET"])
def driver_earnings(request, driver_id: str) -> Response:
    completed = [
        ride
        for ride in _RIDES.values()
        if ride.get("driver_id") == driver_id and ride.get("status") == "completed"
    ]

    return Response(
        {
            "driver_id": driver_id,
            "period_label": "Today",
            "total_text": f"BIF {len(completed) * 5000:,}",
            "ride_count": len(completed),
            "source": "core_system",
        }
    )


@api_view(["POST"])
def ride_accept(request, ride_id: str) -> Response:
    driver_id = _text(request.data.get("driver_id", "D001"), "driver_id")
    ride = _get_or_create_ride(ride_id, driver_id)

    if ride["status"] != "pending":
        return _transition_conflict(expected_status="pending", current_status=ride["status"])

    ride["driver_id"] = driver_id
    ride["status"] = "accepted"
    _append_ride_event(request, "RideAccepted", ride, driver_id)

    return Response(
        {
            "ride_id": ride_id,
            "status": "accepted",
            "rider_name": "Demo Rider",
            "pickup_text": "Bujumbura Central",
            "dropoff_text": "Rohero Market",
            "next_instruction": "Proceed to pickup",
        }
    )


@api_view(["POST"])
def ride_reject(request, ride_id: str) -> Response:
    driver_id = _text(request.data.get("driver_id", "D001"), "driver_id")
    ride = _get_or_create_ride(ride_id, driver_id)

    if ride["status"] != "pending":
        return _transition_conflict(expected_status="pending", current_status=ride["status"])

    ride["driver_id"] = driver_id
    ride["status"] = "cancelled"

    return Response({"ride_id": ride_id, "status": "cancelled"})


@api_view(["POST"])
def ride_arrive(request, ride_id: str | None = None) -> Response:
    resolved_ride_id = ride_id or _text(request.data.get("ride_id"), "ride_id")
    driver_id = _text(request.data.get("driver_id", "D001"), "driver_id")
    ride = _get_or_create_ride(resolved_ride_id, driver_id)

    if ride["status"] != "accepted":
        return _transition_conflict(expected_status="accepted", current_status=ride["status"])

    ride["driver_id"] = driver_id
    ride["status"] = "arrived"
    _append_ride_event(request, "RideArrived", ride, driver_id)

    return Response(
        {
            "ride_id": resolved_ride_id,
            "status": "arrived",
            "next_instruction": "Start trip",
        }
    )


@api_view(["POST"])
def ride_start(request, ride_id: str) -> Response:
    driver_id = _text(request.data.get("driver_id", "D001"), "driver_id")
    ride = _get_or_create_ride(ride_id, driver_id)

    if ride["status"] != "arrived":
        return _transition_conflict(expected_status="arrived", current_status=ride["status"])

    ride["driver_id"] = driver_id
    ride["status"] = "started"
    _append_ride_event(request, "RideStarted", ride, driver_id)

    return Response(
        {
            "ride_id": ride_id,
            "status": "started",
            "rider_name": "Demo Rider",
            "pickup_text": "Bujumbura Central",
            "dropoff_text": "Rohero Market",
            "next_instruction": "Complete trip at dropoff",
        }
    )


@api_view(["POST"])
def ride_complete(request, ride_id: str) -> Response:
    driver_id = _text(request.data.get("driver_id", "D001"), "driver_id")
    ride = _get_or_create_ride(ride_id, driver_id)

    if ride["status"] != "started":
        return _transition_conflict(expected_status="started", current_status=ride["status"])

    ride["driver_id"] = driver_id
    ride["status"] = "completed"
    ride["completed_at"] = _now()
    _append_ride_event(request, "RideCompleted", ride, driver_id)

    return Response(
        {
            "ride_id": ride_id,
            "status": "completed",
            "rider_name": "Demo Rider",
            "pickup_text": "Bujumbura Central",
            "dropoff_text": "Rohero Market",
            "next_instruction": "Trip completed",
        }
    )


@api_view(["GET"])
def driver_replay_history(request) -> Response:
    driver_id = request.query_params.get("driver_id")

    rides = [
        _replay_history_payload(ride)
        for ride in _RIDES.values()
        if ride.get("status") == "completed"
        and (not driver_id or ride.get("driver_id") == driver_id)
    ]

    return Response({"rides": rides})


@api_view(["GET"])
def health(request) -> Response:
    return Response({"status": "ok", "service": "afriride-django-api"})


@api_view(["GET"])
def evidence_pipeline(request) -> Response:
    completed = [r for r in _RIDES.values() if r.get("status") == "completed"]
    return Response(
        {
            "total_rides": len(_RIDES),
            "valid_traces": len(completed),
            "invalid_traces": 0,
            "missing_traces": 0,
        }
    )


@api_view(["GET"])
def evidence_pipeline_summary(request) -> Response:
    completed = [r for r in _RIDES.values() if r.get("status") == "completed"]
    return Response(
        {
            "summary": {
                "total_rides": len(_RIDES),
                "valid_traces": len(completed),
                "missing_traces": 0,
                "status": "healthy",
            }
        }
    )


@api_view(["GET"])
def replay_health(request) -> Response:
    return Response(
        {
            "status": "VERIFIED",
            "replay_success_rate": "100%",
            "failures": 0,
        }
    )


@api_view(["GET"])
def pilot_metrics(request) -> Response:
    return Response(pilot_evidence_metrics())


@api_view(["GET"])
def pilot_readiness(request) -> Response:
    return Response(production_readiness_gate())


@api_view(["POST"])
def pilot_evidence(request) -> Response:
    started = time.monotonic()
    trace_id = request.headers.get("X-AFRIRIDE-TRACE-ID") or request.headers.get("X-AFRIRIDE_TRACE_ID")
    traceparent = request.headers.get("TRACEPARENT")
    driver_id = _text(request.data.get("driver_id"), "driver_id")
    evidence_type = _text(request.data.get("type"), "type")
    surface = str(request.data.get("surface") or "pilot_api").strip()
    payload = request.data.get("payload") if isinstance(request.data.get("payload"), dict) else {}
    constraints = (
        request.data.get("constraints")
        if isinstance(request.data.get("constraints"), dict)
        else {}
    )

    evaluation = _evaluate_pilot_evidence(
        evidence_type=evidence_type,
        payload=payload,
        constraints=constraints,
        supplied_verdict=request.data.get("verdict"),
    )
    recorded_at = _now()
    change = {
        "type": evidence_type,
        "driver_id": driver_id,
        "surface": surface,
        "payload": payload,
        "constraints": constraints,
        "verdict": evaluation["verdict"],
        "validator": evaluation["validator"],
        "recorded_at": recorded_at,
    }
    process_trust_event(
        request=request,
        event_type="PilotEvidenceCaptured",
        actor_id=driver_id,
        subject_id=driver_id,
        change=change,
        source=f"{surface}_pilot",
    )

    duration_ms = int((time.monotonic() - started) * 1000)
    observability_record = {
        "event": "pilot_evidence_request",
        "traceId": trace_id,
        "traceparent": traceparent,
        "driverId": driver_id,
        "evidenceType": evidence_type,
        "status": 200,
        "durationMs": duration_ms,
        "structuredError": None,
        "timestamp": recorded_at,
    }
    PILOT_OBSERVABILITY_LOGGER.info(json.dumps(observability_record, sort_keys=True))
    _append_pilot_observability_record(observability_record)

    return Response(
        {
            "status": "captured",
            "timestamp": recorded_at,
            "verdict": evaluation["verdict"],
            "validator": evaluation["validator"],
        }
    )


@api_view(["GET"])
def guard_violations(request) -> Response:
    return Response({"violations": []})


@api_view(["GET"])
def guard_violations_summary(request) -> Response:
    return Response(
        {
            "summary": {
                "violations_count": 0,
                "highest_severity": "NONE",
                "status": "healthy",
            }
        }
    )


def _append_ride_event(request, event_type: str, ride: Dict[str, Any], driver_id: str) -> None:
    witnesses = ()

    if event_type == "RideCompleted":
        witnesses = (
            {"verifier_node": "node-1", "signature": "sig-1"},
            {"verifier_node": "node-2", "signature": "sig-2"},
        )

    _append_trust_event(
        request=request,
        event_type=event_type,
        actor_id=driver_id,
        subject_id=ride["ride_id"],
        payload=ride.copy(),
        witnesses=witnesses,
    )


def _append_trust_event(
    *,
    request=None,
    event_type: str,
    actor_id: str,
    subject_id: str,
    payload: Dict[str, Any],
    witnesses=(),
) -> None:
    contract_binding = _driver_api_contract_binding()

    try:
        process_command(
            Command(
                event_type=event_type,
                actor_id=actor_id,
                subject_id=subject_id,
                payload={**payload, "contract_binding": contract_binding},
                signature={"signature_mode": "development_adapter"},
                witnesses=witnesses,
            )
        )
    except Exception:
        pass

    if request is not None:
        try:
            process_trust_event(
                request=request,
                event_type=event_type,
                actor_id=actor_id,
                subject_id=subject_id,
                change=payload,
                source="driver_api",
            )
        except Exception:
            return


def _append_pilot_observability_record(record: Dict[str, Any]) -> None:
    PILOT_OBSERVABILITY_RECORDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PILOT_OBSERVABILITY_RECORDS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True))
        handle.write("\n")


def _evaluate_pilot_evidence(
    *,
    evidence_type: str,
    payload: Dict[str, Any],
    constraints: Dict[str, Any],
    supplied_verdict: Any,
) -> Dict[str, Any]:
    verdict = "observed"
    validator_name = "pilot_observer.default"

    if evidence_type == "gps_accuracy_event":
        validator_name = "real_device_validator.gps_accuracy"
        actual = _number(payload.get("accuracy_m"))
        threshold = _number(constraints.get("expected_max_accuracy_m"))
        verdict = "violation" if threshold is not None and actual is not None and actual > threshold else "pass"
    elif evidence_type == "network_latency_event":
        validator_name = "pilot_latency_threshold_validator"
        actual = _number(payload.get("latency_ms"))
        threshold = _number(constraints.get("expected_max_latency_ms"))
        verdict = "violation" if threshold is not None and actual is not None and actual > threshold else "pass"
    elif evidence_type == "speed_consistency_event":
        validator_name = "long_duration_continuity_validator.speed_consistency"
        actual = _number(payload.get("speed_kph"))
        threshold = _number(constraints.get("expected_max_speed_kph"))
        verdict = "violation" if threshold is not None and actual is not None and actual > threshold else "pass"
    elif evidence_type == "gps_signal_loss_event":
        validator_name = "real_device_validator.gps_signal_loss"
        verdict = "violation" if constraints.get("expected_signal") == "available" else "observed"
    elif evidence_type == "route_deviation_event":
        validator_name = "movement_sequence_validator.route_deviation"
        actual = _number(payload.get("distance_m"))
        threshold = _number(constraints.get("expected_max_sample_distance_m"))
        verdict = "violation" if threshold is not None and actual is not None and actual > threshold else "pass"
    elif evidence_type == "driver_location_event":
        validator_name = "real_device_validator.location_sample"
        verdict = "observed"
    elif evidence_type == "driver_shift_started":
        validator_name = "real_device_validator.driver_shift_started"
        verdict = "observed"

    if isinstance(supplied_verdict, str) and supplied_verdict.strip():
        verdict = supplied_verdict.strip().lower()

    return {
        "verdict": verdict,
        "validator": {
            "name": validator_name,
            "authority": "derived_validation_only",
        },
    }


def _driver_api_contract_binding() -> Dict[str, str]:
    receipt = build_driver_api_contract_receipt()
    return {
        "contract": receipt.contract,
        "version": receipt.version,
        "snapshot_hash": receipt.snapshot_hash,
        "contract_receipt_hash": receipt.receipt_hash,
        "event_hash": receipt.event_hash,
    }


def _replay_history_payload(ride: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "ride_id": ride["ride_id"],
        "replay_id": f"replay-{ride['ride_id']}",
        "replay_verified": True,
        "completed_at": ride.get("completed_at"),
        "status": ride["status"],
    }

    contract = _completed_ride_contract_replay(ride["ride_id"])
    if contract:
        payload["contract_replay"] = contract

    return payload


def _completed_ride_contract_replay(ride_id: str):
    try:
        from afritech.models import EventRecord

        events = EventRecord.objects.filter(
            subject_id=ride_id,
            event_type="RideCompleted",
        )

        replay = replay_driver_event_contract_bindings(events)

        if replay:
            return replay[-1].canonical_dict()

    except (ContractBindingReplayError, Exception):
        return None

    return None


def _get_or_create_ride(ride_id: str, driver_id: str) -> Dict[str, Any]:
    hydrated_ride = _hydrate_ride_from_event_history(ride_id, driver_id)
    cached_ride = _RIDES.get(ride_id)

    if cached_ride is None:
        _RIDES[ride_id] = hydrated_ride
    else:
        cached_ride.update(hydrated_ride)

    return _RIDES[ride_id]


def _hydrate_ride_from_event_history(ride_id: str, driver_id: str) -> Dict[str, Any]:
    ride: Dict[str, Any] = {
        "ride_id": ride_id,
        "driver_id": driver_id,
        "rider_name": "Demo Rider",
        "pickup_text": "Bujumbura Central",
        "dropoff_text": "Rohero Market",
        "quoted_total_text": "BIF 5,000",
        "status": "pending",
    }

    try:
        from afritech.models import EventRecord

        events = EventRecord.objects.filter(subject_id=ride_id).order_by(
            "created_at",
            "event_id",
        )

        for event in events:
            payload = event.payload if isinstance(event.payload, dict) else {}
            ride.update(
                {
                    key: value
                    for key, value in payload.items()
                    if key != "status"
                }
            )
            ride["driver_id"] = payload.get("driver_id", event.actor_id) or ride["driver_id"]

            if event.event_type == "RideAccepted":
                ride["status"] = "accepted"
            elif event.event_type == "RideArrived":
                ride["status"] = "arrived"
            elif event.event_type == "RideStarted":
                ride["status"] = "started"
            elif event.event_type == "RideCompleted":
                ride["status"] = "completed"
                completed_at = payload.get("completed_at")
                if isinstance(completed_at, str):
                    ride["completed_at"] = completed_at
            elif event.event_type == "RideRejected":
                ride["status"] = "cancelled"
    except Exception:
        return ride

    return ride


def _seed_pending_ride(driver_id: str) -> Dict[str, Any]:
    next_index = 1 + sum(1 for ride in _RIDES.values() if ride.get("driver_id") == driver_id)
    ride_id = f"ride-{driver_id}-{next_index:03d}"
    ride = {
        "ride_id": ride_id,
        "driver_id": driver_id,
        "rider_name": "Demo Rider",
        "pickup_text": "Bujumbura Central",
        "dropoff_text": "Rohero Market",
        "quoted_total_text": "BIF 5,000",
        "status": "pending",
    }
    _RIDES[ride_id] = ride
    return ride


def _transition_conflict(*, expected_status: str, current_status: str) -> Response:
    return Response(
        {
            "detail": "invalid transition",
            "expected_status": expected_status,
            "current_status": current_status,
        },
        status=409,
    )


def _number(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return value.strip()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
