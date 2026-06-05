from __future__ import annotations

import base64

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from django.test import Client

from afritech.models import DeviceKey, LedgerRootLog, VerifierNode
from afritech.trust_kernel.consensus import event_finality, submit_replay_attestation
from afritech.trust_kernel.events import process_client_command, process_command
from afritech.trust_kernel.policy import Command
from afritech.trust_kernel.signatures import command_signature_message
from afritech.trust_kernel.verifier_cli import verify_event


@pytest.mark.django_db
def test_client_command_requires_ed25519_signature():
    with pytest.raises(ValueError, match="CLIENT_SIGNED_EVENT_REQUIRED"):
        process_client_command(
            Command(
                event_type="RideAccepted",
                actor_id="D001",
                subject_id="ride-v3-unsigned",
                payload={"ride_id": "ride-v3-unsigned", "status": "accepted"},
                signature={"signature_mode": "development_adapter"},
            )
        )


@pytest.mark.django_db
def test_client_signed_command_appends_evidence_and_ledger_roots():
    private_key, public_key_b64 = _keypair()
    DeviceKey.objects.create(
        actor_id="driver-v3",
        device_id="phone-v3",
        public_key=public_key_b64,
    )
    payload = {"ride_id": "ride-v3", "status": "accepted"}

    event = process_client_command(
        Command(
            event_type="RideAccepted",
            actor_id="driver-v3",
            subject_id="ride-v3",
            payload=payload,
            signature=_signature(
                private_key,
                device_id="phone-v3",
                event_type="RideAccepted",
                actor_id="driver-v3",
                subject_id="ride-v3",
                payload=payload,
            ),
        )
    )

    assert LedgerRootLog.objects.count() == 1
    bundle = event.evidencebundle_set.get()
    assert len(bundle.receipts["bundle_root"]) == 64
    assert len(bundle.bundle_hash) == 64


@pytest.mark.django_db
def test_replay_attestation_quorum_finalizes_event():
    event = process_command(
        Command(
            event_type="RideAccepted",
            actor_id="D001",
            subject_id="ride-finality",
            payload={"ride_id": "ride-finality", "status": "accepted"},
            signature={"signature_mode": "development_adapter"},
        )
    )
    VerifierNode.objects.create(node_id="node-a", region="east")
    VerifierNode.objects.create(node_id="node-b", region="west")

    submit_replay_attestation(
        event_id=str(event.event_id),
        node_id="node-a",
        state_hash="b" * 64,
        replay_window_hash="c" * 64,
        signature="sig-a",
    )
    submit_replay_attestation(
        event_id=str(event.event_id),
        node_id="node-b",
        state_hash="b" * 64,
        replay_window_hash="c" * 64,
        signature="sig-b",
    )

    finality = event_finality(event, quorum_size=2)
    assert finality["final"] is True
    assert finality["agreement_count"] == 2
    assert finality["state_hash"] == "b" * 64


@pytest.mark.django_db
def test_public_verify_includes_bundle_root_and_finality():
    event = process_command(
        Command(
            event_type="RideAccepted",
            actor_id="D001",
            subject_id="ride-v3-public",
            payload={"ride_id": "ride-v3-public", "status": "accepted"},
            signature={"signature_mode": "development_adapter"},
        )
    )

    response = Client().get(f"/api/verify/{event.event_id}", HTTP_ACCEPT="application/json")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["evidence_bundle_root"]) == 64
    assert payload["finality"]["final"] is False
    assert payload["finality"]["quorum_size"] == 2


@pytest.mark.django_db
def test_external_verifier_cli_surface_replays_event():
    event = process_command(
        Command(
            event_type="RideAccepted",
            actor_id="D001",
            subject_id="ride-v3-cli",
            payload={"ride_id": "ride-v3-cli", "status": "accepted"},
            signature={"signature_mode": "development_adapter"},
        )
    )

    result = verify_event(str(event.event_id))

    assert result["valid"] is True
    assert len(str(result["state_hash"])) == 64
    assert result["subject_projection"]["status"] == "accepted"


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
    device_id: str,
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
    return {
        "signature_mode": "ed25519",
        "device_id": device_id,
        "signature": base64.b64encode(private_key.sign(message)).decode("ascii"),
    }
