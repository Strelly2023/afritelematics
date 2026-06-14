from __future__ import annotations

import json
from copy import deepcopy

import pytest

from afritech.identity.mobility_participant import MobilityParticipant
from afritech.mobility.fleet_governance import (
    FleetMaintenanceRecord,
    FleetState,
    FleetVehicle,
    build_fleet_governance,
    evaluate_fleet_invariants,
    validate_fleet_invariants,
)
from afritech.mobility.institutional_networks import (
    AUTHORITY_BOUNDARY,
    INSTITUTION_INVARIANT_IDS,
    INSTITUTION_POLICY_TYPES,
    INSTITUTION_PROOF_AUTHORITY_BOUNDARY,
    InstitutionGovernanceError,
    InstitutionNetwork,
    InstitutionPolicy,
    build_institution_governance,
    build_institution_governance_proof,
    evaluate_institution_invariants,
    export_institution_governance_proof,
    export_institution_invariant_report,
    validate_institution_governance,
    validate_institution_invariants,
)


def _participant(participant_id: str, display_name: str, roles: list[str], institution_id: str, trust_score: float = 90.0):
    return MobilityParticipant.from_mapping(
        {
            "participant_id": participant_id,
            "display_name": display_name,
            "roles": roles,
            "verification_status": "verified",
            "trust_score": trust_score,
            "evidence_links": [f"{participant_id}-ev"],
            "metadata": {"institution_id": institution_id},
        }
    )


def _fleet_record(ts: int, suffix: str) -> FleetMaintenanceRecord:
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


def _fleet_state(fleet_id: str = "fleet-001", operator_id: str = "fleet-operator-001") -> FleetState:
    operator = _participant(operator_id, "Fleet Operator", ["fleet"], "hospital-001", 92.5)
    vehicles = (
        FleetVehicle.from_mapping(
            {
                "vehicle_id": f"{fleet_id}-veh-1",
                "vehicle_type": "ev",
                "status": "available",
                "battery_health": 97.0,
                "safety_score": 96.0,
                "route_compliance_score": 95.0,
                "maintenance_history": [
                    _fleet_record(1_700_000_000, f"{fleet_id}-1").canonical_dict(),
                    _fleet_record(1_700_000_100, f"{fleet_id}-2").canonical_dict(),
                ],
                "evidence_links": [f"{fleet_id}-veh-1-ev"],
                "metadata": {},
            }
        ),
        FleetVehicle.from_mapping(
            {
                "vehicle_id": f"{fleet_id}-veh-2",
                "vehicle_type": "ev",
                "status": "available",
                "battery_health": 94.0,
                "safety_score": 93.0,
                "route_compliance_score": 94.0,
                "maintenance_history": [
                    _fleet_record(1_700_000_000, f"{fleet_id}-3").canonical_dict(),
                    _fleet_record(1_700_000_100, f"{fleet_id}-4").canonical_dict(),
                ],
                "evidence_links": [f"{fleet_id}-veh-2-ev"],
                "metadata": {},
            }
        ),
    )
    return FleetState.from_mapping(
        {
            "fleet_id": fleet_id,
            "operator": operator.canonical_dict(),
            "region_id": "melbourne",
            "fleet_type": "commercial",
            "vehicles": [vehicle.canonical_dict() for vehicle in vehicles],
            "timestamp": 1_700_000_500,
            "evidence_links": [f"{fleet_id}-ev"],
            "metadata": {},
        }
    )


def _fleet_report(fleet_id: str = "fleet-001"):
    return build_fleet_governance(_fleet_state(fleet_id=fleet_id))


def _policy(policy_id: str, policy_type: str, constraints: dict[str, object], rules: list[str] | None = None):
    return InstitutionPolicy.from_mapping(
        {
            "policy_id": policy_id,
            "policy_type": policy_type,
            "constraints": constraints,
            "enforcement_rules": rules or [f"enforce-{policy_id}"],
            "verified": True,
        }
    )


