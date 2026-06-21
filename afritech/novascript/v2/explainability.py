from __future__ import annotations

from hashlib import sha256
from typing import Any


class DecisionExplainabilityEngine:
    def explain(
        self,
        *,
        decision: str,
        policy_decision: dict[str, Any],
        trust: dict[str, Any],
        certificate_chain: dict[str, Any],
        assurance: dict[str, Any],
    ) -> dict[str, Any]:
        trust_score = int(trust.get("trust_score", 0))
        allowed = bool(policy_decision.get("allowed"))
        certificate_valid = bool(certificate_chain.get("chain_hash"))
        assured = assurance.get("assurance_status") == "assured"
        reasoning = []
        reasoning.append("policy satisfied" if allowed else "policy requires review")
        reasoning.append("certificate chain present" if certificate_valid else "certificate chain missing")
        reasoning.append("assurance healthy" if assured else "assurance requires review")
        if trust_score >= 80:
            reasoning.append("trust score meets target")
        elif trust_score >= 60:
            reasoning.append("trust score within review band")
        else:
            reasoning.append("trust score below target")
        explanation_hash = sha256(
            f"{decision}:{policy_decision.get('policy_id')}:{policy_decision.get('policy_version')}:{trust_score}:{certificate_chain.get('chain_hash')}:{assurance.get('assurance_status')}".encode()
        ).hexdigest()
        return {
            "mode": "decision_explainability",
            "explanation_id": "explain-" + explanation_hash[:12],
            "decision": decision,
            "policy": policy_decision.get("policy_id"),
            "policy_version": policy_decision.get("policy_version"),
            "trust_score": trust_score,
            "reasoning": reasoning,
            "outcome": "allowed" if allowed and certificate_valid and assured else "review",
            "explanation_hash": explanation_hash,
        }


class AssuranceDriftEngine:
    def detect(
        self,
        *,
        assurance: dict[str, Any],
        compliance: dict[str, Any],
        architecture: dict[str, Any],
        evidence: dict[str, Any],
    ) -> dict[str, Any]:
        drifts = {
            "trust_drift": assurance.get("trust_drift", "low"),
            "policy_drift": assurance.get("policy_drift", "none"),
            "compliance_drift": "none" if compliance.get("compliant") else "compliance_review",
            "architecture_drift": assurance.get("architecture_drift", architecture.get("change_pressure", "baseline")),
            "evidence_drift": "low" if int(evidence.get("verified_count", 0)) >= 1 else "medium",
        }
        severity = _severity(drifts)
        drift_hash = sha256(str(sorted(drifts.items())).encode("utf-8")).hexdigest()
        return {
            "mode": "assurance_drift_detection",
            "drift_id": "drift-" + drift_hash[:12],
            "drift_detected": severity != "low",
            "severity": severity,
            "dimensions": drifts,
            "drift_hash": drift_hash,
        }


class PortableVerificationPackager:
    def package(
        self,
        *,
        receipt: dict[str, Any],
        certificate_chain: dict[str, Any],
        assurance_report: dict[str, Any],
        proof: dict[str, Any],
        explanation: dict[str, Any],
    ) -> dict[str, Any]:
        files = {
            "receipt.json": sha256(str(sorted(receipt.items())).encode("utf-8")).hexdigest(),
            "certificate.json": certificate_chain.get("chain_hash"),
            "assurance.json": assurance_report.get("report_hash"),
            "proof.json": sha256(str(sorted(proof.items())).encode("utf-8")).hexdigest(),
            "explanation.json": explanation.get("explanation_hash"),
        }
        manifest_hash = sha256(str(sorted(files.items())).encode("utf-8")).hexdigest()
        return {
            "mode": "portable_verification_package",
            "package_id": "verifypkg-" + manifest_hash[:12],
            "receipt_id": receipt.get("receipt_id"),
            "files": files,
            "verification_manifest": {
                "manifest_id": "manifest-" + manifest_hash[:12],
                "manifest_hash": manifest_hash,
                "offline_verification": True,
                "requires_novascript_runtime": False,
            },
        }


class ArchitectureObservatory:
    def observe(
        self,
        *,
        project_id: str,
        ledger: dict[str, Any],
        trust: dict[str, Any],
        risk: dict[str, Any],
    ) -> dict[str, Any]:
        timeline = list(ledger.get("timeline", []))
        current = timeline[-1] if timeline else ledger.get("latest", {})
        previous = timeline[-2] if len(timeline) > 1 else None
        observatory_hash = sha256(
            f"{project_id}:{current.get('ledger_id')}:{previous.get('ledger_id') if previous else 'baseline'}:{trust.get('trust_score')}:{risk.get('risk_score')}".encode()
        ).hexdigest()
        return {
            "mode": "architecture_evolution_observatory",
            "observatory_id": "archobs-" + observatory_hash[:12],
            "project_id": project_id,
            "current_architecture": current,
            "previous_architecture": previous,
            "change_timeline": timeline,
            "trust_impact": {
                "trust_score": trust.get("trust_score"),
                "status": trust.get("status"),
            },
            "risk_impact": {
                "risk_score": risk.get("risk_score"),
                "risk_level": risk.get("risk_level"),
            },
            "observatory_hash": observatory_hash,
        }


def _severity(drifts: dict[str, Any]) -> str:
    values = set(str(value) for value in drifts.values())
    if values & {"high", "policy_violation", "compliance_review"}:
        return "high"
    if values & {"medium", "evolving"}:
        return "medium"
    return "low"


_DEFAULT_EXPLAINABILITY = DecisionExplainabilityEngine()
_DEFAULT_DRIFT = AssuranceDriftEngine()
_DEFAULT_PACKAGER = PortableVerificationPackager()
_DEFAULT_OBSERVATORY = ArchitectureObservatory()


def get_decision_explainability_engine() -> DecisionExplainabilityEngine:
    return _DEFAULT_EXPLAINABILITY


def get_assurance_drift_engine() -> AssuranceDriftEngine:
    return _DEFAULT_DRIFT


def get_portable_verification_packager() -> PortableVerificationPackager:
    return _DEFAULT_PACKAGER


def get_architecture_observatory() -> ArchitectureObservatory:
    return _DEFAULT_OBSERVATORY
