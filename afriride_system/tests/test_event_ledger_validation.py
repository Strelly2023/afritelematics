from __future__ import annotations

import pytest

from afriride_system.backend.event_ledger import (
    EventLedgerHasher,
    EventLedgerValidationError,
    EventLedgerValidator,
)
from afriride_system.backend.event_signatures import (
    EventSignatureError,
    EventSignatureValidator,
    EventSigner,
    LegalIdentityBinding,
    RegisteredSigner,
    SignerRegistry,
)


def test_phase5_declared_event_ledger_is_internally_admissible() -> None:
    report = EventLedgerValidator().validate(_phase5_events())
    data = report.canonical_dict()

    assert data["event_count"] == 80
    assert data["ride_count"] == 10
    assert data["completed_ride_count"] == 10
    assert data["total_distance_km"] == 69
    assert data["total_duration_min"] == 148
    assert data["total_fare"] == 220.8
    assert data["declared_chain_terminal_hash"] == "h080"
    assert data["hash_mode"] == "declared_token_chain"
    assert data["signature_mode"] == "unsigned"
    assert data["write_enabled"] is False
    assert data["authority"] == "evidence_validation_only"


def test_phase5_declared_event_ledger_rejects_hash_chain_break() -> None:
    events = _phase5_events()
    events[6]["hash_prev"] = "tampered"

    with pytest.raises(EventLedgerValidationError, match="declared hash chain break"):
        EventLedgerValidator().validate(events)


def test_phase5_declared_event_ledger_rejects_incomplete_lifecycle() -> None:
    events = _phase5_events()
    events[4]["type"] = "RIDE_STARTED"

    with pytest.raises(EventLedgerValidationError, match="invalid lifecycle sequence"):
        EventLedgerValidator().validate(events)


def test_phase5_cryptographic_event_ledger_is_sha256_verifiable() -> None:
    events = EventLedgerHasher().materialize_sha256_chain(_phase5_events())
    report = EventLedgerValidator(require_cryptographic_hashes=True).validate(events)
    data = report.canonical_dict()

    assert data["event_count"] == 80
    assert data["ride_count"] == 10
    assert data["completed_ride_count"] == 10
    assert data["total_fare"] == 220.8
    assert data["hash_mode"] == "sha256_canonical_chain"
    assert data["signature_mode"] == "unsigned"
    assert len(data["declared_chain_terminal_hash"]) == 64
    assert data["write_enabled"] is False
    assert data["authority"] == "evidence_validation_only"


def test_phase5_cryptographic_event_ledger_detects_tampering() -> None:
    events = EventLedgerHasher().materialize_sha256_chain(_phase5_events())
    events[19]["distance_km"] = 99

    with pytest.raises(EventLedgerValidationError, match="cryptographic hash mismatch"):
        EventLedgerValidator(require_cryptographic_hashes=True).validate(events)


def test_phase5_declared_tokens_are_not_accepted_as_cryptographic_hashes() -> None:
    with pytest.raises(EventLedgerValidationError, match="cryptographic hash mismatch"):
        EventLedgerValidator(require_cryptographic_hashes=True).validate(_phase5_events())


def test_phase5_signed_cryptographic_event_ledger_is_origin_verified() -> None:
    events, signature_validator = _signed_phase5_events()

    report = EventLedgerValidator(
        require_cryptographic_hashes=True,
        signature_validator=signature_validator,
    ).validate(events)
    data = report.canonical_dict()

    assert data["event_count"] == 80
    assert data["completed_ride_count"] == 10
    assert data["hash_mode"] == "sha256_canonical_chain"
    assert data["signature_mode"] == "rsa_pss_sha256"
    assert data["write_enabled"] is False
    assert data["authority"] == "evidence_validation_only"


def test_phase5_signed_event_ledger_rejects_invalid_signature() -> None:
    events, signature_validator = _signed_phase5_events()
    events[0]["signature"] = events[1]["signature"]

    with pytest.raises(EventSignatureError, match="invalid event signature"):
        EventLedgerValidator(
            require_cryptographic_hashes=True,
            signature_validator=signature_validator,
        ).validate(events)


def test_phase5_signed_event_ledger_rejects_unknown_signer_key() -> None:
    events, signature_validator = _signed_phase5_events()
    events[0]["public_key_id"] = "missing-key"

    with pytest.raises(EventSignatureError, match="unknown signer key"):
        EventLedgerValidator(
            require_cryptographic_hashes=True,
            signature_validator=signature_validator,
        ).validate(events)


