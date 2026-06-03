from __future__ import annotations

import pytest

from afriride_system.backend.event_ledger import (
    EventLedgerHasher,
    EventLedgerValidationError,
    EventLedgerValidator,
)
from afriride_system.backend.event_signatures import (
    EventSignatureValidator,
    EventSigner,
    LegalIdentityBinding,
    RegisteredSigner,
    SignerRegistry,
)
from afriride_system.backend.ledger_receipts import (
    LedgerReceiptError,
    LedgerReceiptGenerator,
    LedgerReceiptValidator,
    invalid_receipt_from_error,
)
from afriride_system.tests.test_event_ledger_validation import _phase5_events


def test_ledger_receipt_exports_valid_derived_proof() -> None:
    events, signature_validator = _signed_events()
    receipt = LedgerReceiptGenerator(
        validator=EventLedgerValidator(
            require_cryptographic_hashes=True,
            signature_validator=signature_validator,
        )
    ).generate(
        events,
        receipt_id="rcpt_phase5_v1",
        event_log_id="log_phase5",
        replay_run_id="replay_phase5",
        generated_at="2026-06-01T14:00:00Z",
    )
    data = receipt.canonical_dict()

    assert data["verdict"] == "VALID"
    assert data["ledger_proof"]["event_count"] == 70
    assert data["ledger_proof"]["root_hash"] == events[-1]["hash"]
    assert data["signature_validation"]["signature_mode"] == "rsa_pss_sha256"
    assert data["signature_validation"]["all_signatures_valid"] is True
    assert data["identity_validation"]["all_verified"] is True
    assert data["replay_proof"]["replay_valid"] is True
    assert data["financial_summary"]["total_fare"] == 220.8
    assert len(data["receipt_hash"]) == 64
    assert data["write_enabled"] is False
    assert data["authority"] == "derived_evidence_only"

    validation = LedgerReceiptValidator().validate(receipt)
    assert validation["valid"] is True
    assert validation["signed"] is False


def test_ledger_receipt_can_be_platform_signed_and_verified() -> None:
    events, signature_validator = _signed_events()
    signer = EventSigner()
    private_key = signer.generate_private_key()
    public_key = signer.public_key_pem(private_key)
    receipt = LedgerReceiptGenerator(
        validator=EventLedgerValidator(
            require_cryptographic_hashes=True,
            signature_validator=signature_validator,
        ),
        platform_private_key=private_key,
        platform_key_id="platform-key-1",
    ).generate(
        events,
        receipt_id="rcpt_phase5_signed_v1",
        event_log_id="log_phase5",
        replay_run_id="replay_phase5",
        generated_at="2026-06-01T14:00:00Z",
    )
    data = receipt.canonical_dict()

    assert data["platform_key_id"] == "platform-key-1"
    assert data["platform_signature"]

    validation = LedgerReceiptValidator(
        platform_public_keys={"platform-key-1": public_key}
    ).validate(receipt)
    assert validation["valid"] is True
    assert validation["signed"] is True


def test_ledger_receipt_validator_rejects_tampering() -> None:
    events, signature_validator = _signed_events()
    receipt = LedgerReceiptGenerator(
        validator=EventLedgerValidator(
            require_cryptographic_hashes=True,
            signature_validator=signature_validator,
        )
    ).generate(
        events,
        receipt_id="rcpt_phase5_v1",
        event_log_id="log_phase5",
        replay_run_id="replay_phase5",
        generated_at="2026-06-01T14:00:00Z",
    )
    payload = receipt.canonical_dict()
    payload["financial_summary"]["total_fare"] = 1

    with pytest.raises(LedgerReceiptError, match="receipt hash mismatch"):
        LedgerReceiptValidator().validate(payload)


def test_ledger_receipt_generation_rejects_invalid_ledger() -> None:
    events, signature_validator = _signed_events()
    events[0]["signature"] = events[1]["signature"]

    with pytest.raises(Exception, match="invalid event signature"):
        LedgerReceiptGenerator(
            validator=EventLedgerValidator(
                require_cryptographic_hashes=True,
                signature_validator=signature_validator,
            )
        ).generate(
            events,
            receipt_id="rcpt_invalid",
            event_log_id="log_phase5",
            replay_run_id="replay_phase5",
            generated_at="2026-06-01T14:00:00Z",
        )


def test_invalid_receipt_is_exportable_but_not_validated_as_success() -> None:
    receipt = invalid_receipt_from_error(
        receipt_id="rcpt_invalid",
        error=EventLedgerValidationError("chain failed"),
    )

    with pytest.raises(LedgerReceiptError, match="receipt verdict is not valid"):
        LedgerReceiptValidator().validate(receipt)


def _signed_events() -> tuple[list[dict[str, object]], EventSignatureValidator]:
    signer = EventSigner()
    private_key = signer.generate_private_key()
    registry = SignerRegistry(
        (
            RegisteredSigner(
                signer_id="backend",
                public_key_id="backend-key-1",
                public_key_pem=signer.public_key_pem(private_key),
                device_id="backend-ledger-1",
                status="ACTIVE",
                created_at="2026-01-01T00:00:00Z",
                expires_at="2026-12-31T23:59:59Z",
                identity=LegalIdentityBinding(
                    full_name="AfriRide Backend Authority",
                    license_id="AFRIRIDE-BACKEND",
                    jurisdiction="AU",
                    verified=True,
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
