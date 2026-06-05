from __future__ import annotations

import pytest
import base64
from importlib import import_module
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from afritech.models import CrossNodeEventShare, FederatedPolicyRecord, FederationNode
from afritech.trust_kernel.hashing import canonical_json

protocol = import_module("afritech.federation.protocol")
FederationMessage = protocol.FederationMessage
FederationProtocolError = protocol.FederationProtocolError
apply_federated_policy = protocol.apply_federated_policy
federated_state_agreement = protocol.federated_state_agreement
federation_message_payload_hash = protocol.federation_message_payload_hash
register_federation_node = protocol.register_federation_node
event_share_from_message = protocol.event_share_from_message
share_remote_event = protocol.share_remote_event
verify_federation_message = protocol.verify_federation_message


@pytest.mark.django_db
def test_federation_requires_independent_verification_before_sharing():
    register_federation_node(
        node_id="africa-east",
        region="Africa-East",
        public_key="pub-east",
        endpoint="https://east.example.test",
    )

    with pytest.raises(FederationProtocolError, match="independently replay-verified"):
        share_remote_event(
            source_node_id="africa-east",
            remote_event_id="evt-1",
            remote_event_hash="a" * 64,
            remote_bundle_root="b" * 64,
            remote_state_hash="c" * 64,
            signature="sig-east",
            independently_verified=False,
        )

    assert CrossNodeEventShare.objects.count() == 0


@pytest.mark.django_db
def test_federated_state_agreement_counts_verified_nodes_only():
    register_federation_node(
        node_id="africa-east",
        region="Africa-East",
        public_key="pub-east",
        endpoint="https://east.example.test",
    )
    register_federation_node(
        node_id="africa-west",
        region="Africa-West",
        public_key="pub-west",
        endpoint="https://west.example.test",
    )

    share_remote_event(
        source_node_id="africa-east",
        remote_event_id="evt-east",
        remote_event_hash="a" * 64,
        remote_bundle_root="b" * 64,
        remote_state_hash="c" * 64,
        signature="sig-east",
        independently_verified=True,
    )
    share_remote_event(
        source_node_id="africa-west",
        remote_event_id="evt-west",
        remote_event_hash="d" * 64,
        remote_bundle_root="e" * 64,
        remote_state_hash="c" * 64,
        signature="sig-west",
        independently_verified=True,
    )

    agreement = federated_state_agreement(minimum_nodes=2)
    assert FederationNode.objects.count() == 2
    assert agreement["accepted"] is True
    assert agreement["state_hash"] == "c" * 64
    assert agreement["agreement_count"] == 2


@pytest.mark.django_db
def test_federation_rejects_invalid_hash_material():
    register_federation_node(
        node_id="eu-node",
        region="Europe",
        public_key="pub-eu",
        endpoint="https://eu.example.test",
    )

    with pytest.raises(FederationProtocolError, match="remote_event_hash"):
        share_remote_event(
            source_node_id="eu-node",
            remote_event_id="evt-eu",
            remote_event_hash="short",
            remote_bundle_root="b" * 64,
            remote_state_hash="c" * 64,
            signature="sig-eu",
            independently_verified=True,
        )


@pytest.mark.django_db
def test_signed_federation_message_accepts_verified_event_share():
    private_key, public_key = _keypair()
    register_federation_node(
        node_id="gov-node",
        region="Africa-East",
        public_key=public_key,
        endpoint="https://gov.example.test",
        node_type="government",
    )
    payload = {
        "event_id": "evt-gov",
        "event_hash": "a" * 64,
        "bundle_root": "b" * 64,
        "state_hash": "c" * 64,
        "domain": "AfriRide",
        "operation": "TripCompleted",
    }
    payload_hash = federation_message_payload_hash(payload)
    message = FederationMessage(
        message_id="msg-1",
        sender_node_id="gov-node",
        receiver_node_id="local-node",
        timestamp=1000,
        payload=payload,
        payload_hash=payload_hash,
        signature=_sign(private_key, payload_hash.encode("utf-8")),
        public_key=public_key,
    )

    verify_federation_message(message, now=1000)
    share = event_share_from_message(
        message,
        now=1000,
        independently_verified=True,
        verification_notes="local replay matched",
    )

    assert share.independently_verified is True
    assert share.remote_event_hash == "a" * 64


@pytest.mark.django_db
def test_federation_message_rejects_replay_window_violation():
    private_key, public_key = _keypair()
    register_federation_node(
        node_id="university-node",
        region="Africa-West",
        public_key=public_key,
        endpoint="https://uni.example.test",
    )
    payload = {"event_id": "evt-old", "event_hash": "a" * 64}
    payload_hash = federation_message_payload_hash(payload)
    message = FederationMessage(
        message_id="msg-old",
        sender_node_id="university-node",
        receiver_node_id="local-node",
        timestamp=1,
        payload=payload,
        payload_hash=payload_hash,
        signature=_sign(private_key, payload_hash.encode("utf-8")),
        public_key=public_key,
    )

    with pytest.raises(FederationProtocolError, match="timestamp"):
        verify_federation_message(message, now=1000)


@pytest.mark.django_db
def test_federated_policy_requires_signature_before_apply():
    private_key, public_key = _keypair()
    rules = {"TripCompleted": {"min_witnesses": 2}}
    payload = {
        "policy_id": "policy.trip.completed",
        "version": "1",
        "rules": rules,
        "issuing_authority": "AfriCPPT",
    }

    policy = apply_federated_policy(
        policy_id="policy.trip.completed",
        version="1",
        rules=rules,
        issuing_authority="AfriCPPT",
        signature=_sign(private_key, canonical_json(payload).encode("utf-8")),
        public_key=public_key,
    )

    assert policy.verified is True
    assert FederatedPolicyRecord.objects.count() == 1


def _keypair() -> tuple[Ed25519PrivateKey, str]:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return private_key, base64.b64encode(public_key).decode("ascii")


def _sign(private_key: Ed25519PrivateKey, message: bytes) -> str:
    return base64.b64encode(private_key.sign(message)).decode("ascii")
