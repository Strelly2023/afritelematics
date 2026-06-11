from __future__ import annotations

from afritech.extensions.afriprog.copilot_assist import validate_context_proposal
from afritech.runtime_monitoring.anomaly_classifier import classify_anomaly
from afritech.runtime_monitoring.anomaly_context_builder import build_anomaly_context
from afritech.runtime_monitoring.anomaly_detector import detect_anomalies
from afritech.runtime_monitoring.anomaly_to_proposal import anomaly_to_proposal
from afritech.runtime_monitoring.monitor import collect_runtime_events


def validate_monitoring_pipeline() -> dict[str, object]:
    events = collect_runtime_events(contract_mismatches=("receipt mismatch",))
    anomalies = detect_anomalies(events)
    classified = classify_anomaly(anomalies[0])
    context = build_anomaly_context(
        classified,
        timestamp="2026-06-06T00:00:00Z",
        event_trace=("RideRequested", "RideAccepted"),
        current_receipt="v1",
        expected_receipt="v2",
        affected_files=("afritech/api/driver.py",),
        validator_failures=("driver_contract_replay_validator",),
    )
    proposal = anomaly_to_proposal(classified, context)
    validation = validate_context_proposal(proposal)
    return {
        "anomaly_count": len(anomalies),
        "severity": classified["severity"],
        "proposal_id": proposal.proposal_id,
        "proposal_status": validation["status"],
        "governance_required": proposal.governance_required,
        "activation_allowed": proposal.activation_allowed,
        "runtime_mutation_allowed": proposal.runtime_mutation_allowed,
        "rollback_execution_allowed": proposal.rollback_execution_allowed,
    }


__all__ = ["validate_monitoring_pipeline"]
