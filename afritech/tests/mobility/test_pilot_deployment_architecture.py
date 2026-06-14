from __future__ import annotations

import json
from copy import deepcopy

import pytest

from afritech.mobility.pilot_deployment_architecture import (
    PilotDeploymentError,
    PilotDeploymentPlan,
    PilotRegion,
    build_pilot_deployment,
    build_pilot_deployment_proof,
    evaluate_pilot_deployment_invariants,
    export_pilot_deployment,
    export_pilot_deployment_invariant_report,
    validate_pilot_deployment,
    validate_pilot_deployment_invariants,
)
from afritech.mobility.real_time_execution_engine import build_real_time_execution
from afritech.mobility.trust_dispatch import DispatchCandidate, DispatchRequest, run_trust_aware_dispatch
from afritech.identity.mobility_participant import MobilityParticipant


def _execution():
    request = DispatchRequest.from_mapping(
        {
            "operation_id": "op-001",
            "operation_type": "ride",
            "origin": {"lat": -37.8136, "lon": 144.9631, "timestamp": 1_700_000_000},
            "destination": {"lat": -37.8036, "lon": 144.9731, "timestamp": 1_700_000_100},
            "constraints": {"required_roles": ["driver"]},
            "timestamp": 1_700_000_000,
        }
    )
    participant = MobilityParticipant.from_mapping(
        {
            "participant_id": "driver-001",
            "display_name": "Driver One",
            "roles": ["driver"],
            "verification_status": "verified",
            "trust_score": 95.0,
            "evidence_links": ["driver-001-ev"],
            "metadata": {},
        }
    )
    candidate = DispatchCandidate.from_mapping(
        {
            "participant": participant.canonical_dict(),
            "location": {"lat": -37.8136, "lon": 144.9631, "timestamp": 1_700_000_000},
            "availability": True,
            "reliability_score": 95.0,
            "anomaly_rate": 0.0,
            "supported_operations": ["ride"],
            "capacity": 1,
            "metadata": {},
        }
    )
    return build_real_time_execution(run_trust_aware_dispatch(request, (candidate,)))


def _deployment():
    region = PilotRegion.from_mapping(
        {
            "region_id": "melbourne",
            "partition_id": "south-east",
            "authority_scope": "pilot",
            "replay_hash": "a" * 64,
            "verified": True,
            "metadata": {},
        }
    )
    return build_pilot_deployment(
        _execution(),
        pilot_id="pilot-001",
        regions=(region,),
        tenants=("operator", "auditor"),
        deployment_stage="READY",
        readiness_gate=True,
    )


def test_pilot_happy_path():
    deployment = _deployment()

    assert deployment.deployment_stage == "READY"


def test_invalid_input():
    with pytest.raises(PilotDeploymentError):
        build_pilot_deployment({}, pilot_id="")  # type: ignore[arg-type]


def test_determinism():
    a = _deployment()
    b = _deployment()

    assert a.deployment_hash == b.deployment_hash


def test_replay_stability():
    deployment = _deployment()
    rebuilt = PilotDeploymentPlan.from_mapping(deployment.canonical_dict())

    assert deployment.canonical_dict() == rebuilt.canonical_dict()


def test_authority_boundary():
    deployment = _deployment().canonical_dict()
    deployment["authority_boundary"] = "override"

    with pytest.raises(PilotDeploymentError):
        validate_pilot_deployment(deployment)


def test_backend_surface_explicit():
    deployment = _deployment()
    assert deployment.backend_entrypoint == "afriride_system.api.main:app"


def test_tenant_isolation():
    deployment = _deployment()
    assert deployment.tenants == ("auditor", "operator")


def test_region_binding():
    deployment = _deployment()
    assert deployment.regions[0].region_id == "melbourne"


def test_hash_tampering_detected():
    deployment = _deployment().canonical_dict()
    deployment["deployment_hash"] = "f" * 64

    with pytest.raises(PilotDeploymentError):
        validate_pilot_deployment(deployment)


def test_dispatch_and_execution_binding():
    deployment = _deployment()
    assert len(deployment.dispatch_hash) == 64
    assert len(deployment.execution_hash) == 64


def test_proof_integrity_round_trip():
    deployment = _deployment()
    proof = build_pilot_deployment_proof(deployment)
    decoded = json.loads(json.dumps(proof, sort_keys=True))

    assert decoded["deployment_hash"] == deployment.deployment_hash
    assert decoded["authority_boundary"] == "pilot_deployment_proof_read_only"


def test_proof_hash_tampering_rejected(tmp_path):
    deployment = _deployment()
    exported = export_pilot_deployment(tmp_path, deployment)
    proof = json.loads(exported["proof"].read_text())
    proof["deployment_hash"] = "f" * 64

    with pytest.raises(PilotDeploymentError):
        validate_pilot_deployment(proof)


def test_export_pilot_deployment(tmp_path):
    deployment = _deployment()
    exported = export_pilot_deployment(tmp_path, deployment)

    assert exported["json"].exists()
    assert exported["proof"].exists()


def test_invariant_report():
    deployment = _deployment()
    proof = build_pilot_deployment_proof(deployment)
    report = evaluate_pilot_deployment_invariants(deployment, proof)

    assert report.verified is True
    assert validate_pilot_deployment_invariants(report) is True


def test_export_invariant_report(tmp_path):
    deployment = _deployment()
    exported = export_pilot_deployment_invariant_report(tmp_path, deployment)

    assert exported["report"].exists()
