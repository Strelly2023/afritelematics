from __future__ import annotations

from typing import Any

from afritech.afriprogramming.assurance.replay_registry import ReplayRegistry
from afritech.afriprogramming.assurance.risk_engine import RiskEngine
from afritech.afriprogramming.assurance.trust_engine import TrustService, verify_external_receipt
from afritech.afriprogramming.persistence import PlatformStore, get_platform_store


class AssuranceService:
    def __init__(self, repository: PlatformStore | None = None) -> None:
        self.repository = repository or get_platform_store()
        self.trust_service = TrustService(self.repository)
        self.risk_engine = RiskEngine()
        self.replay_registry = ReplayRegistry(self.repository)

    def compute_for_deployment(self, *, deployment_id: str, organization_id: str) -> dict[str, Any]:
        deployment = self.repository.get_deployment(
            deployment_id=deployment_id,
            organization_id=organization_id,
        )
        if deployment is None:
            raise KeyError(deployment_id)

        request = self.repository.get_deployment_request(
            request_id=deployment["request_id"],
            organization_id=organization_id,
        )
        if request is None:
            raise KeyError(deployment["request_id"])

        trust = self.trust_service.compute_for_org(organization_id)
        proof = self.repository.latest_proof(organization_id=organization_id)
        proof_hash = proof["proof_hash"] if proof else deployment["deployment_id"]
        audit_hash = self.repository.get_last_audit_hash(organization_id=organization_id) or ""
        receipt = self.repository.get_deployment_receipt(
            deployment_id=deployment_id,
            organization_id=organization_id,
        )
        if receipt is None:
            receipt = self.repository.store_deployment_receipt(
                organization_id=organization_id,
                deployment_id=deployment_id,
                request_id=request["request_id"],
                proof_hash=proof_hash,
                audit_hash=audit_hash,
            )

        risk = self.risk_engine.compute(
            trust_score=int(trust["trust_score"]),
            proof_coverage=100 if proof else 60,
            policy_compliance=100 if request["status"] == "approved" else 50,
            audit_integrity=100 if trust["audit_chain_valid"] else 45,
            receipts_present=receipt is not None,
        )
        assurance_status = "verified" if trust["trust_score"] >= 70 and request["status"] == "approved" and trust["audit_chain_valid"] else "review"
        payload = {
            "deployment": deployment,
            "request": request,
            "trust": trust,
            "risk": {
                "risk_score": risk.risk_score,
                "risk_level": risk.risk_level,
                "findings": list(risk.findings),
            },
            "receipt": receipt,
            "proof_hash": proof_hash,
            "audit_hash": audit_hash,
            "assurance_status": assurance_status,
        }
        assurance = self.repository.store_assurance_record(
            organization_id=organization_id,
            deployment_id=deployment_id,
            trust_score=int(trust["trust_score"]),
            risk_score=risk.risk_score,
            proof_coverage=100 if proof else 60,
            policy_compliance=100 if request["status"] == "approved" else 50,
            assurance_status=assurance_status,
            payload=payload,
        )
        self.repository.track_usage(
            organization_id=organization_id,
            metric="assurance.compute",
            amount=1,
            context={
                "deployment_id": deployment_id,
                "trust_score": trust["trust_score"],
                "assurance_status": assurance_status,
            },
        )
        replay = self.replay_registry.register(
            organization_id=organization_id,
            deployment_id=deployment_id,
            proof_id=proof["proof_id"] if proof else proof_hash,
            receipt_id=receipt["receipt_id"],
            audit_hash=audit_hash,
        )
        self.repository.publish_trust_stream_event(
            organization_id=organization_id,
            event_type="assurance.completed",
            payload={
                "deployment_id": deployment_id,
                "assurance_status": assurance_status,
                "trust_score": trust["trust_score"],
                "risk_score": risk.risk_score,
            },
        )
        return {
            "organization_id": organization_id,
            "deployment_id": deployment_id,
            "assurance": assurance,
            "trust": trust,
            "risk": payload["risk"],
            "receipt": receipt,
            "replay": replay,
            "proof_hash": proof_hash,
            "audit_hash": audit_hash,
            "assurance_status": assurance_status,
        }

    def certification(self, *, organization_id: str) -> dict[str, Any]:
        trust = self.trust_service.latest(organization_id)
        if trust is None:
            trust = self.trust_service.compute_for_org(organization_id)
        audit_valid = self.repository.verify_audit_chain(organization_id=organization_id)
        assurance_records = self.repository.list_assurance_records(organization_id=organization_id, limit=50)
        issued = bool(
            trust["trust_score"] >= 80
            and audit_valid
            and any(record["assurance_status"] == "verified" for record in assurance_records)
        )
        record = {
            "organization_id": organization_id,
            "certification": "CONTROLLED_OPERATIONAL_STATE",
            "issued": issued,
            "trust_score": trust["trust_score"],
            "audit_chain_valid": audit_valid,
            "assurance_records": len(assurance_records),
        }
        self.repository.publish_trust_stream_event(
            organization_id=organization_id,
            event_type="certification.checked",
            payload=record,
        )
        self.repository.track_usage(
            organization_id=organization_id,
            metric="certification.check",
            amount=1,
            context=record,
        )
        return record

    def verify_external(self, receipt: dict[str, Any]) -> dict[str, Any]:
        return verify_external_receipt(receipt)
