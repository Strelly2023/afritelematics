from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean, stdev
from typing import Any

from afritech.afriprogramming.persistence import PlatformStore, get_platform_store


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


@dataclass(frozen=True)
class TrustInputs:
    organization_id: str
    policy_compliance_rate: float
    proof_coverage_rate: float
    audit_integrity_score: float
    deployment_success_rate: float
    verification_completeness: float
    incident_count: int
    failed_deployments: int
    audit_chain_breaks: int


@dataclass(frozen=True)
class TrustResult:
    organization_id: str
    trust_score: int
    classification: str
    breakdown: dict[str, float]
    findings: list[str]
    computed_at: str


class TrustEngine:
    WEIGHTS = {
        "policy": 0.25,
        "proof": 0.25,
        "audit": 0.20,
        "deployment": 0.15,
        "verification": 0.15,
    }

    def compute(self, inputs: TrustInputs) -> TrustResult:
        policy = self._clamp(inputs.policy_compliance_rate)
        proof = self._clamp(inputs.proof_coverage_rate)
        audit = self._clamp(inputs.audit_integrity_score)
        deployment = self._clamp(inputs.deployment_success_rate)
        verification = self._clamp(inputs.verification_completeness)

        weighted = (
            policy * self.WEIGHTS["policy"]
            + proof * self.WEIGHTS["proof"]
            + audit * self.WEIGHTS["audit"]
            + deployment * self.WEIGHTS["deployment"]
            + verification * self.WEIGHTS["verification"]
        )
        penalty = (
            inputs.incident_count * 2.0
            + inputs.failed_deployments * 1.5
            + inputs.audit_chain_breaks * 10.0
        )
        score = max(0.0, min(100.0, weighted - penalty))
        classification = self._classify(score)
        findings = self._findings(inputs, score)
        return TrustResult(
            organization_id=inputs.organization_id,
            trust_score=round(score),
            classification=classification,
            breakdown={
                "policy_compliance": policy,
                "proof_coverage": proof,
                "audit_integrity": audit,
                "deployment_success": deployment,
                "verification_completeness": verification,
                "penalty": penalty,
            },
            findings=findings,
            computed_at=_now(),
        )

    def _clamp(self, value: float) -> float:
        return max(0.0, min(100.0, float(value)))

    def _classify(self, score: float) -> str:
        if score >= 90:
            return "HIGH_TRUST"
        if score >= 75:
            return "MEDIUM_TRUST"
        if score >= 55:
            return "LOW_TRUST"
        return "CRITICAL"

    def _findings(self, inputs: TrustInputs, score: float) -> list[str]:
        findings: list[str] = []
        if inputs.policy_compliance_rate < 90:
            findings.append("policy compliance below target")
        if inputs.proof_coverage_rate < 90:
            findings.append("proof coverage below target")
        if inputs.audit_integrity_score < 100:
            findings.append("audit chain is not perfect")
        if inputs.failed_deployments > 0:
            findings.append(f"{inputs.failed_deployments} failed deployments detected")
        if inputs.incident_count > 0:
            findings.append(f"{inputs.incident_count} incidents recorded")
        if inputs.audit_chain_breaks > 0:
            findings.append("audit chain break detected")
        if score >= 90:
            findings.append("system operating at high trust")
        return findings