def test_phase5_signed_event_ledger_rejects_device_mismatch() -> None:
    events, signature_validator = _signed_phase5_events()
    events[0]["device_id"] = "unexpected-device"

    with pytest.raises(EventSignatureError, match="device mismatch"):
        EventLedgerValidator(
            require_cryptographic_hashes=True,
            signature_validator=signature_validator,
        ).validate(events)


def test_phase5_signature_validation_requires_cryptographic_hashes() -> None:
    _, signature_validator = _signed_phase5_events()

    with pytest.raises(
        EventLedgerValidationError,
        match="signature validation requires cryptographic hash validation",
    ):
        EventLedgerValidator(signature_validator=signature_validator)


def test_phase5_signed_event_ledger_rejects_revoked_key() -> None:
    events, signature_validator = _signed_phase5_events(revoked=True)

    with pytest.raises(EventSignatureError, match="revoked signer key"):
        EventLedgerValidator(
            require_cryptographic_hashes=True,
            signature_validator=signature_validator,
        ).validate(events)


def test_phase5_signed_event_ledger_rejects_expired_key() -> None:
    events, signature_validator = _signed_phase5_events(
        expires_at="2026-05-24T00:00:00Z",
    )

    with pytest.raises(EventSignatureError, match="expired signer key"):
        EventLedgerValidator(
            require_cryptographic_hashes=True,
            signature_validator=signature_validator,
        ).validate(events)


def test_phase5_signed_event_ledger_rejects_inactive_key() -> None:
    events, signature_validator = _signed_phase5_events(status="SUSPENDED")

    with pytest.raises(EventSignatureError, match="inactive signer key"):
        EventLedgerValidator(
            require_cryptographic_hashes=True,
            signature_validator=signature_validator,
        ).validate(events)


def test_phase5_signed_event_ledger_rejects_unverified_identity() -> None:
    events, signature_validator = _signed_phase5_events(identity_verified=False)

    with pytest.raises(EventSignatureError, match="unverified legal identity"):
        EventLedgerValidator(
            require_cryptographic_hashes=True,
            signature_validator=signature_validator,
        ).validate(events)


def test_phase5_signed_event_ledger_rejects_terms_mismatch() -> None:
    events, signature_validator = _signed_phase5_events()
    events[0]["terms_version"] = "v0.9"

    with pytest.raises(EventSignatureError, match="terms version mismatch"):
        EventLedgerValidator(
            require_cryptographic_hashes=True,
            signature_validator=signature_validator,
        ).validate(events)


