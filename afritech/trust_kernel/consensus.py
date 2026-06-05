from __future__ import annotations

from collections import Counter

from afritech.models import (
    EventRecord,
    ReplayAttestation,
    ReplaySubmission,
    VerifierNode,
)
from afritech.trust_kernel.hashing import sha256_payload
from afritech.trust_kernel.replay.engine import replay_all


def submit_replay_result(
    *,
    node_id: str,
    state_hash: str,
    event_count: int | None = None,
    replay_window_hash: str = "",
    signature: str = "",
) -> ReplaySubmission:
    node = VerifierNode.objects.get(node_id=node_id, is_active=True)
    return ReplaySubmission.objects.create(
        verifier_node=node,
        state_hash=state_hash,
        event_count=event_count if event_count is not None else EventRecord.objects.count(),
        replay_window_hash=replay_window_hash,
        signature=signature,
    )


def submit_local_replay_result(node_id: str) -> ReplaySubmission:
    return submit_replay_result(
        node_id=node_id,
        state_hash=replay_all(),
        event_count=EventRecord.objects.count(),
        replay_window_hash=current_replay_window_hash(),
    )


def consensus_state_hash(minimum_nodes: int = 2) -> dict[str, object]:
    latest_by_node: dict[str, ReplaySubmission] = {}
    for submission in ReplaySubmission.objects.select_related("verifier_node").order_by(
        "-created_at",
        "id",
    ):
        latest_by_node.setdefault(submission.verifier_node.node_id, submission)

    counts = Counter(row.state_hash for row in latest_by_node.values())
    if not counts:
        return {
            "accepted": False,
            "state_hash": None,
            "agreement_count": 0,
            "minimum_nodes": minimum_nodes,
        }

    state_hash, agreement_count = counts.most_common(1)[0]
    return {
        "accepted": agreement_count >= minimum_nodes,
        "state_hash": state_hash,
        "agreement_count": agreement_count,
        "minimum_nodes": minimum_nodes,
    }


def submit_replay_attestation(
    *,
    event_id: str,
    node_id: str,
    state_hash: str,
    replay_window_hash: str,
    signature: str,
) -> ReplayAttestation:
    if not signature:
        raise ValueError("attestation.signature is required")
    node = VerifierNode.objects.get(node_id=node_id, is_active=True)
    event = EventRecord.objects.get(event_id=event_id)
    return ReplayAttestation.objects.create(
        event=event,
        verifier_node=node,
        state_hash=state_hash,
        replay_window_hash=replay_window_hash,
        signature=signature,
    )


def event_finality(event: EventRecord, quorum_size: int = 2) -> dict[str, object]:
    attestations = ReplayAttestation.objects.filter(event=event).select_related(
        "verifier_node"
    )
    counts = Counter(row.state_hash for row in attestations)
    if not counts:
        return {
            "final": False,
            "state_hash": None,
            "agreement_count": 0,
            "quorum_size": quorum_size,
            "attestations": [],
        }

    state_hash, agreement_count = counts.most_common(1)[0]
    return {
        "final": agreement_count >= quorum_size,
        "state_hash": state_hash,
        "agreement_count": agreement_count,
        "quorum_size": quorum_size,
        "attestations": [
            {
                "node_id": row.verifier_node.node_id,
                "state_hash": row.state_hash,
                "replay_window_hash": row.replay_window_hash,
                "signature": row.signature,
            }
            for row in attestations.order_by("created_at", "id")
        ],
    }


def current_replay_window_hash() -> str:
    return sha256_payload(
        [
            event.event_hash
            for event in EventRecord.objects.order_by("created_at", "event_id")
        ]
    )
