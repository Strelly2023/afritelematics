from __future__ import annotations

import base64

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from django.test import Client

from afritech.models import DeviceKey, VerifierNode
from afritech.trust_kernel.consensus import consensus_state_hash, submit_replay_result
from afritech.trust_kernel.events import process_command
from afritech.trust_kernel.policy import Command
from afritech.trust_kernel.projections import get_subject_projection, projection_hash
from afritech.trust_kernel.signatures import command_signature_message
from afritech.trust_kernel.witness import guard_witness_consensus


@pytest.mark.django_db
def test_registered_device_requires_valid_ed25519_signature():
    private_key, public_key_b64 = _keypair()
    DeviceKey.objects.create(
        actor_id="driver-crypto",
        device_id="phone-1",
        public_key=public_key_b64,
    )
    payload = {"ride_id": "ride-crypto", "status": "accepted"}

    event = process_command(
        Command(
            event_type="RideAccepted",
            actor_id="driver-crypto",
            subject_id="ride-crypto",
            payload=payload,
            signature=_signature(
                private_key,
                event_type="RideAccepted",
                actor_id="driver-crypto",
                subject_id="ride-crypto",
                payload=payload,
            ),
        )
    )

    assert event.signature["signature_mode"] == "ed25519"


@pytest.mark.django_db
def test_registered_device_rejects_development_adapter_signature():
    _, public_key_b64 = _keypair()
    DeviceKey.objects.create(
        actor_id="driver-registered",
        device_id="phone-1",
        public_key=public_key_b64,
    )

    with pytest.raises(ValueError, match="REGISTERED_DEVICE_REQUIRES_CRYPTOGRAPHIC_SIGNATURE"):
        process_command(
            Command(
                event_type="RideAccepted",
                actor_id="driver-registered",
                subject_id="ride-registered",
                payload={"ride_id": "ride-registered", "status": "accepted"},
                signature={
                    "signature_mode": "development_adapter",
                    "device_id": "phone-1",
                },
            )
        )


@pytest.mark.django_db
def test_trip_completed_requires_two_witnesses_and_persists_consensus():
    with pytest.raises(ValueError, match="TripCompleted requires at least 2 witnesses"):
        process_command(
            Command(
                event_type="TripCompleted",
                actor_id="D001",
                subject_id="ride-witness",
                payload={"ride_id": "ride-witness", "status": "completed"},
                signature={"signature_mode": "development_adapter"},
            )
        )

    event = process_command(
        Command(
            event_type="TripCompleted",
            actor_id="D001",
            subject_id="ride-witness",
            payload={"ride_id": "ride-witness", "status": "completed"},
            signature={"signature_mode": "development_adapter"},
            witnesses=(
                {"verifier_node": "observer-a", "signature": "sig-a"},
                {"verifier_node": "observer-b", "signature": "sig-b"},
            ),
        )
    )

    guard_witness_consensus(event)


@pytest.mark.django_db
def test_reads_are_replay_projection_backed():
    ride_id = "ride-projection"
    process_command(
        Command(
            event_type="RideAccepted",
            actor_id="D001",
            subject_id=ride_id,
            payload={"ride_id": ride_id, "status": "accepted"},
            signature={"signature_mode": "development_adapter"},
        )
    )
    process_command(
        Command(
            event_type="TripCompleted",
            actor_id="D001",
            subject_id=ride_id,
            payload={"ride_id": ride_id, "status": "completed"},
            signature={"signature_mode": "development_adapter"},
            witnesses=(
                {"verifier_node": "observer-a", "signature": "sig-a"},
                {"verifier_node": "observer-b", "signature": "sig-b"},
            ),
        )
    )

    projection = get_subject_projection(ride_id)
    assert projection is not None
    assert projection["status"] == "completed"
    assert len(projection_hash()) == 64


@pytest.mark.django_db
def test_verifier_node_replay_consensus_accepts_matching_hashes():
    VerifierNode.objects.create(node_id="node-a", region="east")
    VerifierNode.objects.create(node_id="node-b", region="west")

    submit_replay_result(node_id="node-a", state_hash="a" * 64, event_count=1)
    submit_replay_result(node_id="node-b", state_hash="a" * 64, event_count=1)

    result = consensus_state_hash(minimum_nodes=2)
    assert result["accepted"] is True
    assert result["state_hash"] == "a" * 64
    assert result["agreement_count"] == 2


@pytest.mark.django_db
def test_public_verification_endpoint_returns_event_proof_surface():
    event = process_command(
        Command(
            event_type="RideAccepted",
            actor_id="D001",
            subject_id="ride-public-verify",
            payload={"ride_id": "ride-public-verify", "status": "accepted"},
            signature={"signature_mode": "development_adapter"},
        )
    )

    response = Client().get(f"/api/verify/{event.event_id}", HTTP_ACCEPT="application/json")

    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is True
    assert payload["event_id"] == str(event.event_id)
    assert len(payload["state_hash"]) == 64
    assert payload["subject_projection"]["status"] == "accepted"


def _keypair() -> tuple[Ed25519PrivateKey, str]:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return private_key, base64.b64encode(public_key).decode("ascii")


def _signature(
    private_key: Ed25519PrivateKey,
    *,
    event_type: str,
    actor_id: str,
    subject_id: str,
    payload: dict[str, object],
) -> dict[str, str]:
    message = command_signature_message(
        event_type=event_type,
        actor_id=actor_id,
        subject_id=subject_id,
        payload=payload,
    )
    signature = private_key.sign(message)
    return {
        "signature_mode": "ed25519",
        "device_id": "phone-1",
        "signature": base64.b64encode(signature).decode("ascii"),
    }