def _hospital_network(emergency: bool = True):
    policies = [
        _policy("dispatch-priority", "dispatch", {"emergency": emergency, "priority_role": "driver"}),
        _policy("access-medical", "access", {"restricted_zone": "medical", "allowed_roles": ["driver", "institution"]}),
        _policy("custody-temperature", "custody", {"temperature_sensitive": True, "required_condition": "temperature_safe"}),
        _policy("market-medical", "market", {"subsidy": "medical_priority", "price_cap": 1.1}),
    ]
    return InstitutionNetwork.from_mapping(
        {
            "institution_id": "hospital-001",
            "domain_type": "hospital",
            "participants": [
                _participant("driver-001", "Driver One", ["driver"], "hospital-001", 97.0).canonical_dict(),
                _participant("driver-002", "Driver Two", ["driver"], "hospital-001", 92.0).canonical_dict(),
                _participant("courier-001", "Courier One", ["courier"], "hospital-001", 88.0).canonical_dict(),
            ],
            "fleets": [
                _fleet_report("hospital-fleet-001").canonical_dict(),
            ],
            "policies": [policy.canonical_dict() for policy in policies],
            "timestamp": 1_700_000_800,
            "evidence_links": ["hospital-001-ev"],
            "metadata": {},
        }
    )


def _airport_network():
    return InstitutionNetwork.from_mapping(
        {
            "institution_id": "airport-001",
            "domain_type": "airport",
            "participants": [
                _participant("driver-003", "Airport Driver", ["driver"], "airport-001", 90.0).canonical_dict(),
                _participant("courier-002", "Airport Courier", ["courier"], "airport-001", 89.0).canonical_dict(),
            ],
            "fleets": [
                _fleet_report("airport-fleet-001").canonical_dict(),
            ],
            "policies": [
                _policy("dispatch-airport", "dispatch", {"priority_role": "driver"}).canonical_dict(),
                _policy("access-airport", "access", {"zone": "airside"}).canonical_dict(),
            ],
            "timestamp": 1_700_000_900,
            "evidence_links": ["airport-001-ev"],
            "metadata": {},
        }
    )


def _university_network():
    return InstitutionNetwork.from_mapping(
        {
            "institution_id": "university-001",
            "domain_type": "university",
            "participants": [
                _participant("driver-004", "University Driver", ["driver"], "university-001", 89.0).canonical_dict(),
                _participant("merchant-001", "Campus Merchant", ["merchant"], "university-001", 91.0).canonical_dict(),
            ],
            "fleets": [
                _fleet_report("university-fleet-001").canonical_dict(),
            ],
            "policies": [
                _policy("dispatch-campus", "dispatch", {"priority_role": "driver"}).canonical_dict(),
                _policy("access-campus", "access", {"zone": "campus"}).canonical_dict(),
                _policy("custody-campus", "custody", {"temperature_sensitive": False}).canonical_dict(),
            ],
            "timestamp": 1_700_001_000,
            "evidence_links": ["university-001-ev"],
            "metadata": {},
        }
    )


def test_institution_network_happy_path():
    network = _hospital_network()
    report = build_institution_governance(network)

    assert report.verified is True
    assert report.governance_hash == network.governance_hash
    assert report.reference_hash == network.reference_hash


def test_institution_policy_registration():
    network = _hospital_network()

    assert set(policy.policy_type for policy in network.policies).issubset(set(INSTITUTION_POLICY_TYPES))
    assert all(len(policy.policy_hash) == 64 for policy in network.policies)


def test_institution_fleet_binding():
    fleet_report = _fleet_report()
    network = InstitutionNetwork.from_mapping(
        {
            "institution_id": "hospital-002",
            "domain_type": "hospital",
            "participants": [_participant("driver-010", "Driver Ten", ["driver"], "hospital-002").canonical_dict()],
            "fleets": [fleet_report.canonical_dict()],
            "policies": [_policy("dispatch-002", "dispatch", {"priority_role": "driver"}).canonical_dict()],
            "timestamp": 1_700_001_100,
            "evidence_links": ["hospital-002-ev"],
            "metadata": {},
        }
    )

    assert network.fleets[0].fleet_hash == fleet_report.fleet_hash
    assert network.fleets[0].verified is True


def test_institution_participant_binding():
    network = _hospital_network()

    assert {participant.participant_id for participant in network.participants} == {
        "driver-001",
        "driver-002",
        "courier-001",
    }
    assert all(participant.verification_status == "verified" for participant in network.participants)


