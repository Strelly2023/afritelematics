from __future__ import annotations

import pytest

from afritech.models import EventRecord
from afritech.trust_kernel.events import process_command
from afritech.trust_kernel.policy import Command
from afritech.trust_kernel.replay.engine import replay_all


@pytest.mark.django_db
def test_trust_kernel_appends_hash_linked_event_and_replays_deterministically():
    event = process_command(
        Command(
            event_type="DriverAvailabilityChanged",
            actor_id="D001",
            subject_id="D001",
            payload={"status": "available"},
            signature={"signature_mode": "development_adapter"},
        )
    )

    assert event.prev_hash == "GENESIS"
    assert len(event.event_hash) == 64
    first_hash = replay_all()
    second_hash = replay_all()
    assert first_hash == second_hash


@pytest.mark.django_db
def test_trust_kernel_blocks_event_mutation():
    event = process_command(
        Command(
            event_type="RideAccepted",
            actor_id="D001",
            subject_id="ride-001",
            payload={"ride_id": "ride-001", "status": "accepted"},
            signature={"signature_mode": "development_adapter"},
        )
    )

    event.payload = {"ride_id": "ride-001", "status": "tampered"}
    with pytest.raises(ValueError, match="IMMUTABLE_EVENT_RECORD_VIOLATION"):
        event.save()


@pytest.mark.django_db
def test_trust_kernel_enforces_signature_metadata():
    with pytest.raises(ValueError, match="signature.signature_mode is required"):
        process_command(
            Command(
                event_type="RideAccepted",
                actor_id="D001",
                subject_id="ride-001",
                payload={"ride_id": "ride-001", "status": "accepted"},
                signature={},
            )
        )


@pytest.mark.django_db
def test_trust_kernel_enforces_high_value_witness_policy():
    with pytest.raises(ValueError, match="PaymentCaptured requires at least 3 witnesses"):
        process_command(
            Command(
                event_type="PaymentCaptured",
                actor_id="customer-001",
                subject_id="payment-001",
                payload={"amount": 5000, "currency": "BIF"},
                signature={"signature_mode": "development_adapter"},
            )
        )

    event = process_command(
        Command(
            event_type="PaymentCaptured",
            actor_id="customer-001",
            subject_id="payment-001",
            payload={"amount": 5000, "currency": "BIF"},
            signature={"signature_mode": "development_adapter"},
            witnesses=(
                {"verifier_node": "node-a", "signature": "sig-a"},
                {"verifier_node": "node-b", "signature": "sig-b"},
                {"verifier_node": "node-c", "signature": "sig-c"},
            ),
        )
    )

    assert EventRecord.objects.get(event_id=event.event_id).event_type == "PaymentCaptured"
