from __future__ import annotations

from statistics import mean
from typing import Any

from afritech.afriprogramming.persistence import PlatformStore, get_platform_store


class RiskPredictionService:
    """Heuristic AI-style risk prediction over trust, identity, and fabric signals."""

    def __init__(self, repository: PlatformStore | None = None) -> None:
        self.repository = repository or get_platform_store()

    def predict(
        self,
        *,
        organization_id: str,
        entity_type: str = "organization",
        entity_id: str | None = None,
        horizon_days: int = 30,
    ) -> dict[str, Any]:
        insights = self.repository.insights(organization_id=organization_id)
        trust_scores = self.repository.list_trust_scores(organization_id=organization_id, limit=30)
        trust_values = [int(row["trust_score"]) for row in trust_scores]
        trust_avg = round(mean(trust_values), 2) if trust_values else 0.0
        identity_bindings = self.repository.list_identity_bindings(organization_id=organization_id, limit=50)
        regions = self.repository.list_trust_regions(organization_id=organization_id, limit=50)
        links = self.repository.list_trust_region_links(organization_id=organization_id, limit=50)
        negotiations = self.repository.list_negotiation_sessions(organization_id=organization_id, limit=50)
        stream_backends = self.repository.list_stream_backends(organization_id=organization_id, limit=20)
        certificate_valid = self.repository.verify_certificate_chain(organization_id=organization_id)

        features = {
            "trust_score": insights["trust_score"] or 0,
            "trust_average": trust_avg,
            "audit_chain_valid": insights["audit_chain_valid"],
            "signed_audit_chain_valid": insights["signed_audit_chain_valid"],
            "identity_bindings": len(identity_bindings),
            "regions": len(regions),
            "region_links": len(links),
            "negotiations": len(negotiations),
            "stream_backends": len(stream_backends),
            "certificate_valid": certificate_valid,
            "usage_total": insights["usage_total"],
        }
        risk_score = 100
        risk_score -= min(40, int(features["trust_score"] or 0) // 2)
        risk_score -= min(15, int(features["trust_average"] or 0) // 10)
        risk_score -= 10 if features["audit_chain_valid"] else 0
        risk_score -= 10 if features["signed_audit_chain_valid"] else 0
        risk_score -= min(10, features["identity_bindings"] * 2)
        risk_score -= min(8, features["regions"] * 2)
        risk_score -= min(8, features["stream_backends"] * 2)
        risk_score -= 8 if certificate_valid else 0
        risk_score += min(20, len([n for n in negotiations if n["state"] not in {"accepted", "completed"}]) * 3)
        risk_score = max(0, min(100, risk_score))

        confidence = round(min(0.98, 0.55 + len(trust_values) / 120), 2)
        if risk_score >= 75:
            risk_level = "critical"
        elif risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 25:
            risk_level = "moderate"
        else:
            risk_level = "low"

        explanation = []
        if not features["audit_chain_valid"]:
            explanation.append("audit chain is invalid")
        if not features["signed_audit_chain_valid"]:
            explanation.append("signed audit chain is invalid")
        if not certificate_valid:
            explanation.append("certificate chain is invalid")
        if len(identity_bindings) == 0:
            explanation.append("no identity bindings")
        if len(negotiations) > 0:
            explanation.append("open trust negotiations present")
        if not explanation:
            explanation.append("trust posture stable")

        prediction = self.repository.store_risk_prediction(
            organization_id=organization_id,
            entity_type=entity_type,
            entity_id=entity_id or organization_id,
            horizon_days=horizon_days,
            risk_score=risk_score,
            confidence=confidence,
            features=features,
            explanation=explanation,
        )
        return {
            "prediction": prediction,
            "organization_id": organization_id,
            "entity_type": entity_type,
            "entity_id": entity_id or organization_id,
            "horizon_days": horizon_days,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "confidence": confidence,
            "features": features,
            "explanation": explanation,
        }

    def latest(self, organization_id: str | None = None, entity_type: str | None = None) -> dict[str, Any] | None:
        return self.repository.latest_risk_prediction(organization_id=organization_id, entity_type=entity_type)

    def history(self, organization_id: str | None = None, entity_type: str | None = None) -> list[dict[str, Any]]:
        return self.repository.list_risk_predictions(organization_id=organization_id, entity_type=entity_type)


__all__ = ["RiskPredictionService"]