def test_institution_governance_determinism():
    network = _hospital_network()
    a = build_institution_governance(network)
    b = build_institution_governance(network)

    assert a.canonical_dict() == b.canonical_dict()
    assert a.report_hash() == b.report_hash()


def test_institution_governance_hash_stability():
    network = _hospital_network()
    report = build_institution_governance(network)
    round_tripped = InstitutionNetwork.from_mapping(network.canonical_dict())
    rebuilt = build_institution_governance(round_tripped)

    assert report.governance_hash == rebuilt.governance_hash
    assert report.reference_hash == rebuilt.reference_hash


def test_institution_governance_replay_stability():
    network = _hospital_network()
    report = build_institution_governance(network)
    invariant_report = evaluate_institution_invariants(network, report)

    assert invariant_report.verified is True
    assert validate_institution_invariants(invariant_report) is True


def test_institution_cannot_become_truth_authority():
    network = _hospital_network()
    report = build_institution_governance(network)

    assert network.authority_boundary == AUTHORITY_BOUNDARY
    assert report.authority_boundary == AUTHORITY_BOUNDARY
    assert "truth" not in report.canonical_dict()


def test_institution_cannot_override_proof_authority():
    network = _hospital_network()
    report = build_institution_governance(network)
    proof = build_institution_governance_proof(network, report)

    assert proof["authority_boundary"] == INSTITUTION_PROOF_AUTHORITY_BOUNDARY
    assert proof["verified"] is True


def test_institution_cannot_override_replay_authority():
    network = _hospital_network()
    report = build_institution_governance(network)
    round_tripped = InstitutionNetwork.from_mapping(network.canonical_dict())
    rebuilt = build_institution_governance(round_tripped)

    assert report.reference_hash == rebuilt.reference_hash
    assert report.canonical_dict()["reference_hash"] == rebuilt.canonical_dict()["reference_hash"]


def test_institution_cannot_override_settlement_authority():
    network = _hospital_network()
    report = build_institution_governance(network)

    assert "settlement" not in report.canonical_dict()


def test_dispatch_policy_is_explicit():
    network = _hospital_network()
    report = build_institution_governance(network)

    assert report.dispatch_projection == ("driver-001", "driver-002", "courier-001")
    assert "dispatch-priority" in report.policy_hash or len(report.policy_hash) == 64


def test_access_policy_is_explicit():
    network = _hospital_network()
    report = build_institution_governance(network)

    assert any(item.startswith("access-medical") for item in report.access_projection)
    assert any("restricted_zone" in item for item in report.access_projection)


def test_market_policy_is_explicit():
    network = _hospital_network()
    report = build_institution_governance(network)

    assert any(item.startswith("market-medical") for item in report.market_projection)
    assert any("price_cap" in item for item in report.market_projection)


def test_custody_policy_is_explicit():
    network = _hospital_network()
    report = build_institution_governance(network)

    assert any(item.startswith("custody-temperature") for item in report.custody_projection)
    assert any("temperature_sensitive" in item for item in report.custody_projection)


def test_hospital_rules_do_not_leak_to_airport():
    hospital = _hospital_network()
    airport = _airport_network()

    hospital_report = build_institution_governance(hospital)
    airport_report = build_institution_governance(airport)

    assert hospital_report.dispatch_projection != airport_report.dispatch_projection
    assert hospital_report.policy_hash != airport_report.policy_hash


def test_airport_rules_do_not_leak_to_university():
    airport = _airport_network()
    university = _university_network()

    airport_report = build_institution_governance(airport)
    university_report = build_institution_governance(university)

    assert airport_report.access_projection != university_report.access_projection


def test_institution_boundary_is_enforced():
    network = _hospital_network()
    tampered = deepcopy(network.canonical_dict())
    tampered["authority_boundary"] = "malicious_boundary"

    with pytest.raises(InstitutionGovernanceError):
        InstitutionNetwork.from_mapping(tampered)


def test_cross_institution_access_rejected():
    network = _hospital_network()
    tampered = deepcopy(network.canonical_dict())
    tampered["participants"][0]["metadata"]["institution_id"] = "airport-001"

    with pytest.raises(InstitutionGovernanceError):
        InstitutionNetwork.from_mapping(tampered)


