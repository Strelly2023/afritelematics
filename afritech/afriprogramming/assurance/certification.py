from __future__ import annotations

from typing import Any

from afritech.afriprogramming.assurance.assurance_engine import AssuranceService
from afritech.afriprogramming.assurance.cert_signer import (
    DEFAULT_CERTIFICATION_KEY_ID,
    hash_payload,
    issue_signed_certification,
    verify_signed_certification,
)
from afritech.afriprogramming.persistence import PlatformStore, get_platform_store


class CertificationService:
    def __init__(self, repository: PlatformStore | None = None) -> None:
        self.repository = repository or get_platform_store()
        self.assurance_service = AssuranceService(self.repository)

    def issue(
        self,
        *,
        organization_id: str,
        certification_type: str = "CONTROLLED_OPERATIONAL_STATE",
        public_key_id: str = DEFAULT_CERTIFICATION_KEY_ID,
    ) -> dict[str, Any]:
        trust = self.repository.latest_trust_score(organization_id=organization_id)
        if trust is None:
            trust = self.assurance_service.trust_service.compute_for_org(organization_id)
        latest_assurance = self.repository.latest_assurance_record(organization_id=organization_id)
        audit_chain_hash = self.repository.get_last_audit_hash(organization_id=organization_id) or ""
        proof_count = len(self.repository.list_proofs(organization_id=organization_id))
        receipt_count = len(self.repository.list_deployment_receipts(organization_id=organization_id))
        assurance_status = (
            latest_assurance["assurance_status"]
            if latest_assurance is not None
            else "review"
        )
        base_payload = {
            "organization_id": organization_id,
            "certification_type": certification_type,
            "trust_score": int(trust["trust_score"]),
            "assurance_status": assurance_status,
            "audit_chain_hash": audit_chain_hash,
            "proof_count": proof_count,
            "receipt_count": receipt_count,
            "classification": "VERIFIED_OPERATIONAL_STATE"
            if int(trust["trust_score"]) >= 90 and audit_chain_hash
            else "CONTROLLED_OPERATIONAL_STATE",
            "public_key_id": public_key_id,
        }
        signed = issue_signed_certification(base_payload)
        certification = self.repository.store_certification_record(
            organization_id=organization_id,
            certification_type=certification_type,
            trust_score=int(trust["trust_score"]),
            assurance_status=assurance_status,
            audit_chain_hash=audit_chain_hash,
            proof_count=proof_count,
            receipt_count=receipt_count,
            certification_hash=signed["certification_hash"],
            signature=signed["signature"],
            public_key_id=public_key_id,
            issued_at=signed["issued_at"],
            payload=signed["payload"],
        )
        self.repository.publish_trust_stream_event(
            organization_id=organization_id,
            event_type="certification.issued",
            payload=certification,
        )
        self.repository.track_usage(
            organization_id=organization_id,
            metric="certification.issue",
            amount=1,
            context={
                "certification_type": certification_type,
                "certification_hash": signed["certification_hash"],
            },
        )
        return {
            **certification,
            "classification": base_payload["classification"],
            "public_key_id": public_key_id,
            "signature_valid": True,
        }

    def verify(self, certification: dict[str, Any]) -> dict[str, Any]:
        return verify_signed_certification(certification)

    def latest(self, organization_id: str) -> dict[str, Any] | None:
        return self.repository.latest_certification_record(organization_id=organization_id)

    def summary(self, organization_id: str) -> dict[str, Any]:
        latest = self.latest(organization_id)
        trust = self.repository.latest_trust_score(organization_id=organization_id)
        if trust is None:
            trust = self.assurance_service.trust_service.compute_for_org(organization_id)
        audit_valid = self.repository.verify_audit_chain(organization_id=organization_id)
        assurance_records = self.repository.list_assurance_records(organization_id=organization_id, limit=50)
        classification = latest["certification_type"] if latest else "CONTROLLED_OPERATIONAL_STATE"
        issued = bool(
            trust["trust_score"] >= 80
            and audit_valid
            and any(record["assurance_status"] == "verified" for record in assurance_records)
        )
        payload = {
            "organization_id": organization_id,
            "certification_type": classification,
            "trust_score": int(trust["trust_score"]),
            "assurance_status": latest["assurance_status"] if latest else "review",
            "audit_chain_valid": audit_valid,
            "proof_count": len(self.repository.list_proofs(organization_id=organization_id)),
            "receipt_count": len(self.repository.list_deployment_receipts(organization_id=organization_id)),
            "issued": issued,
            "certification_hash": latest["certification_hash"] if latest else None,
            "signature": latest["signature"] if latest else None,
            "public_key_id": latest["public_key_id"] if latest else DEFAULT_CERTIFICATION_KEY_ID,
        }
        return {
            **payload,
            "classification": latest["payload"].get("classification") if latest else "CONTROLLED_OPERATIONAL_STATE",
        }
