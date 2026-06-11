from __future__ import annotations

import subprocess
import sys

from afritech.distributed.anomaly_consensus import (
    collect_evidence,
    compute_consensus,
    consensus_to_proposal,
    observe_anomaly,
)
from afritech.extensions.afriprog.copilot_assist.federation_governance import (
    build_federation_message,
    compute_federated_vote,
    validate_constitutional_compliance,
)
from afritech.runtime_monitoring import (
    anomaly_to_proposal,
    build_anomaly_context,
    classify_anomaly,
    collect_runtime_events,
    detect_anomalies,
    validate_monitoring_pipeline,
)
from afritech.ci import (
    afriprog_activation_boundary_validator,
    afriprog_anomaly_context_integrity_validator,
    afriprog_anomaly_detection_validator,
    afriprog_anomaly_proposal_conversion_validator,
    afriprog_consensus_non_authority_validator,
    afriprog_consensus_threshold_validator,
    afriprog_constitutional_compliance_validator,
    afriprog_cross_network_signature_validator,
    afriprog_cross_node_context_validator,
    afriprog_evidence_integrity_validator,
    afriprog_federated_vote_validator,
    afriprog_federation_protocol_validator,
    afriprog_global_anomaly_consensus_validator,
    afriprog_runtime_monitoring_validator,
    afriprog_runtime_non_authority_validator,
    afriprog_sovereignty_enforcement_validator,
)


VALIDATORS = (
    afriprog_runtime_monitoring_validator,
    afriprog_anomaly_detection_validator,
    afriprog_anomaly_proposal_conversion_validator,
    afriprog_runtime_non_authority_validator,
    afriprog_anomaly_context_integrity_validator,
    afriprog_global_anomaly_consensus_validator,
    afriprog_evidence_integrity_validator,
    afriprog_consensus_threshold_validator,
    afriprog_consensus_non_authority_validator,
    afriprog_cross_node_context_validator,
    afriprog_federation_protocol_validator,
    afriprog_cross_network_signature_validator,
    afriprog_constitutional_compliance_validator,
    afriprog_federated_vote_validator,
    afriprog_sovereignty_enforcement_validator,
)


def test_runtime_anomaly_monitoring_emits_governed_proposal_only():
    events = collect_runtime_events(contract_mismatches=("receipt mismatch",))
    anomaly = classify_anomaly(detect_anomalies(events)[0])
    context = build_anomaly_context(
        anomaly,
        timestamp="2026-06-06T00:00:00Z",
        affected_files=("afritech/api/driver.py",),
    )
    proposal = anomaly_to_proposal(anomaly, context)
    pipeline = validate_monitoring_pipeline()

    assert anomaly["severity"] == "HIGH"
    assert context["runtime_mutation_allowed"] is False
    assert proposal.governance_required is True
    assert proposal.activation_allowed is False
    assert pipeline["runtime_mutation_allowed"] is False


def test_multi_node_consensus_requires_quorum_and_remains_non_authoritative():
    report_a = observe_anomaly(
        node_id="node-A",
        timestamp="2026-06-06T00:00:00Z",
        anomaly_type="contract_mismatch",
        severity="HIGH",
        context_hash="ctx",
    )
    report_b = observe_anomaly(
        node_id="node-B",
        timestamp="2026-06-06T00:00:01Z",
        anomaly_type="contract_mismatch",
        severity="HIGH",
        context_hash="ctx",
    )
    evidence = collect_evidence((report_a, {**report_b, "signature": "bad"}))
    no_consensus = compute_consensus((report_a,), total_nodes=2, min_quorum=2)
    consensus = compute_consensus((report_a, report_b), total_nodes=2, min_quorum=2)[0]
    proposal = consensus_to_proposal(consensus)

    assert len(evidence["verified_reports"]) == 1
    assert len(evidence["rejected_reports"]) == 1
    assert no_consensus == ()
    assert consensus["consensus_authority"] == "non_authoritative"
    assert consensus["activation_allowed"] is False
    assert proposal.governance_required is True


def test_cross_network_federation_preserves_local_sovereignty():
    messages = (
        build_federation_message(network_id="network-A", proposal_id="P", vote="yes"),
        build_federation_message(network_id="network-B", proposal_id="P", vote="yes"),
        build_federation_message(network_id="network-C", proposal_id="P", vote="no"),
    )
    vote = compute_federated_vote(messages, quorum_ratio=0.66)
    compliance = validate_constitutional_compliance(
        {
            "replay_required": True,
            "validators_required": True,
            "governance_required": True,
            "local_activation_sovereignty": True,
            "runtime_mutation_protected": True,
        }
    )

    assert vote["consensus_reached"] is True
    assert vote["governance_outcome"] == "LOCAL_APPROVAL_REQUIRED"
    assert vote["external_activation_allowed"] is False
    assert vote["external_runtime_mutation_allowed"] is False
    assert compliance["compliant"] is True


def test_runtime_consensus_federation_validators_pass_directly():
    for validator in VALIDATORS:
        validator.validate()


def test_runtime_consensus_federation_validator_cli_entrypoints_pass():
    for validator in VALIDATORS:
        result = subprocess.run(
            [sys.executable, "-m", validator.VALIDATOR_NAME],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert "PASSED" in result.stdout
