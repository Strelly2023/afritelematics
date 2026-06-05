"""Resilience decisions for federation consensus, reputation, and replay divergence."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Mapping

from django.utils import timezone

from afritech.models import (
    ConsensusIncident,
    EventRecord,
    NodeReputation,
    ReplayDivergenceRecord,
)


CONSENSUS_FINALIZED = "FINALIZED"
CONSENSUS_UNRESOLVED = "CONSENSUS_UNRESOLVED"
CONSENSUS_NO_AGREEMENT = "NO_AGREEMENT"
REPLAY_DIVERGENCE = "REPLAY_DIVERGENCE"

SIGNATURE_FAILURE_ISOLATION_THRESHOLD = 3
REPLAY_FAILURE_ISOLATION_THRESHOLD = 3
CONFLICTING_ATTESTATION_ISOLATION_THRESHOLD = 2


@dataclass(frozen=True)
class ConsensusEvaluation:
    status: str
    accepted: bool
    state_hash: str | None
    quorum: int
    agreement_count: int
    minority_nodes: tuple[str, ...]
    state_hash_counts: dict[str, int]
    finality_halted: bool


def required_quorum(total_nodes: int) -> int:
    if total_nodes < 1:
        return 1
    return (total_nodes // 2) + 1


def evaluate_state_hash_consensus(
    node_state_hashes: Mapping[str, str],
    *,
    quorum: int | None = None,
    event: EventRecord | None = None,
    persist_incident: bool = False,
) -> ConsensusEvaluation:
    """Classify consensus without guessing truth during disagreement."""

    clean_votes = {
        str(node_id): str(state_hash)
        for node_id, state_hash in node_state_hashes.items()
        if str(node_id).strip() and str(state_hash).strip()
    }
    needed = quorum if quorum is not None else required_quorum(len(clean_votes))
    counts = Counter(clean_votes.values())

    if not counts:
        evaluation = ConsensusEvaluation(
            status=CONSENSUS_NO_AGREEMENT,
            accepted=False,
            state_hash=None,
            quorum=needed,
            agreement_count=0,
            minority_nodes=(),
            state_hash_counts={},
            finality_halted=True,
        )
        _maybe_record_incident(event, evaluation, persist_incident)
        return evaluation

    most_common = counts.most_common()
    winning_hash, agreement_count = most_common[0]
    top_count = agreement_count
    tied_top_hashes = [state_hash for state_hash, count in most_common if count == top_count]
    minority_nodes = tuple(
        sorted(node_id for node_id, state_hash in clean_votes.items() if state_hash != winning_hash)
    )

    if top_count == 1 and len(tied_top_hashes) == len(counts):
        evaluation = ConsensusEvaluation(
            status=CONSENSUS_NO_AGREEMENT,
            accepted=False,
            state_hash=None,
            quorum=needed,
            agreement_count=1,
            minority_nodes=tuple(sorted(clean_votes)),
            state_hash_counts=dict(counts),
            finality_halted=True,
        )
        _maybe_record_incident(event, evaluation, persist_incident)
        return evaluation

    if len(tied_top_hashes) > 1:
        evaluation = ConsensusEvaluation(
            status=CONSENSUS_UNRESOLVED,
            accepted=False,
            state_hash=None,
            quorum=needed,
            agreement_count=top_count,
            minority_nodes=tuple(sorted(clean_votes)),
            state_hash_counts=dict(counts),
            finality_halted=True,
        )
        _maybe_record_incident(event, evaluation, persist_incident)
        return evaluation

    if agreement_count >= needed:
        evaluation = ConsensusEvaluation(
            status=CONSENSUS_FINALIZED,
            accepted=True,
            state_hash=winning_hash,
            quorum=needed,
            agreement_count=agreement_count,
            minority_nodes=minority_nodes,
            state_hash_counts=dict(counts),
            finality_halted=False,
        )
        for node_id in minority_nodes:
            record_node_signal(node_id=node_id, replay_failure=True, reason="minority divergence")
        return evaluation

    evaluation = ConsensusEvaluation(
        status=CONSENSUS_NO_AGREEMENT,
        accepted=False,
        state_hash=None,
        quorum=needed,
        agreement_count=agreement_count,
        minority_nodes=tuple(sorted(clean_votes)),
        state_hash_counts=dict(counts),
        finality_halted=True,
    )
    _maybe_record_incident(event, evaluation, persist_incident)
    return evaluation


def record_node_signal(
    *,
    node_id: str,
    valid_attestation: bool = False,
    invalid_attestation: bool = False,
    signature_failure: bool = False,
    replay_failure: bool = False,
    conflicting_attestation: bool = False,
    reason: str = "",
) -> NodeReputation:
    reputation, _ = NodeReputation.objects.get_or_create(node_id=node_id)
    reputation.valid_attestations += int(valid_attestation)
    reputation.invalid_attestations += int(invalid_attestation)
    reputation.signature_failures += int(signature_failure)
    reputation.replay_failures += int(replay_failure)
    reputation.conflicting_attestations += int(conflicting_attestation)
    reputation.voting_weight = _voting_weight(reputation)
    reputation.is_isolated = _should_isolate(reputation)
    reputation.last_reason = reason
    reputation.updated_at = timezone.now()
    reputation.save()
    return reputation


def record_replay_divergence(
    *,
    expected_state_hash: str,
    observed_state_hash: str,
    event: EventRecord | None = None,
    code_version: str = "",
    event_order_hash: str = "",
    dependency_fingerprint: str = "",
    root_cause: str = "",
) -> ReplayDivergenceRecord:
    if expected_state_hash == observed_state_hash:
        raise ValueError("replay divergence requires different state hashes")
    return ReplayDivergenceRecord.objects.create(
        event=event,
        expected_state_hash=expected_state_hash,
        observed_state_hash=observed_state_hash,
        code_version=code_version,
        event_order_hash=event_order_hash,
        dependency_fingerprint=dependency_fingerprint,
        root_cause=root_cause,
        status=REPLAY_DIVERGENCE,
        finality_halted=True,
    )


def node_health_score(reputation: NodeReputation) -> float:
    penalty = (
        reputation.invalid_attestations * 0.08
        + reputation.signature_failures * 0.2
        + reputation.replay_failures * 0.15
        + reputation.conflicting_attestations * 0.2
    )
    return max(0.0, round(1.0 - penalty, 2))


def _maybe_record_incident(
    event: EventRecord | None,
    evaluation: ConsensusEvaluation,
    persist_incident: bool,
) -> None:
    if not persist_incident or evaluation.accepted:
        return
    ConsensusIncident.objects.create(
        event=event,
        incident_type=evaluation.status,
        status=evaluation.status,
        state_hash_counts=evaluation.state_hash_counts,
        affected_nodes=list(evaluation.minority_nodes),
        finality_halted=True,
    )


def _voting_weight(reputation: NodeReputation) -> float:
    if _should_isolate(reputation):
        return 0.0
    return max(0.1, node_health_score(reputation))


def _should_isolate(reputation: NodeReputation) -> bool:
    return (
        reputation.signature_failures >= SIGNATURE_FAILURE_ISOLATION_THRESHOLD
        or reputation.replay_failures >= REPLAY_FAILURE_ISOLATION_THRESHOLD
        or reputation.conflicting_attestations >= CONFLICTING_ATTESTATION_ISOLATION_THRESHOLD
    )
