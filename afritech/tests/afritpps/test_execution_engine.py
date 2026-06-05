from __future__ import annotations

import base64

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from afritech.afritpps.execution_engine import (
    AfriTPPSOperationIntent,
    execute_operation,
)
from afritech.models import DeviceKey, EventRecord, EvidenceBundle
from afritech.trust_kernel.signatures import command_signature_message


@pytest.mark.django_db
def test_execute_operation_generates_trust_kernel_event_and_verified_outcome():
    outcome = execute_operation(
        AfriTPPSOperationIntent(
            operation_id="op.mobility.dispatch.001",
            domain="AfriRide",
            actor_id="operator-001",
            subject_id="ride-tpps-001",
            action="dispatch_driver",
            expected_outcome="driver dispatched",
            payload={"ride_id": "ride-tpps-001", "driver_id": "D001"},
            signature={"signature_mode": "development_adapter"},
        )
    )

    event = EventRecord.objects.get(event_id=outcome.event_id)
    bundle = EvidenceBundle.objects.get(event=event)

    assert outcome.verified is True
    assert event.event_type == "AfriTPPSOperationExecuted"
    assert bundle.bundle_hash == outcome.evidence_bundle_hash
    assert len(outcome.evidence_bundle_root) == 64
    assert outcome.subject_projection["status"] == "executed"


@pytest.mark.django_db
def test_execute_operation_can_require_client_signed_intent():
    private_key, public_key_b64 = _keypair()
    DeviceKey.objects.create(
        actor_id="operator-signed",
        device_id="device-signed",
        public_key=public_key_b64,
    )
    payload = {
        "operation_id": "op.signed.001",
        "domain": "AfriRide",
        "action": "dispatch_driver",
        "expected_outcome": "driver dispatched",
        "payload": {"ride_id": "ride-signed", "driver_id": "D001"},
        "status": "executed",
    }

    outcome = execute_operation(
        AfriTPPSOperationIntent(
            operation_id="op.signed.001",
            domain="AfriRide",
            actor_id="operator-signed",
            subject_id="ride-signed",
            action="dispatch_driver",
            expected_outcome="driver dispatched",
            payload={"ride_id": "ride-signed", "driver_id": "D001"},
            signature=_signature(
                private_key,
                device_id="device-signed",
                event_type="AfriTPPSOperationExecuted",
                actor_id="operator-signed",
                subject_id="ride-signed",
                payload=payload,
            ),
        ),
        require_client_signature=True,
    )

    assert outcome.verified is True
    assert EventRecord.objects.get(event_id=outcome.event_id).signature[
        "signature_mode"
    ] == "ed25519"


@pytest.mark.django_db
def test_execute_operation_rejects_unsigned_intent_when_client_signature_required():
    with pytest.raises(ValueError, match="CLIENT_SIGNED_EVENT_REQUIRED"):
        execute_operation(
            AfriTPPSOperationIntent(
                operation_id="op.unsigned.001",
                domain="AfriRide",
                actor_id="operator-unsigned",
                subject_id="ride-unsigned",
                action="dispatch_driver",
                expected_outcome="driver dispatched",
                payload={"ride_id": "ride-unsigned", "driver_id": "D001"},
                signature={"signature_mode": "development_adapter"},
            ),
            require_client_signature=True,
        )


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