def test_duplicate_identity_rejected():
    network = _hospital_network()
    tampered = deepcopy(network.canonical_dict())
    tampered["participants"].append(deepcopy(tampered["participants"][0]))

    with pytest.raises(InstitutionGovernanceError):
        InstitutionNetwork.from_mapping(tampered)


def test_identity_must_be_registered():
    network = _hospital_network()
    tampered = deepcopy(network.canonical_dict())
    tampered["participants"][0]["metadata"]["institution_id"] = "unregistered-institution"

    with pytest.raises(InstitutionGovernanceError):
        InstitutionNetwork.from_mapping(tampered)


def test_participant_role_validation():
    with pytest.raises(Exception):
        _participant("bad-role", "Bad Role", ["admin"], "hospital-001")


def test_institution_owned_fleet_binding():
    network = _hospital_network()
    report = build_institution_governance(network)

    assert report.fleet_bindings
    assert report.fleet_bindings[0][0] == "hospital-fleet-001"


def test_fleet_must_pass_fleet_invariants():
    fleet_state = _fleet_state("hospital-fleet-010")
    fleet_report = build_fleet_governance(fleet_state)
    fleet_invariants = evaluate_fleet_invariants(fleet_state, fleet_report)

    assert fleet_invariants.verified is True
    assert validate_fleet_invariants(fleet_invariants) is True


def test_fleet_eligibility_projection_preserved():
    network = _hospital_network()
    report = build_institution_governance(network)

    assert any(binding[1]["eligible_vehicle_ids"] for binding in report.fleet_bindings)


def test_emergency_dispatch_priority():
    network = _hospital_network(emergency=True)
    report = build_institution_governance(network)

    assert report.dispatch_projection[:2] == ("driver-001", "driver-002")


def test_normal_dispatch_unchanged():
    network = _hospital_network(emergency=False)
    report = build_institution_governance(network)

    assert report.dispatch_projection == ("driver-001", "driver-002", "courier-001")


def test_dispatch_remains_deterministic():
    network = _hospital_network()
    a = build_institution_governance(network)
    b = build_institution_governance(network)

    assert a.dispatch_projection == b.dispatch_projection


def test_medical_delivery_requires_custody_constraints():
    network = _hospital_network()
    report = build_institution_governance(network)

    assert any(item.startswith("custody-temperature") for item in report.custody_projection)


def test_temperature_sensitive_delivery_constraints():
    network = _hospital_network()
    report = build_institution_governance(network)

    assert "temperature_sensitive=True" in report.custody_projection


def test_custody_chain_remains_replayable():
    network = _hospital_network()
    report = build_institution_governance(network)
    round_tripped = InstitutionNetwork.from_mapping(network.canonical_dict())
    rebuilt = build_institution_governance(round_tripped)

    assert report.custody_projection == rebuilt.custody_projection


def test_institution_policy_does_not_change_proof_hash():
    network = _hospital_network()
    report = build_institution_governance(network)
    proof_a = build_institution_governance_proof(network, report)

    tampered = deepcopy(network.canonical_dict())
    tampered["policies"][0]["constraints"]["emergency"] = False
    changed = InstitutionNetwork.from_mapping(tampered)
    changed_report = build_institution_governance(changed)
    proof_b = build_institution_governance_proof(changed, changed_report)

    assert proof_a["proof_hash"] == proof_b["proof_hash"]
    assert report.governance_hash != changed_report.governance_hash


def test_institution_policy_does_not_change_replay_truth():
    network = _hospital_network()
    tampered = deepcopy(network.canonical_dict())
    tampered["policies"][1]["constraints"]["zone"] = "critical"
    changed = InstitutionNetwork.from_mapping(tampered)

    assert network.reference_hash == changed.reference_hash


def test_institution_artifacts_are_reference_only():
    network = _hospital_network()
    report = build_institution_governance(network)
    proof = build_institution_governance_proof(network, report)

    assert proof["authority_boundary"] == INSTITUTION_PROOF_AUTHORITY_BOUNDARY
    assert proof["reference_hash"] == network.reference_hash
    assert proof["governance_hash"] == network.governance_hash


