"""Deterministic pilot dataset simulation for first live deployment."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from afritech.identity.mobility_participant import MobilityParticipant
from afritech.mobility.field_evidence import (
    FieldEvidenceIngestionResult,
    ingest_field_evidence_signals,
    validate_field_evidence_ingestion,
)
from afritech.mobility.trust_dispatch import (
    DispatchCandidate,
    DispatchDecision,
    DispatchRequest,
    run_trust_aware_dispatch,
)


SCHEMA = "afritech.simulation.pilot_dataset.v1"
SCENARIO_SCHEMA = "afritech.live_deployment.scenario.v1"
AUTHORITY_BOUNDARY = "pilot_dataset_simulation_reference_only"
SCENARIO_AUTHORITY_BOUNDARY = "live_deployment_scenario_reference_only"

FIRST_DEPLOYMENT_SCENARIO = {
    "schema": SCENARIO_SCHEMA,
    "scenario_id": "airport-zone-001",
    "name": "Airport controlled pickup and dropoff pilot",
    "deployment_type": "airport",
    "zone": "airport_pickup_dropoff_zone",
    "city": "Melbourne",
    "authority_boundary": SCENARIO_AUTHORITY_BOUNDARY,
    "live_money": "disabled_by_default",
    "pilot_window": "controlled_day_0",
    "operator_roles": (
        "pilot_lead",
        "airport_zone_operator",
        "driver_support",
        "evidence_reviewer",
        "rollback_owner",
    ),
    "required_gates": (
        "constitutional_doctrine_validation",
        "adr_0042_runtime_validation",
        "pilot_dataset_simulation_validation",
        "field_evidence_ingestion_validation",
        "operator_closeout_review",
    ),
    "stop_conditions": (
        "authority_chain_changed",
        "field_evidence_as_truth_authority",
        "dispatch_participant_mismatch",
        "missing_event_sequence",
        "unstable_evidence_hash",
        "unapproved_live_money_movement",
    ),
}


class PilotDatasetSimulationError(RuntimeError):
    """Raised when the pilot dataset simulation is inadmissible."""


@dataclass(frozen=True)
class SimulatedPilotOperation:
    operation_id: str
    dispatch_hash: str
    selected_participant_id: str
    signal_count: int
    collection_hash: str
    proof_hash: str
    ingestion_hash: str
    verified: bool

    def canonical_dict(self) -> dict[str, object]:
        return {
            "collection_hash": self.collection_hash,
            "dispatch_hash": self.dispatch_hash,
            "ingestion_hash": self.ingestion_hash,
            "operation_id": self.operation_id,
            "proof_hash": self.proof_hash,
            "selected_participant_id": self.selected_participant_id,
            "signal_count": self.signal_count,
            "verified": self.verified,
        }


@dataclass(frozen=True)
class PilotDatasetSimulation:
    scenario: dict[str, Any]
    operations: tuple[SimulatedPilotOperation, ...]
    authority_boundary: str = AUTHORITY_BOUNDARY

    @property
    def verified(self) -> bool:
        return (
            self.authority_boundary == AUTHORITY_BOUNDARY
            and self.scenario.get("authority_boundary") == SCENARIO_AUTHORITY_BOUNDARY
            and self.scenario.get("deployment_type") == "airport"
            and len(self.operations) >= 3
            and all(operation.verified for operation in self.operations)
        )

    @property
    def dataset_hash(self) -> str:
        return _hash(self._hash_payload())

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "operations": [operation.canonical_dict() for operation in self.operations],
            "scenario": self.scenario,
            "schema": SCHEMA,
            "verified": self.verified,
        }

    def canonical_dict(self) -> dict[str, Any]:
        payload = self._hash_payload()
        payload["dataset_hash"] = self.dataset_hash
        return payload


def generate_airport_pilot_dataset(operation_count: int = 3) -> PilotDatasetSimulation:
    if operation_count < 1:
        raise PilotDatasetSimulationError("operation_count must be positive")

    operations: list[SimulatedPilotOperation] = []
    for index in range(operation_count):
        dispatch = _dispatch(index)
        signals = _signals(dispatch, index)
        ingestion = ingest_field_evidence_signals(
            dispatch,
            reversed(signals),
            ingestion_id=f"airport-zone-001-ingestion-{index + 1:03d}",
            collection_id=f"airport-zone-001-evidence-{index + 1:03d}",
        )
        _validate_ingestion(dispatch, ingestion)
        operations.append(
            SimulatedPilotOperation(
                operation_id=dispatch.request.operation_id,
                dispatch_hash=dispatch.decision_hash,
                selected_participant_id=dispatch.selected_participant_id,
                signal_count=len(ingestion.signal_hashes),
                collection_hash=ingestion.collection.collection_hash,
                proof_hash=str(ingestion.proof["proof_hash"]),
                ingestion_hash=ingestion.ingestion_hash,
                verified=ingestion.verified,
            )
        )

    simulation = PilotDatasetSimulation(
        scenario=dict(FIRST_DEPLOYMENT_SCENARIO),
        operations=tuple(operations),
    )
    if not simulation.verified:
        raise PilotDatasetSimulationError("airport pilot dataset simulation failed")
    return simulation


def generate_airport_pilot_dispatches(operation_count: int = 3):
    if operation_count < 1:
        raise PilotDatasetSimulationError("operation_count must be positive")
    return tuple(_dispatch(index) for index in range(operation_count))


def generate_airport_pilot_signals(operation_count: int = 3) -> tuple[tuple[dict[str, Any], ...], ...]:
    if operation_count < 1:
        raise PilotDatasetSimulationError("operation_count must be positive")

    signals: list[tuple[dict[str, Any], ...]] = []
    for index in range(operation_count):
        dispatch = _dispatch(index)
        signals.append(_signals(dispatch, index))
    return tuple(signals)


def generate_airport_pilot_ingestions(
    operation_count: int = 3,
) -> tuple[FieldEvidenceIngestionResult, ...]:
    if operation_count < 1:
        raise PilotDatasetSimulationError("operation_count must be positive")

    ingestions: list[FieldEvidenceIngestionResult] = []
    for index, signals in enumerate(generate_airport_pilot_signals(operation_count)):
        dispatch = _dispatch(index)
        ingestion = ingest_field_evidence_signals(
            dispatch,
            reversed(signals),
            ingestion_id=f"airport-zone-001-ingestion-{index + 1:03d}",
            collection_id=f"airport-zone-001-evidence-{index + 1:03d}",
        )
        _validate_ingestion(dispatch, ingestion)
        ingestions.append(ingestion)

    return tuple(ingestions)


def _dispatch(index: int) -> DispatchDecision:
    operation_id = f"airport-zone-001-op-{index + 1:03d}"
    timestamp = 1_700_100_000 + index * 900
    request = DispatchRequest.from_mapping(
        {
            "operation_id": operation_id,
            "operation_type": "ride",
            "origin": {
                "lat": -37.6690 + index * 0.0001,
                "lon": 144.8490 + index * 0.0001,
                "timestamp": timestamp,
            },
            "destination": {
                "lat": -37.6705 + index * 0.0001,
                "lon": 144.8515 + index * 0.0001,
                "timestamp": timestamp + 600,
            },
            "constraints": {"required_roles": ["driver"]},
            "timestamp": timestamp,
        }
    )
    participant = MobilityParticipant.from_mapping(
        {
            "participant_id": f"airport-driver-{index + 1:03d}",
            "display_name": f"Airport Pilot Driver {index + 1:03d}",
            "roles": ["driver"],
            "verification_status": "verified",
            "trust_score": 94.0 - index,
            "evidence_links": [f"airport-driver-evidence-{index + 1:03d}"],
            "metadata": {"pilot_zone": "airport_pickup_dropoff_zone"},
        }
    )
    candidate = DispatchCandidate.from_mapping(
        {
            "participant": participant.canonical_dict(),
            "location": {
                "lat": -37.6690 + index * 0.0001,
                "lon": 144.8490 + index * 0.0001,
                "timestamp": timestamp,
            },
            "availability": True,
            "reliability_score": 95.0 - index,
            "anomaly_rate": 0.0,
            "supported_operations": ["ride"],
            "capacity": 1,
            "metadata": {"staging_lane": f"lane-{index + 1}"},
        }
    )
    return run_trust_aware_dispatch(request, (candidate,))


def _signals(dispatch: DispatchDecision, index: int) -> tuple[dict[str, Any], ...]:
    operation_id = dispatch.request.operation_id
    participant_id = dispatch.selected_participant_id
    timestamp = 1_700_100_000 + index * 900
    lat = -37.6690 + index * 0.0001
    lon = 144.8490 + index * 0.0001
    base = (
        ("GPS", 0, {"lat": lat, "lon": lon, "timestamp": timestamp}, {"speed": 0, "zone": "airport_entry"}),
        ("DRIVER_ACCEPT", 20, {"lat": lat + 0.0001, "lon": lon + 0.0001, "timestamp": timestamp + 20}, {"accepted": True}),
        ("ARRIVAL", 120, {"lat": lat + 0.0002, "lon": lon + 0.0002, "timestamp": timestamp + 120}, {"arrival_zone": "pickup_bay"}),
        ("PICKUP", 180, {"lat": lat + 0.0003, "lon": lon + 0.0003, "timestamp": timestamp + 180}, {"passenger_onboard": True}),
        ("DROPOFF", 600, {"lat": lat + 0.0004, "lon": lon + 0.0004, "timestamp": timestamp + 600}, {"dropoff_zone": "terminal_exit"}),
        ("CUSTOMER_CONFIRM", 630, {"lat": lat + 0.0005, "lon": lon + 0.0005, "timestamp": timestamp + 630}, {"confirmed": True}),
        ("PAYMENT_CONFIRM", 660, {"lat": lat + 0.0006, "lon": lon + 0.0006, "timestamp": timestamp + 660}, {"paid": False, "mode": "simulation_only"}),
    )
    return tuple(
        {
            "signal_id": f"{operation_id}-{event_type.lower()}",
            "source_id": "airport-zone-simulator",
            "source_adapter_version": "adr-0042-airport-sim-v1",
            "operation_id": operation_id,
            "participant_id": participant_id,
            "event_type": event_type,
            "observed_at": timestamp + offset - 1,
            "received_at": timestamp + offset,
            "location": location,
            "payload": payload,
        }
        for event_type, offset, location, payload in base
    )


def _validate_ingestion(dispatch: DispatchDecision, ingestion: FieldEvidenceIngestionResult) -> None:
    if not validate_field_evidence_ingestion(ingestion):
        raise PilotDatasetSimulationError("field evidence ingestion failed")
    if ingestion.collection.operation_id != dispatch.request.operation_id:
        raise PilotDatasetSimulationError("operation binding mismatch")
    if ingestion.collection.selected_participant_id != dispatch.selected_participant_id:
        raise PilotDatasetSimulationError("participant binding mismatch")
    if ingestion.collection.dispatch_hash != dispatch.decision_hash:
        raise PilotDatasetSimulationError("dispatch binding mismatch")


def _hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


__all__ = [
    "AUTHORITY_BOUNDARY",
    "FIRST_DEPLOYMENT_SCENARIO",
    "PilotDatasetSimulation",
    "PilotDatasetSimulationError",
    "SCENARIO_AUTHORITY_BOUNDARY",
    "SCENARIO_SCHEMA",
    "SCHEMA",
    "SimulatedPilotOperation",
    "generate_airport_pilot_dispatches",
    "generate_airport_pilot_ingestions",
    "generate_airport_pilot_dataset",
    "generate_airport_pilot_signals",
]
