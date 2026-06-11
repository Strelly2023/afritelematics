from __future__ import annotations

from afritech.distributed.anomaly_consensus.consensus_engine import compute_consensus
from afritech.distributed.anomaly_consensus.consensus_to_proposal import (
    consensus_to_proposal,
)
from afritech.distributed.anomaly_consensus.evidence_collector import collect_evidence
from afritech.distributed.anomaly_consensus.node_observer import observe_anomaly


def validate_consensus_pipeline() -> dict[str, object]:
    reports = (
        observe_anomaly(
            node_id="node-A",
            timestamp="2026-06-06T00:00:00Z",
            anomaly_type="contract_mismatch",
            severity="HIGH",
            context_hash="ctx-1",
        ),
        observe_anomaly(
            node_id="node-B",
            timestamp="2026-06-06T00:00:01Z",
            anomaly_type="contract_mismatch",
            severity="HIGH",
            context_hash="ctx-1",
        ),
        observe_anomaly(
            node_id="node-C",
            timestamp="2026-06-06T00:00:02Z",
            anomaly_type="contract_mismatch",
            severity="MEDIUM",
            context_hash="ctx-1",
        ),
    )
    evidence = collect_evidence(reports)
    consensus = compute_consensus(
        evidence["verified_reports"],
        total_nodes=3,
        min_quorum=2,
    )
    proposal = consensus_to_proposal(consensus[0])
    return {
        "verified_count": len(evidence["verified_reports"]),
        "consensus_count": len(consensus),
        "proposal_id": proposal.proposal_id,
        "governance_required": proposal.governance_required,
        "activation_allowed": proposal.activation_allowed,
        "runtime_mutation_allowed": proposal.runtime_mutation_allowed,
    }


__all__ = ["validate_consensus_pipeline"]
