from __future__ import annotations

import base64
from importlib import import_module

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from afritech.trust_kernel.hashing import canonical_json

discovery = import_module("afritech.federation.discovery")
NodeAnnouncement = discovery.NodeAnnouncement
NodeDiscoveryError = discovery.NodeDiscoveryError
accept_node_announcement = discovery.accept_node_announcement
peer_exchange_records = discovery.peer_exchange_records


@pytest.mark.django_db
def test_node_announcement_requires_valid_signature_before_acceptance():
    private_key, public_key = _keypair()
    announcement = NodeAnnouncement(
        node_id="africa-east-1",
        public_key=public_key,
        region="Africa-East",
        capabilities=("verification", "orchestration"),
        endpoint="https://east.example.test",
        governance_version="1",
        signature="",
    )
    signed = NodeAnnouncement(
        **{
            **announcement.__dict__,
            "signature": _sign(private_key, canonical_json(announcement.signing_payload()).encode("utf-8")),
        }
    )

    record = accept_node_announcement(signed)

    assert record.verified is True
    assert peer_exchange_records()[0]["node_id"] == "africa-east-1"


@pytest.mark.django_db
def test_node_announcement_rejects_empty_capabilities():
    private_key, public_key = _keypair()
    announcement = NodeAnnouncement(
        node_id="bad-node",
        public_key=public_key,
        region="Africa-East",
        capabilities=(),
        endpoint="https://bad.example.test",
        governance_version="1",
        signature="",
    )
    signed = NodeAnnouncement(
        **{
            **announcement.__dict__,
            "signature": _sign(private_key, canonical_json(announcement.signing_payload()).encode("utf-8")),
        }
    )

    with pytest.raises(NodeDiscoveryError, match="capabilities"):
        accept_node_announcement(signed)


def _keypair() -> tuple[Ed25519PrivateKey, str]:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return private_key, base64.b64encode(public_key).decode("ascii")


def _sign(private_key: Ed25519PrivateKey, message: bytes) -> str:
    return base64.b64encode(private_key.sign(message)).decode("ascii")
