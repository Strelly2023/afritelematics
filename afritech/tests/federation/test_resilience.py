from __future__ import annotations

from importlib import import_module

import pytest

from afritech.models import ConsensusIncident, NodeReputation, ReplayDivergenceRecord

protocol = import_module("afritech.federation.protocol")
resilience = import_module("afritech.federation.resilience")
FederationMessage = protocol.FederationMessage
FederationProtocolError = protocol.FederationProtocolError
MAX_CLOCK_SKEW_SECONDS = protocol.MAX_CLOCK_SKEW_SECONDS
MESSAGE_EXPIRY_SECONDS = protocol.MESSAGE_EXPIRY_SECONDS
register_federation_node = protocol.register_federation_node
verify_federation_message = protocol.verify_federation_message
CONSENSUS_FINALIZED = resilience.CONSENSUS_FINALIZED
CONSENSUS_NO_AGREEMENT = resilience.CONSENSUS_NO_AGREEMENT
CONSENSUS_UNRESOLVED = resilience.CONSENSUS_UNRESOLVED
REPLAY_DIVERGENCE = resilience.REPLAY_DIVERGENCE
evaluate_state_hash_consensus = resilience.evaluate_state_hash_consensus
record_node_signal = resilience.record_node_signal
record_replay_divergence = resilience.record_replay_divergence


def test_consensus_accepts_majority_and_exposes_minority_nodes():
    result = evaluate_state_hash_consensus(
        {"node-a": "state-1", "node-b": "state-1", "node-c": "state-2"}
    )

    assert result.status == CONSENSUS_FINALIZED
    assert result.accepted is True
    assert result.state_hash == "state-1"
    assert result.minority_nodes == ("node-c",)
    assert result.finality_halted is False


@pytest.mark.django_db
def test_split_consensus_halts_finality_and_records_incident():
    result = evaluate_state_hash_consensus(
        {
            "node-a": "state-1",
            "node-b": "state-1",
            "node-c": "state-2",
            "node-d": "state-2",
        },
        persist_incident=True,
    )

    assert result.status == CONSENSUS_UNRESOLVED
    assert result.accepted is False
    assert result.finality_halted is True
    assert ConsensusIncident.objects.get().status == CONSENSUS_UNRESOLVED


@pytest.mark.django_db
def test_no_agreement_halts_finality():
    result = evaluate_state_hash_consensus(
        {"node-a": "state-1", "node-b": "state-2", "node-c": "state-3"},
        persist_incident=True,
    )

    assert result.status == CONSENSUS_NO_AGREEMENT
    assert result.accepted is False
    assert ConsensusIncident.objects.get().finality_halted is True


@pytest.mark.django_db
def test_reputation_isolates_repeatedly_faulty_node():
    for _ in range(3):
        reputation = record_node_signal(
            node_id="node-bad",
            signature_failure=True,
            reason="invalid federation signature",
        )

    assert reputation.is_isolated is True
    assert reputation.voting_weight == 0.0
    assert NodeReputation.objects.get(node_id="node-bad").signature_failures == 3


@pytest.mark.django_db
def test_replay_divergence_record_halts_finality():
    record = record_replay_divergence(
        expected_state_hash="a" * 64,
        observed_state_hash="b" * 64,
        code_version="afritech-test",
        root_cause="software mismatch",
    )

    assert record.status == REPLAY_DIVERGENCE
    assert record.finality_halted is True
    assert ReplayDivergenceRecord.objects.count() == 1


@pytest.mark.django_db
def test_federation_message_enforces_tight_time_windows():
    register_federation_node(
        node_id="clock-node",
        region="Africa-East",
        public_key="pub-clock",
        endpoint="https://clock.example.test",
    )
    message = FederationMessage(
        message_id="msg-expired",
        sender_node_id="clock-node",
        receiver_node_id="local-node",
        timestamp=100,
        payload={},
        payload_hash="wrong",
        signature="bad",
        public_key="pub-clock",
    )

    assert MAX_CLOCK_SKEW_SECONDS == 30
    assert MESSAGE_EXPIRY_SECONDS == 60
    with pytest.raises(FederationProtocolError, match="timestamp"):
        verify_federation_message(message, now=200)