def _phase5_events() -> list[dict[str, object]]:
    ride_specs = (
        ("2026-05-25", "08:00:00", "08:01:00", "08:01:10", "08:01:30", "08:02:30", "08:03:00", "08:15:00", "drv_001", "ride_001", "rdr_001", 5, 12, 17.50),
        ("2026-05-25", "09:00:00", "09:02:00", "09:02:10", "09:02:40", "09:04:00", "09:05:00", "09:25:00", "drv_002", "ride_002", "rdr_002", 10, 20, 30.00),
        ("2026-05-26", "07:50:00", "07:55:00", "07:55:10", "07:55:20", "07:57:00", "07:58:00", "08:06:00", "drv_003", "ride_003", "rdr_003", 3, 8, 12.50),
        ("2026-05-26", "10:00:00", "10:02:00", "10:02:15", "10:02:30", "10:04:00", "10:05:00", "10:20:00", "drv_001", "ride_004", "rdr_004", 7, 15, 22.00),
        ("2026-05-27", "08:30:00", "08:32:00", "08:32:10", "08:32:25", "08:34:00", "08:35:00", "08:48:00", "drv_002", "ride_005", "rdr_005", 6, 13, 19.80),
        ("2026-05-27", "09:00:00", "09:02:00", "09:02:10", "09:02:25", "09:04:00", "09:05:00", "09:23:00", "drv_003", "ride_006", "rdr_001", 9, 18, 27.50),
        ("2026-05-28", "08:00:00", "08:02:00", "08:02:10", "08:02:20", "08:03:30", "08:04:00", "08:14:00", "drv_001", "ride_007", "rdr_002", 4, 10, 15.00),
        ("2026-05-29", "07:50:00", "07:52:00", "07:52:10", "07:52:20", "07:54:00", "07:55:00", "08:17:00", "drv_002", "ride_008", "rdr_003", 11, 22, 31.00),
        ("2026-05-30", "09:00:00", "09:02:00", "09:02:10", "09:02:20", "09:04:00", "09:05:00", "09:21:00", "drv_003", "ride_009", "rdr_004", 8, 16, 25.00),
        ("2026-05-31", "08:10:00", "08:12:00", "08:12:10", "08:12:20", "08:14:00", "08:15:00", "08:29:00", "drv_001", "ride_010", "rdr_005", 6, 14, 20.50),
    )
    events: list[dict[str, object]] = []
    previous_hash: str | None = None
    event_number = 1

    for (
        day,
        online_at,
        requested_at,
        assigned_at,
        accepted_at,
        arrived_at,
        started_at,
        completed_at,
        driver_id,
        ride_id,
        rider_id,
        distance_km,
        duration_min,
        fare,
    ) in ride_specs:
        ride_events = (
            {
                "type": "DRIVER_ONLINE",
                "driver_id": driver_id,
                "timestamp": f"{day}T{online_at}Z",
            },
            {
                "type": "RIDE_REQUEST_CREATED",
                "ride_id": ride_id,
                "rider_id": rider_id,
                "timestamp": f"{day}T{requested_at}Z",
            },
            {
                "type": "DRIVER_ASSIGNED",
                "ride_id": ride_id,
                "driver_id": driver_id,
                "timestamp": f"{day}T{assigned_at}Z",
            },
            {
                "type": "RIDE_ACCEPTED",
                "ride_id": ride_id,
                "timestamp": f"{day}T{accepted_at}Z",
            },
            {
                "type": "DRIVER_ARRIVED",
                "ride_id": ride_id,
                "timestamp": f"{day}T{arrived_at}Z",
            },
            {
                "type": "RIDE_STARTED",
                "ride_id": ride_id,
                "timestamp": f"{day}T{started_at}Z",
            },
            {
                "type": "RIDE_COMPLETED",
                "ride_id": ride_id,
                "distance_km": distance_km,
                "duration_min": duration_min,
                "timestamp": f"{day}T{completed_at}Z",
            },
            {
                "type": "RECEIPT_GENERATED",
                "ride_id": ride_id,
                "fare": fare,
                "timestamp": f"{day}T{completed_at[:6]}01Z",
            },
        )

        for event in ride_events:
            event_hash = f"h{event_number:03d}"
            events.append(
                {
                    "event_id": f"evt_{event_number:03d}",
                    **event,
                    "hash_prev": previous_hash,
                    "hash": event_hash,
                }
            )
            previous_hash = event_hash
            event_number += 1

    return events


def _signed_phase5_events(
    *,
    status: str = "ACTIVE",
    expires_at: str = "2026-12-31T23:59:59Z",
    revoked: bool = False,
    identity_verified: bool = True,
) -> tuple[list[dict[str, object]], EventSignatureValidator]:
    signer = EventSigner()
    private_key = signer.generate_private_key()
    registry = SignerRegistry(
        (
            RegisteredSigner(
                signer_id="backend",
                public_key_id="backend-key-1",
                public_key_pem=signer.public_key_pem(private_key),
                device_id="backend-ledger-1",
                status=status,
                created_at="2026-01-01T00:00:00Z",
                expires_at=expires_at,
                revoked=revoked,
                revoked_reason="test_revocation" if revoked else None,
                identity=LegalIdentityBinding(
                    full_name="AfriRide Backend Authority",
                    license_id="AFRIRIDE-BACKEND",
                    jurisdiction="AU",
                    verified=identity_verified,
                    verification_method="KYC",
                    legal_acknowledgement=True,
                    terms_version="v1.0",
                ),
            ),
        )
    )
    events = EventLedgerHasher().materialize_sha256_chain(_phase5_events())

    for event in events:
        event["signer_id"] = "backend"
        event["public_key_id"] = "backend-key-1"
        event["device_id"] = "backend-ledger-1"
        event["terms_version"] = "v1.0"
        event["signature"] = signer.sign_hash(str(event["hash"]), private_key)

    return events, EventSignatureValidator(registry)
