"""Mobile pilot end-to-end proof for AfriRide.

Mobile clients submit envelopes. Server-side normalization, deterministic
domain execution, persistent event evidence, and replay validation remain the
authority surfaces.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Callable, Mapping

from afritech.storage.postgres_event_store import PostgresEventStore
from ecosystems.afriride.domain.execution.ride_execution_engine import (
    TransitionRequest,
    execute_lifecycle,
)
from ecosystems.afriride.domain.models.canonical_ride import Ride
from ecosystems.afriride.domain.optimization.deterministic_matching import match_driver
from ecosystems.afriride.domain.optimization.deterministic_pricing import (
    PricingConfig,
    compute_price,
)
from ecosystems.afriride.domain.optimization.deterministic_routing import compute_route
from ecosystems.afriride.domain.replay.ride_replay_validator import validate_ride_replay
from ecosystems.afriride.domain.state.ride_lifecycle_dag import RideLifecycleState
from ecosystems.afriride.domain.trace.ride_execution_trace import build_ride_execution_trace


AUTHORITY_DISCLAIMER = (
    "Mobile clients may observe, request, and submit events. They may not "
    "define identity, fare, match result, replay hash, trip legitimacy, or final truth."
)

REQUIRED_REJECTIONS = (
    "client_timestamp_authority",
    "client_computed_fare_authority",
    "client_computed_driver_match_authority",
    "client_replay_hash_authority",
    "duplicate_mobile_request",
    "spoofed_rider_driver_event",
    "out_of_order_mobile_update",
    "tampered_trip_status",
)

FORBIDDEN_CLIENT_FIELDS = frozenset(
    {
        "authoritative_timestamp",
        "fare",
        "final_truth",
        "match_result",
        "replay_hash",
        "trip_legitimacy",
    }
)


class MobilePilotProofError(ValueError):
    """Raised when mobile pilot proof violates replay-safe admission."""


@dataclass(frozen=True)
class MobileEnvelope:
    envelope_id: str
    client_kind: str
    principal_id: str
    event_type: str
    client_sequence: int
    payload: Mapping[str, Any]
    observed_at: str

    def __post_init__(self) -> None:
        _require_text(self.envelope_id, "envelope_id")
        if self.client_kind not in {"rider", "driver"}:
            raise MobilePilotProofError("client_kind must be rider or driver")
        _require_text(self.principal_id, "principal_id")
        _require_text(self.event_type, "event_type")
        if not isinstance(self.client_sequence, int) or self.client_sequence < 0:
            raise MobilePilotProofError("client_sequence must be non-negative int")
        if not isinstance(self.payload, Mapping):
            raise MobilePilotProofError("payload must be mapping")
        _require_text(self.observed_at, "observed_at")


@dataclass(frozen=True)
class MobilePilotProofReport:
    event_count: int
    persistent_event_hash: str
    ride_hash: str
    assignment_hash: str
    route_hash: str
    price_hash: str
    execution_steps_hash: str
    trip_replay_hash: str
    replayed_trip_hash: str
    eta_seconds: int
    rejected_cases: tuple[str, ...]
    authority_disclaimer: str = AUTHORITY_DISCLAIMER

    @property
    def verified(self) -> bool:
        return (
            self.event_count >= 6
            and self.trip_replay_hash == self.replayed_trip_hash
            and self.rejected_cases == REQUIRED_REJECTIONS
            and self.authority_disclaimer == AUTHORITY_DISCLAIMER
            and all(len(value) == 64 for value in self._hashes())
            and self.eta_seconds > 0
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "assignment_hash": self.assignment_hash,
            "authority_disclaimer": self.authority_disclaimer,
            "eta_seconds": self.eta_seconds,
            "event_count": self.event_count,
            "execution_steps_hash": self.execution_steps_hash,
            "persistent_event_hash": self.persistent_event_hash,
            "price_hash": self.price_hash,
            "rejected_cases": list(self.rejected_cases),
            "replayed_trip_hash": self.replayed_trip_hash,
            "ride_hash": self.ride_hash,
            "route_hash": self.route_hash,
            "schema": "afriride.mobile_pilot_e2e_proof_report.v1",
            "trip_replay_hash": self.trip_replay_hash,
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())

    def _hashes(self) -> tuple[str, ...]:
        return (
            self.persistent_event_hash,
            self.ride_hash,
            self.assignment_hash,
            self.route_hash,
            self.price_hash,
            self.execution_steps_hash,
            self.trip_replay_hash,
            self.replayed_trip_hash,
        )


class MobilePilotAdapter:
    """Controlled mobile envelope adapter."""

    def __init__(self) -> None:
        self._seen_envelopes: set[str] = set()
        self._next_sequence: dict[str, int] = {}

    def normalize(self, envelope: MobileEnvelope) -> dict[str, object]:
        if envelope.envelope_id in self._seen_envelopes:
            raise MobilePilotProofError("duplicate mobile request")
        self._seen_envelopes.add(envelope.envelope_id)

        expected_sequence = self._next_sequence.get(envelope.principal_id, 0)
        if envelope.client_sequence != expected_sequence:
            raise MobilePilotProofError("out-of-order mobile update")
        self._next_sequence[envelope.principal_id] = expected_sequence + 1

        self._reject_client_authority(envelope.payload)
        self._require_principal_consistency(envelope)
        self._reject_tampered_status(envelope)

        return {
            "event_id": f"mobile.{envelope.envelope_id}",
            "payload": {
                "client_kind": envelope.client_kind,
                "event_type": envelope.event_type,
                "observed_at": envelope.observed_at,
                "principal_id": envelope.principal_id,
                "submitted_payload": _canonicalize(envelope.payload),
            },
            "timestamp": f"server-sequence-{envelope.client_sequence:04d}",
            "type": "afriride.mobile.normalized",
        }

    def _reject_client_authority(self, value: Mapping[str, Any]) -> None:
        injected = FORBIDDEN_CLIENT_FIELDS.intersection(value.keys())
        if injected:
            raise MobilePilotProofError(f"mobile client authority field: {sorted(injected)[0]}")
        for nested in value.values():
            if isinstance(nested, Mapping):
                self._reject_client_authority(nested)

    def _require_principal_consistency(self, envelope: MobileEnvelope) -> None:
        rider_id = envelope.payload.get("rider_id")
        driver_id = envelope.payload.get("driver_id")
        if envelope.client_kind == "rider" and rider_id != envelope.principal_id:
            raise MobilePilotProofError("spoofed rider event")
        if envelope.client_kind == "driver" and driver_id != envelope.principal_id:
            raise MobilePilotProofError("spoofed driver event")

    def _reject_tampered_status(self, envelope: MobileEnvelope) -> None:
        status = envelope.payload.get("trip_status")
        if status in {"COMPLETED", "FINAL", "LEGITIMATE"}:
            raise MobilePilotProofError("tampered trip status")


def run_mobile_pilot_e2e_proof() -> MobilePilotProofReport:
    adapter = MobilePilotAdapter()
    store = PostgresEventStore()

    ride_request_event = adapter.normalize(_rider_request_envelope())
    store.append(ride_request_event)
    ride = _ride_from_normalized_event(ride_request_event)

    drivers = _drivers()
    assignment = match_driver(ride, drivers)
    if assignment is None:
        raise MobilePilotProofError("driver candidate selection failed")
    store.append(_server_event("driver_candidate_selected", ride.id, assignment.assignment_hash()))

    route = compute_route(ride, _map_graph())
    price = compute_price(ride, assignment, route, _pricing_config())
    eta_seconds = int(route.estimated_time * 60)

    accept_event = adapter.normalize(_driver_accept_envelope())
    track_event = adapter.normalize(_driver_track_envelope())
    store.append(accept_event)
    store.append(_server_event("trip_accepted", ride.id, assignment.assignment_hash()))
    store.append(track_event)
    store.append(_server_event("eta_shared", ride.id, _canonical_hash({"eta_seconds": eta_seconds})))

    execution_steps = execute_lifecycle(
        ride,
        (
            TransitionRequest(
                ride_hash=ride.ride_hash(),
                current_state=RideLifecycleState.REQUESTED,
                target_state=RideLifecycleState.MATCHED,
                declared_at="server-sequence-0001",
            ),
            TransitionRequest(
                ride_hash=ride.ride_hash(),
                current_state=RideLifecycleState.MATCHED,
                target_state=RideLifecycleState.DRIVER_ACCEPTED,
                declared_at="server-sequence-0002",
            ),
            TransitionRequest(
                ride_hash=ride.ride_hash(),
                current_state=RideLifecycleState.DRIVER_ACCEPTED,
                target_state=RideLifecycleState.IN_PROGRESS,
                declared_at="server-sequence-0003",
            ),
        ),
    )
    trace = build_ride_execution_trace(
        ride,
        assignment=assignment,
        route=route,
        price=price,
        execution_steps=execution_steps,
    )
    replay_report = validate_ride_replay(
        trace,
        ride,
        drivers=drivers,
        map_graph=_map_graph(),
        pricing_config=_pricing_config(),
        execution_steps=execution_steps,
    )

    report = MobilePilotProofReport(
        assignment_hash=assignment.assignment_hash(),
        eta_seconds=eta_seconds,
        event_count=store.row_count(),
        execution_steps_hash=trace.execution_steps_hash or "",
        persistent_event_hash=store.replay_hash(),
        price_hash=price.price_hash(),
        rejected_cases=_rejected_cases(),
        replayed_trip_hash=replay_report.replayed_trace_hash,
        ride_hash=ride.ride_hash(),
        route_hash=route.route_hash(),
        trip_replay_hash=replay_report.original_trace_hash,
    )
    if not report.verified:
        raise MobilePilotProofError("mobile pilot e2e proof failed")
    return report


def _rejected_cases() -> tuple[str, ...]:
    rejected = []
    for case_name, attempt in (
        ("client_timestamp_authority", _reject_client_timestamp_authority),
        ("client_computed_fare_authority", _reject_client_computed_fare_authority),
        ("client_computed_driver_match_authority", _reject_client_match_authority),
        ("client_replay_hash_authority", _reject_client_replay_hash_authority),
        ("duplicate_mobile_request", _reject_duplicate_mobile_request),
        ("spoofed_rider_driver_event", _reject_spoofed_rider_driver_event),
        ("out_of_order_mobile_update", _reject_out_of_order_mobile_update),
        ("tampered_trip_status", _reject_tampered_trip_status),
    ):
        try:
            attempt()
        except MobilePilotProofError:
            rejected.append(case_name)
        else:
            raise MobilePilotProofError(f"mobile rejection case admitted: {case_name}")
    return tuple(rejected)


def _reject_client_timestamp_authority() -> None:
    MobilePilotAdapter().normalize(
        _rider_request_envelope(
            envelope_id="reject.timestamp",
            payload_extra={"authoritative_timestamp": "2026-05-26T00:00:00Z"},
        )
    )


def _reject_client_computed_fare_authority() -> None:
    MobilePilotAdapter().normalize(
        _rider_request_envelope(
            envelope_id="reject.fare",
            payload_extra={"fare": {"total_cost": "1.00"}},
        )
    )


def _reject_client_match_authority() -> None:
    MobilePilotAdapter().normalize(
        _rider_request_envelope(
            envelope_id="reject.match",
            payload_extra={"match_result": {"driver_id": "driver.client"}},
        )
    )


def _reject_client_replay_hash_authority() -> None:
    MobilePilotAdapter().normalize(
        _rider_request_envelope(
            envelope_id="reject.replay",
            payload_extra={"replay_hash": "0" * 64},
        )
    )


def _reject_duplicate_mobile_request() -> None:
    adapter = MobilePilotAdapter()
    envelope = _rider_request_envelope(envelope_id="reject.duplicate")
    adapter.normalize(envelope)
    adapter.normalize(envelope)


def _reject_spoofed_rider_driver_event() -> None:
    MobilePilotAdapter().normalize(
        MobileEnvelope(
            envelope_id="reject.spoof",
            client_kind="driver",
            principal_id="driver.real",
            event_type="driver_accept",
            client_sequence=0,
            observed_at="2026-05-26T00:01:00Z",
            payload={"driver_id": "driver.spoof", "ride_id": "ride.mobile.001"},
        )
    )


def _reject_out_of_order_mobile_update() -> None:
    MobilePilotAdapter().normalize(
        _rider_request_envelope(
            envelope_id="reject.order",
            client_sequence=2,
        )
    )


def _reject_tampered_trip_status() -> None:
    MobilePilotAdapter().normalize(
        _driver_accept_envelope(
            envelope_id="reject.status",
            payload_extra={"trip_status": "COMPLETED"},
        )
    )


def _rider_request_envelope(
    *,
    envelope_id: str = "rider.request.001",
    client_sequence: int = 0,
    payload_extra: Mapping[str, Any] | None = None,
) -> MobileEnvelope:
    payload = {
        "dropoff_location": {"lat": -37.8222, "lng": 144.9689, "node_id": "docklands", "zone": "melbourne.cbd"},
        "pickup_location": {"lat": -37.8136, "lng": 144.9631, "node_id": "flinders", "zone": "melbourne.cbd"},
        "rider_id": "rider.mobile.001",
        "ride_id": "ride.mobile.001",
    }
    payload.update(dict(payload_extra or {}))
    return MobileEnvelope(
        client_kind="rider",
        client_sequence=client_sequence,
        envelope_id=envelope_id,
        event_type="rider_request",
        observed_at="2026-05-26T00:00:00Z",
        payload=payload,
        principal_id="rider.mobile.001",
    )


def _driver_accept_envelope(
    *,
    envelope_id: str = "driver.accept.001",
    payload_extra: Mapping[str, Any] | None = None,
) -> MobileEnvelope:
    payload = {
        "driver_id": "driver.mobile.001",
        "ride_id": "ride.mobile.001",
    }
    payload.update(dict(payload_extra or {}))
    return MobileEnvelope(
        client_kind="driver",
        client_sequence=0,
        envelope_id=envelope_id,
        event_type="driver_accept",
        observed_at="2026-05-26T00:01:00Z",
        payload=payload,
        principal_id="driver.mobile.001",
    )


def _driver_track_envelope() -> MobileEnvelope:
    return MobileEnvelope(
        client_kind="driver",
        client_sequence=1,
        envelope_id="driver.track.001",
        event_type="driver_track",
        observed_at="2026-05-26T00:02:00Z",
        payload={
            "driver_id": "driver.mobile.001",
            "location": {"lat": -37.8140, "lng": 144.9635, "zone": "melbourne.cbd"},
            "ride_id": "ride.mobile.001",
        },
        principal_id="driver.mobile.001",
    )


def _ride_from_normalized_event(event: Mapping[str, Any]) -> Ride:
    payload = event["payload"]["submitted_payload"]
    return Ride(
        id=payload["ride_id"],
        passenger_id=payload["rider_id"],
        pickup_location=payload["pickup_location"],
        dropoff_location=payload["dropoff_location"],
        requested_at="2026-05-26T00:00:00Z",
    )


def _server_event(event_type: str, ride_id: str, artifact_hash: str) -> dict[str, object]:
    return {
        "event_id": f"server.{event_type}.{ride_id}",
        "payload": {
            "artifact_hash": artifact_hash,
            "event_type": event_type,
            "ride_id": ride_id,
        },
        "timestamp": f"server.{event_type}",
        "type": "afriride.server.deterministic",
    }


def _drivers() -> tuple[dict[str, object], ...]:
    return (
        {"id": "driver.mobile.001", "lat": -37.8141, "lng": 144.9634, "zone": "melbourne.cbd"},
        {"id": "driver.mobile.002", "lat": -37.8300, "lng": 144.9800, "zone": "melbourne.cbd"},
    )


def _map_graph() -> dict[str, object]:
    return {
        "nodes": {
            "docklands": {"zone": "melbourne.cbd"},
            "flinders": {"zone": "melbourne.cbd"},
            "southern_cross": {"zone": "melbourne.cbd"},
        },
        "edges": (
            {"from": "flinders", "to": "southern_cross", "distance": 1.1, "estimated_time": 3.0},
            {"from": "southern_cross", "to": "docklands", "distance": 1.4, "estimated_time": 4.0},
            {"from": "flinders", "to": "docklands", "distance": 2.8, "estimated_time": 8.0},
        ),
    }


def _pricing_config() -> PricingConfig:
    return PricingConfig(
        base_fare="4.20",
        currency="AUD",
        per_distance_rate="1.70",
        per_time_rate="0.45",
    )


def _require_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise MobilePilotProofError(f"{field} must be non-empty string")
    if "/" in value or "\\" in value or ".." in value:
        raise MobilePilotProofError(f"{field} contains forbidden path syntax")
    return value


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, tuple):
        return [_canonicalize(item) for item in value]
    if isinstance(value, list):
        return [_canonicalize(item) for item in value]
    return value


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()

