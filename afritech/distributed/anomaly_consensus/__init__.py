"""Distributed anomaly consensus as non-authoritative proposal intelligence."""

from afritech.distributed.anomaly_consensus.consensus_engine import compute_consensus
from afritech.distributed.anomaly_consensus.consensus_to_proposal import (
    consensus_to_proposal,
)
from afritech.distributed.anomaly_consensus.evidence_collector import collect_evidence
from afritech.distributed.anomaly_consensus.node_observer import observe_anomaly
from afritech.distributed.anomaly_consensus.trust_verifier import verify_report

__all__ = [
    "collect_evidence",
    "compute_consensus",
    "consensus_to_proposal",
    "observe_anomaly",
    "verify_report",
]
