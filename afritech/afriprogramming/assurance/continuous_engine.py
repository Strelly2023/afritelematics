from __future__ import annotations

from typing import Any

from afritech.afriprogramming.assurance.policy_registry import PolicyRegistryService
from afritech.afriprogramming.assurance.risk_engine import RiskEngine
from afritech.afriprogramming.assurance.trust_engine import TrustService
from afritech.afriprogramming.persistence import PlatformStore, get_platform_store


class ContinuousAssuranceService:
    def __init__(self, repository: PlatformStore | None = None) -> None:
        self.repository = repository or get_platform_store()
        self.trust_service = TrustService(self.repository)
        self.policy_registry = PolicyRegistryService(self.repository)
        self.risk_engine = RiskEngine()

    def run(self, *, organization_id: str, actor_user_id: str = "system") -> dict[str, Any]:
        self.policy_registry.seed_defaults(organization_id=organization_id, created_by=actor_user_id)
        previous = self.repository.latest_assurance_run(organization_id=organization_id)
        previous_trust = int(previous["trust_score"]) if previous else 0
        trust = self.trust_service.compute_for_org(organization_id)
        proof = self.repository.latest_proof(organization_id=organization_id)
        receipts = self.repository.list_deployment_receipts(organization_id=organization_id, limit=500)
        risk = self.risk_engine.compute(
            trust_score=int(trust["trust_score"]),
            proof_coverage=100 if proof else 60,
            policy_compliance=100 if trust["audit_chain_valid"] else 70,
            audit_integrity=100 if trust["audit_chain_valid"] else 40,
            receipts_present=bool(receipts),
        )
        drift = int(trust["trust_score"]) - previous_trust
        assurance_status = "verified" if int(trust["trust_score"]) >= 80 and trust["audit_chain_valid"] else "review"
        alert_level = "critical" if drift <= -20 or risk.risk_score >= 75 else "watch" if drift < 0 or risk.risk_score >= 40 else "green"
        run = self.repository.store_assurance_run(
            organization_id=organization_id,
            trust_score=int(trust["trust_score"]),
            previous_trust_score=previous_trust,
            drift=drift,
            risk_score=risk.risk_score,
            assurance_status=assurance_status,
            alert_level=alert_level,
            findings=list(trust["findings"]) + list(risk.findings),
            payload={
                "trust": trust,
                "proof_present": bool(proof),
                "receipt_count": len(receipts),
                "risk": {
                    "risk_score": risk.risk_score,
                    "risk_level": risk.risk_level,
                },
            },
        )
        if drift != 0:
            self.repository.store_assurance_drift_event(
                organization_id=organization_id,
                assurance_run_id=run["assurance_run_id"],
                previous_trust_score=previous_trust,
                current_trust_score=int(trust["trust_score"]),
                drift=drift,
                severity="high" if drift <= -20 else "medium" if drift < 0 else "low",
            )
        if alert_level != "green":
            self.repository.store_assurance_alert(
                organization_id=organization_id,
                assurance_run_id=run["assurance_run_id"],
                alert_level=alert_level,
                message=f"trust drift {drift} with risk {risk.risk_score}",
            )
        self.repository.publish_trust_stream_event(
            organization_id=organization_id,
            event_type="assurance.run",
            payload=run,
        )
        return run

    def status(self, *, organization_id: str) -> dict[str, Any]:
        latest = self.repository.latest_assurance_run(organization_id=organization_id)
        if latest is None:
            latest = self.run(organization_id=organization_id)
        return {
            "organization_id": organization_id,
            "assurance_status": latest["assurance_status"],
            "trust_score": latest["trust_score"],
            "drift": latest["drift"],
            "risk_score": latest["risk_score"],
            "alert_level": latest["alert_level"],
            "computed_at": latest["created_at"],
        }

    def history(self, *, organization_id: str, limit: int = 100) -> list[dict[str, Any]]:
        return self.repository.list_assurance_runs(organization_id=organization_id, limit=limit)

    def alerts(self, *, organization_id: str, limit: int = 100) -> list[dict[str, Any]]:
        return self.repository.list_assurance_alerts(organization_id=organization_id, limit=limit)
