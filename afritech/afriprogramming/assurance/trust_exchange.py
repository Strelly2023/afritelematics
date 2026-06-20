from __future__ import annotations

from typing import Any

from afritech.afriprogramming.assurance.cert_signer import verify_signed_certification
from afritech.afriprogramming.persistence import PlatformStore, get_platform_store


class TrustExchangeService:
    def __init__(self, repository: PlatformStore | None = None) -> None:
        self.repository = repository or get_platform_store()

    def verify_public_receipt(self, *, organization_id: str, receipt: dict[str, Any]) -> dict[str, Any]:
        public = {
            "organization_id": receipt.get("organization_id"),
            "receipt_hash": receipt.get("receipt_hash"),
            "proof_hash": receipt.get("proof_hash"),
            "audit_hash": receipt.get("audit_hash"),
            "certification_hash": receipt.get("certification_hash"),
            "signature": receipt.get("signature"),
            "public_key_id": receipt.get("public_key_id"),
            "payload": receipt.get("payload"),
        }
        verification = verify_signed_certification(public)
        valid = bool(verification.get("valid"))
        details = {
            "verification": verification,
            "receipt_hash": public["receipt_hash"],
            "proof_hash": public["proof_hash"],
            "audit_hash": public["audit_hash"],
            "certification_hash": public["certification_hash"],
        }
        self.repository.store_trust_exchange_event(
            organization_id=organization_id,
            external_organization_id=str(receipt.get("organization_id", "")),
            receipt_hash=str(public["receipt_hash"] or ""),
            proof_hash=str(public["proof_hash"] or ""),
            audit_hash=str(public["audit_hash"] or ""),
            certification_hash=str(public["certification_hash"] or ""),
            valid=valid,
            details=details,
        )
        return {
            "valid": valid,
            "reason": verification.get("reason") if not valid else None,
            "receipt_hash": public["receipt_hash"],
            "origin_organization": receipt.get("organization_id"),
        }

    def events(self, *, organization_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        return self.repository.list_trust_exchange_events(organization_id=organization_id, limit=limit)
