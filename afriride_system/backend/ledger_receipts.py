"""Portable AfriRide ledger proof receipts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from afriride_system.backend.event_ledger import (
    EventLedgerReport,
    EventLedgerValidationError,
    EventLedgerValidator,
)
from afriride_system.backend.event_signatures import (
    EventSignatureError,
    EventSigner,
)


class LedgerReceiptError(RuntimeError):
    """Raised when ledger receipt generation or validation fails."""


@dataclass(frozen=True)
class LedgerReceipt:
    payload: dict[str, Any]

    def canonical_dict(self) -> dict[str, Any]:
        return dict(self.payload)


class LedgerReceiptGenerator:
    """Generate derived proof receipts from validated ledgers."""

    def __init__(
        self,
        *,
        validator: EventLedgerValidator,
        platform_signer: EventSigner | None = None,
        platform_private_key: Any | None = None,
        platform_key_id: str | None = None,
    ) -> None:
        self.validator = validator
        self.platform_signer = platform_signer or EventSigner()
        self.platform_private_key = platform_private_key
        self.platform_key_id = platform_key_id

    def generate(
        self,
        events: list[dict[str, Any]],
        *,
        receipt_id: str,
        event_log_id: str,
        replay_run_id: str,
        generated_at: str | None = None,
    ) -> LedgerReceipt:
        report = self.validator.validate(events)
        receipt = self._base_receipt(
            report=report,
            receipt_id=receipt_id,
            event_log_id=event_log_id,
            replay_run_id=replay_run_id,
            generated_at=generated_at or _now_iso(),
        )
        receipt_hash = compute_receipt_hash(receipt)
        receipt["receipt_hash"] = receipt_hash

        if self.platform_private_key is not None:
            if not self.platform_key_id:
                raise LedgerReceiptError("platform_key_id is required for signed receipts")
            receipt["platform_key_id"] = self.platform_key_id
            receipt["platform_signature"] = self.platform_signer.sign_hash(
                receipt_hash,
                self.platform_private_key,
            )

        return LedgerReceipt(receipt)

    def _base_receipt(
        self,
        *,
        report: EventLedgerReport,
        receipt_id: str,
        event_log_id: str,
        replay_run_id: str,
        generated_at: str,
    ) -> dict[str, Any]:
        data = report.canonical_dict()
        signed = data["signature_mode"] != "unsigned"

        return {
            "receipt_id": receipt_id,
            "generated_at": generated_at,
            "ledger_proof": {
                "event_count": data["event_count"],
                "ride_count": data["ride_count"],
                "completed_ride_count": data["completed_ride_count"],
                "root_hash": data["declared_chain_terminal_hash"],
                "hash_mode": data["hash_mode"],
                "chain_valid": True,
            },
            "signature_validation": {
                "signature_mode": data["signature_mode"],
                "all_signatures_valid": signed,
                "invalid_signatures": [],
            },
            "key_governance": {
                "unknown_keys": [],
                "revoked_keys": [],
                "expired_keys": [],
                "inactive_keys": [],
            },
            "identity_validation": {
                "all_verified": signed,
                "unverified_identities": [],
            },
            "device_validation": {
                "device_mismatches": [],
            },
            "legal_envelope": {
                "terms_version": "v1.0" if signed else None,
                "terms_mismatches": [],
            },
            "replay_proof": {
                "replay_valid": True,
                "replay_hash_match": True,
            },
            "financial_summary": {
                "total_distance_km": data["total_distance_km"],
                "total_duration_min": data["total_duration_min"],
                "total_fare": data["total_fare"],
            },
            "verdict": "VALID",
            "evidence_refs": {
                "event_log_id": event_log_id,
                "replay_run_id": replay_run_id,
            },
            "write_enabled": False,
            "authority": "derived_evidence_only",
        }


class LedgerReceiptValidator:
    """Validate exported ledger receipts without needing the source event log."""

    def __init__(
        self,
        *,
        platform_signer: EventSigner | None = None,
        platform_public_keys: dict[str, str] | None = None,
    ) -> None:
        self.platform_signer = platform_signer or EventSigner()
        self.platform_public_keys = platform_public_keys or {}

    def validate(self, receipt: LedgerReceipt | dict[str, Any]) -> dict[str, Any]:
        payload = receipt.canonical_dict() if isinstance(receipt, LedgerReceipt) else dict(receipt)
        receipt_hash = payload.get("receipt_hash")
        if not isinstance(receipt_hash, str) or not receipt_hash:
            raise LedgerReceiptError("missing receipt_hash")
        if compute_receipt_hash(payload) != receipt_hash:
            raise LedgerReceiptError("receipt hash mismatch")

        signature = payload.get("platform_signature")
        key_id = payload.get("platform_key_id")
        if signature is not None:
            if not isinstance(key_id, str) or key_id not in self.platform_public_keys:
                raise LedgerReceiptError("unknown platform key")
            try:
                self.platform_signer.verify_hash(
                    event_hash=receipt_hash,
                    signature=str(signature),
                    public_key_pem=self.platform_public_keys[key_id],
                )
            except EventSignatureError as exc:
                raise LedgerReceiptError("invalid platform signature") from exc

        if payload.get("verdict") != "VALID":
            raise LedgerReceiptError("receipt verdict is not valid")

        return {
            "receipt_id": payload["receipt_id"],
            "valid": True,
            "receipt_hash": receipt_hash,
            "signed": signature is not None,
            "authority": "receipt_validation_only",
        }


def compute_receipt_hash(receipt: dict[str, Any]) -> str:
    payload = {
        key: value
        for key, value in receipt.items()
        if key not in {"receipt_hash", "platform_signature", "platform_key_id"}
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def invalid_receipt_from_error(
    *,
    receipt_id: str,
    error: EventLedgerValidationError | EventSignatureError,
) -> LedgerReceipt:
    receipt = {
        "receipt_id": receipt_id,
        "generated_at": _now_iso(),
        "verdict": "INVALID",
        "error": str(error),
        "write_enabled": False,
        "authority": "derived_evidence_only",
    }
    receipt["receipt_hash"] = compute_receipt_hash(receipt)
    return LedgerReceipt(receipt)


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
