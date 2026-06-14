from __future__ import annotations

import json
from copy import deepcopy

import pytest

from afritech.identity.mobility_participant import MobilityParticipant
from afritech.mobility.fleet_governance import (
    AUTHORITY_BOUNDARY,
    FleetGovernanceError,
    FleetMaintenanceRecord,
    FleetState,
    FleetVehicle,
    build_fleet_governance,
    build_fleet_governance_proof,
    evaluate_fleet_invariants,
    export_fleet_governance_proof,
    validate_fleet_governance,
    validate_fleet_governance_report,
    validate_fleet_invariants,
)


def _operator() -> MobilityParticipant:
    return MobilityParticipant.from_mapping(
        {
            "participant_id": "fleet-operator-001",
            "display_name": "Fleet Operator One",
            "roles": ["fleet"],
            "verification_status": "verified",
            "trust_score": 92.5,
            "evidence_links": ["fleet-op-ev-001"],
            "metadata": {},
        }
    )


def _record(ts: int, suffix: str) -> FleetMaintenanceRecord:
    return FleetMaintenanceRecord.from_mapping(
        {
            "maintenance_id": f"maint-{suffix}",
            "timestamp": ts,
            "service_type": "safety-check",
            "service_center_id": "svc-001",
            "custody_link": f"custody-{suffix}",
            "evidence_link": f"maint-ev-{suffix}",
            "verified": True,
            "metadata": {},
        }
    )


def _vehicle(
    vehicle_id: str,
    status: str = "available",
    battery_health: float = 96.0,
    safety_score: float = 94.0,
    route_compliance_score: float = 95.0,
    ts: int = 1_700_000_000,
) -> FleetVehicle:
    return FleetVehicle.from_mapping(
        {
            "vehicle_id": vehicle_id,
            "vehicle_type": "ev",
            "status": status,
            "battery_health": battery_health,
            "safety_score": safety_score,
            "route_compliance_score": route_compliance_score,
            "maintenance_history": [
                _record(ts - 2_000, f"{vehicle_id}-001").canonical_dict(),
                _record(ts - 100, f"{vehicle_id}-002").canonical_dict(),
            ],
            "evidence_links": [f"veh-ev-{vehicle_id}"],
            "metadata": {},
        }
    )


def _state(*, degraded: bool = False) -> FleetState:
    vehicles = (
        _vehicle("veh-a", battery_health=96.0, safety_score=95.0, route_compliance_score=95.0),
        _vehicle("veh-b", battery_health=94.0, safety_score=92.0, route_compliance_score=93.0),
        _vehicle(
            "veh-c",
            status="maintenance" if degraded else "available",
            battery_health=70.0 if degraded else 91.0,
            safety_score=72.0 if degraded else 90.0,
            route_compliance_score=70.0 if degraded else 92.0,
        ),
    )
    return FleetState.from_mapping(
        {
            "fleet_id": "fleet-001",
            "operator": _operator().canonical_dict(),
            "region_id": "melbourne",
            "fleet_type": "commercial",
            "vehicles": [vehicle.canonical_dict() for vehicle in vehicles],
            "timestamp": 1_700_000_500,
            "evidence_links": ["fleet-ev-001"],
            "metadata": {},
        }
    )


def test_fleet_governance_happy_path():
    state = _state()
    report = build_fleet_governance(state)

    assert report.verified is True
    assert report.fleet_trust_score > 0
    assert report.eligible_vehicle_ids


def test_invalid_fleet_configuration_rejected():
    with pytest.raises(FleetGovernanceError):
        FleetState.from_mapping(
            {
                "fleet_id": "fleet-invalid",
                "operator": _operator().canonical_dict(),
                "region_id": "melbourne",
                "fleet_type": "commercial",
                "vehicles": [
                    {
                        "vehicle_id": "veh-x",
                        "vehicle_type": "ev",
                        "status": "available",
                        "battery_health": 90.0,
                        "safety_score": 90.0,
                        "route_compliance_score": 90.0,
                        "maintenance_history": [],
                        "evidence_links": ["veh-ev-x"],
                        "metadata": {},
                    }
                ],
                "timestamp": 1_700_000_500,
                "evidence_links": ["fleet-ev-001"],
                "metadata": {},
            }
        )


def test_fleet_governance_determinism():
    state = _state()
    a = build_fleet_governance(state)
    b = build_fleet_governance(state)

    assert a.canonical_dict() == b.canonical_dict()
    assert a.report_hash() == b.report_hash()


def test_fleet_governance_replay_stability():
    state = _state()
    a = build_fleet_governance(state)
    round_tripped = FleetState.from_mapping(state.canonical_dict())
    b = build_fleet_governance(round_tripped)

    assert a.canonical_dict() == b.canonical_dict()


def test_fleet_tampering_detected():
    state = _state()
    report = build_fleet_governance(state)
    tampered = deepcopy(report.canonical_dict())
    tampered["vehicle_reports"][0]["details"]["battery_health"] = 10.0

    with pytest.raises(FleetGovernanceError):
        validate_fleet_governance(state, tampered)


def test_authority_boundary_preserved():
    state = _state()
    report = build_fleet_governance(state)

    assert state.authority_boundary == AUTHORITY_BOUNDARY
    assert report.authority_boundary == AUTHORITY_BOUNDARY
    assert validate_fleet_governance_report(report) is True


def test_fleet_invariant_compliance():
    state = _state()
    report = build_fleet_governance(state)
    invariant_report = evaluate_fleet_invariants(state, report)

    assert invariant_report.verified is True
    assert validate_fleet_invariants(invariant_report) is True


def test_vehicle_state_requires_maintenance_history():
    with pytest.raises(FleetGovernanceError):
        FleetVehicle.from_mapping(
            {
                "vehicle_id": "veh-x",
                "vehicle_type": "ev",
                "status": "available",
                "battery_health": 90.0,
                "safety_score": 90.0,
                "route_compliance_score": 90.0,
                "maintenance_history": [],
                "evidence_links": ["veh-ev-x"],
                "metadata": {},
            }
        )


def test_custody_links_are_required():
    state = _state()
    tampered = deepcopy(state.canonical_dict())
    tampered["vehicles"][0]["maintenance_history"][0]["custody_link"] = ""

    with pytest.raises(FleetGovernanceError):
        FleetState.from_mapping(tampered)


def test_vehicle_health_influences_fleet_trust():
    healthy = build_fleet_governance(_state())
    degraded = build_fleet_governance(_state(degraded=True))

    assert healthy.fleet_trust_score > degraded.fleet_trust_score


def test_proof_artifact_roundtrip(tmp_path):
    state = _state()
    report = build_fleet_governance(state)
    proof = build_fleet_governance_proof(state, report)
    exported = export_fleet_governance_proof(state, tmp_path, report)

    assert proof["verified"] is True
    assert proof["schema"] == "afritech.mobility.fleet_governance_proof.v1"
    assert exported["json"].exists()
    assert exported["proof"].exists()
    loaded = json.loads(exported["proof"].read_text())
    assert loaded["proof_hash"] == proof["proof_hash"]