def build_trust_anomalies(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scores = [int(item["trust_score"]) for item in history if "trust_score" in item]
    if len(scores) < 4:
        return []
    average = mean(scores)
    deviation = stdev(scores) or 0.0
    anomalies: list[dict[str, Any]] = []
    for index, item in enumerate(history):
        score = int(item["trust_score"])
        previous = int(history[index - 1]["trust_score"]) if index else score
        if deviation and abs(score - average) > 2 * deviation:
            anomalies.append(
                {
                    "organization_id": item.get("organization_id"),
                    "computed_at": item.get("computed_at"),
                    "trust_score": score,
                    "reason": "deviation from trust baseline",
                }
            )
        if index and previous - score >= 20:
            anomalies.append(
                {
                    "organization_id": item.get("organization_id"),
                    "computed_at": item.get("computed_at"),
                    "trust_score": score,
                    "reason": "sharp trust drop",
                }
            )
    return anomalies


def verify_external_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    required = ("organization_id", "proof_hash", "audit_hash", "receipt_hash")
    missing = [field for field in required if not str(receipt.get(field, "")).strip()]
    if missing:
        return {"valid": False, "reason": f"missing fields: {', '.join(missing)}"}
    proof_hash = str(receipt["proof_hash"])
    audit_hash = str(receipt["audit_hash"])
    receipt_hash = str(receipt["receipt_hash"])
    if len(proof_hash) < 16 or len(audit_hash) < 16 or len(receipt_hash) < 16:
        return {"valid": False, "reason": "hash values too short"}
    return {
        "valid": True,
        "origin_organization": str(receipt["organization_id"]),
        "receipt_hash": receipt_hash,
    }


class TrustService:
    def __init__(self, repository: PlatformStore | None = None) -> None:
        self.repository = repository or get_platform_store()
        self.engine = TrustEngine()

    def compute_for_org(self, organization_id: str) -> dict[str, Any]:
        summary = self.repository.insights(organization_id=organization_id)
        audit_chain_valid = self.repository.verify_signed_audit_chain(organization_id=organization_id)
        if not audit_chain_valid:
            audit_chain_valid = self.repository.verify_audit_chain(organization_id=organization_id)
        deployment_requests = int(summary["deployment_requests"])
        deployments = int(summary["deployments"])
        proofs = int(summary["proofs"])
        receipts = int(summary["deployment_receipts"])
        approved = int(summary["approved_requests"])

        policy_rate = 100.0 if deployment_requests == 0 else min(100.0, 60.0 + (approved / deployment_requests) * 40.0)
        proof_rate = 90.0 if deployments == 0 else min(100.0, (proofs / max(1, deployments)) * 100.0)
        audit_rate = 100.0 if audit_chain_valid else 45.0
        deployment_rate = 90.0 if deployment_requests == 0 else min(100.0, (deployments / deployment_requests) * 100.0)
        verification_rate = 95.0 if deployments == 0 else min(100.0, ((proofs + receipts) / max(1, deployments)) * 100.0)
        incident_count = max(0, deployment_requests - approved)
        failed_deployments = max(0, deployments - approved)
        audit_chain_breaks = 0 if audit_chain_valid else 1

        result = self.engine.compute(
            TrustInputs(
                organization_id=organization_id,
                policy_compliance_rate=policy_rate,
                proof_coverage_rate=proof_rate,
                audit_integrity_score=audit_rate,
                deployment_success_rate=deployment_rate,
                verification_completeness=verification_rate,
                incident_count=incident_count,
                failed_deployments=failed_deployments,
                audit_chain_breaks=audit_chain_breaks,
            )
        )
        stored = self.repository.store_trust_score(
            organization_id=organization_id,
            trust_score=result.trust_score,
            classification=result.classification,
            breakdown=result.breakdown,
            findings=result.findings,
        )
        self.repository.track_usage(
            organization_id=organization_id,
            metric="trust.compute",
            amount=1,
            context={
                "trust_score": result.trust_score,
                "classification": result.classification,
            },
        )
        self.repository.publish_trust_stream_event(
            organization_id=organization_id,
            event_type="trust.updated",
            payload={
                "trust_score": result.trust_score,
                "classification": result.classification,
                "audit_chain_valid": audit_chain_valid,
            },
        )
        return {
            "organization_id": organization_id,
            "trust_score": result.trust_score,
            "classification": result.classification,
            "breakdown": result.breakdown,
            "findings": result.findings,
            "computed_at": result.computed_at,
            "audit_chain_valid": audit_chain_valid,
            "source": stored["score_id"],
        }

    def latest(self, organization_id: str) -> dict[str, Any] | None:
        return self.repository.latest_trust_score(organization_id=organization_id)

    def stream(self, organization_id: str, limit: int = 100) -> list[dict[str, Any]]:
        return self.repository.list_trust_stream_events(organization_id=organization_id, limit=limit)

    def anomalies(self, organization_id: str, limit: int = 25) -> list[dict[str, Any]]:
        history = self.repository.list_trust_scores(organization_id=organization_id, limit=limit)
        return build_trust_anomalies(list(reversed(history)))

    def trust_risk(self, organization_id: str) -> dict[str, Any]:
        latest = self.latest(organization_id)
        if latest is None:
            latest = self.compute_for_org(organization_id)
        return {
            "organization_id": organization_id,
            "trust_score": latest["trust_score"],
            "classification": latest["classification"],
            "risk_score": max(0, 100 - int(latest["trust_score"])),
        }
