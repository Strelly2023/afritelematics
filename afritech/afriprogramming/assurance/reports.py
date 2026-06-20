from __future__ import annotations

from typing import Any

from afritech.afriprogramming.assurance.continuous_engine import ContinuousAssuranceService
from afritech.afriprogramming.assurance.trust_engine import TrustService
from afritech.afriprogramming.persistence import PlatformStore, get_platform_store


class AssuranceReportService:
    def __init__(self, repository: PlatformStore | None = None) -> None:
        self.repository = repository or get_platform_store()
        self.trust_service = TrustService(self.repository)
        self.assurance_service = ContinuousAssuranceService(self.repository)

    def build(self, *, organization_id: str, report_classification: str) -> dict[str, Any]:
        trust = self.trust_service.latest(organization_id)
        if trust is None:
            trust = self.trust_service.compute_for_org(organization_id)
        assurance_status = self.assurance_service.status(organization_id=organization_id)
        proof_count = len(self.repository.list_proofs(organization_id=organization_id))
        receipt_count = len(self.repository.list_deployment_receipts(organization_id=organization_id))
        policies = self.repository.list_policy_definitions(organization_id=organization_id)
        decisions = self.repository.list_policy_decisions(organization_id=organization_id)
        certification = self.repository.latest_certification_record(organization_id=organization_id)
        payload = {
            "organization_summary": {
                "organization_id": organization_id,
                "trust_score": trust["trust_score"],
                "assurance_status": assurance_status["assurance_status"],
                "audit_chain_valid": self.repository.verify_audit_chain(organization_id=organization_id),
            },
            "trust_score": trust["trust_score"],
            "assurance_status": assurance_status["assurance_status"],
            "audit_chain_valid": self.repository.verify_audit_chain(organization_id=organization_id),
            "proof_coverage": proof_count,
            "deployment_receipt_coverage": receipt_count,
            "policy_compliance": len([decision for decision in decisions if decision["allowed"]]),
            "risk_findings": list(trust["findings"]),
            "certification_status": certification["certification_type"] if certification else None,
            "evidence_references": {
                "proofs": proof_count,
                "receipts": receipt_count,
                "policies": len(policies),
                "decisions": len(decisions),
            },
        }
        report = self.repository.store_assurance_report(
            organization_id=organization_id,
            report_classification=report_classification,
            payload=payload,
        )
        return {
            "report_classification": report_classification,
            **report,
            "payload": payload,
        }

    def latest(self, organization_id: str) -> dict[str, Any] | None:
        reports = self.repository.list_assurance_reports(organization_id=organization_id, limit=1)
        return reports[0] if reports else None