def test_ia_institution_001():
    network = _hospital_network()
    report = build_institution_governance(network)
    invariant_report = evaluate_institution_invariants(network, report)

    assert any(check.identifier == "IA-INSTITUTION-001" and check.satisfied for check in invariant_report.checks)


def test_ia_institution_002():
    network = _hospital_network()
    report = build_institution_governance(network)
    invariant_report = evaluate_institution_invariants(network, report)

    assert any(check.identifier == "IA-INSTITUTION-002" and check.satisfied for check in invariant_report.checks)


def test_ia_institution_003():
    network = _hospital_network()
    report = build_institution_governance(network)
    invariant_report = evaluate_institution_invariants(network, report)

    assert any(check.identifier == "IA-INSTITUTION-003" and check.satisfied for check in invariant_report.checks)


def test_ia_institution_004():
    network = _hospital_network()
    report = build_institution_governance(network)
    invariant_report = evaluate_institution_invariants(network, report)

    assert any(check.identifier == "IA-INSTITUTION-004" and check.satisfied for check in invariant_report.checks)


def test_ia_institution_005():
    network = _hospital_network()
    report = build_institution_governance(network)
    invariant_report = evaluate_institution_invariants(network, report)

    assert any(check.identifier == "IA-INSTITUTION-005" and check.satisfied for check in invariant_report.checks)


def test_ia_institution_006():
    network = _hospital_network()
    report = build_institution_governance(network)
    invariant_report = evaluate_institution_invariants(network, report)

    assert any(check.identifier == "IA-INSTITUTION-006" and check.satisfied for check in invariant_report.checks)


def test_tampered_policy_detected():
    network = _hospital_network()
    tampered = deepcopy(network.canonical_dict())
    tampered["policies"][0]["constraints"]["emergency"] = False

    with pytest.raises(InstitutionGovernanceError):
        validate_institution_governance(InstitutionNetwork.from_mapping(tampered), build_institution_governance(network))


def test_tampered_dispatch_constraints_detected():
    network = _hospital_network()
    report = build_institution_governance(network)
    tampered = deepcopy(report.canonical_dict())
    tampered["dispatch_projection"] = list(reversed(tampered["dispatch_projection"]))

    with pytest.raises(InstitutionGovernanceError):
        validate_institution_governance(network, tampered)


def test_tampered_institution_hash_detected():
    network = _hospital_network()
    report = build_institution_governance(network)
    tampered = deepcopy(report.canonical_dict())
    tampered["governance_hash"] = "f" * 64

    with pytest.raises(InstitutionGovernanceError):
        validate_institution_governance(network, tampered)


def test_tampered_identity_mapping_detected():
    network = _hospital_network()
    tampered = deepcopy(network.canonical_dict())
    tampered["participant_ids"][0] = "unexpected-participant"

    with pytest.raises(InstitutionGovernanceError):
        InstitutionNetwork.from_mapping(tampered)


def test_tampered_fleet_binding_detected():
    network = _hospital_network()
    tampered = deepcopy(network.canonical_dict())
    tampered["fleet_hashes"][0] = "a" * 64

    with pytest.raises(InstitutionGovernanceError):
        InstitutionNetwork.from_mapping(tampered)


def test_export_institution_governance_proof(tmp_path):
    network = _hospital_network()
    report = build_institution_governance(network)
    exported = export_institution_governance_proof(network, tmp_path, report)

    assert exported["json"].exists()
    assert exported["proof"].exists()
    loaded = json.loads(exported["proof"].read_text())
    assert loaded["proof_hash"] == build_institution_governance_proof(network, report)["proof_hash"]


def test_export_institution_invariant_report(tmp_path):
    network = _hospital_network()
    report = build_institution_governance(network)
    exported = export_institution_invariant_report(network, tmp_path, report)

    assert exported["report"].exists()
    loaded = json.loads(exported["report"].read_text())
    assert loaded["schema"] == "afritech.mobility.institution_invariant_report.v1"


def test_export_is_hash_stable(tmp_path):
    network = _hospital_network()
    report = build_institution_governance(network)
    first = export_institution_governance_proof(network, tmp_path / "a", report)
    second = export_institution_governance_proof(network, tmp_path / "b", report)

    assert first["proof"].read_text() == second["proof"].read_text()
