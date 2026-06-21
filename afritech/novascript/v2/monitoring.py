from __future__ import annotations

from hashlib import sha256
from typing import Any


class OpenTelemetryBridge:
    def emit_span(self, *, name: str, attributes: dict[str, Any]) -> dict[str, Any]:
        span_hash = sha256(f"{name}:{sorted(attributes.items())}".encode("utf-8")).hexdigest()
        return {
            "mode": "opentelemetry_bridge",
            "span_id": "span-" + span_hash[:16],
            "trace_id": "trace-" + span_hash[16:32],
            "name": name,
            "attributes": attributes,
            "exporter": "otlp_ready",
        }


class ContinuousAssuranceMonitor:
    def __init__(self) -> None:
        self._samples: dict[str, list[dict[str, Any]]] = {}

    def observe(
        self,
        *,
        organization_id: str,
        project_id: str,
        assurance: dict[str, Any],
        risk: dict[str, Any],
        trust: dict[str, Any],
    ) -> dict[str, Any]:
        sample = {
            "sample_id": "assure-" + sha256(
                f"{organization_id}:{project_id}:{assurance.get('assurance_status')}:{risk.get('risk_score')}:{trust.get('trust_score')}".encode()
            ).hexdigest()[:12],
            "organization_id": organization_id,
            "project_id": project_id,
            "assurance_status": assurance.get("assurance_status"),
            "trust_drift": assurance.get("trust_drift"),
            "risk_drift": assurance.get("risk_drift"),
            "policy_drift": assurance.get("policy_drift"),
            "architecture_drift": assurance.get("architecture_drift"),
            "risk_score": risk.get("risk_score"),
            "trust_score": trust.get("trust_score"),
        }
        self._samples.setdefault(organization_id, []).append(sample)
        return {"mode": "continuous_assurance_monitoring_service", "latest": sample, "sample_count": len(self._samples[organization_id])}

    def risk_dashboard(self, *, organization_id: str) -> dict[str, Any]:
        samples = self._samples.get(organization_id, [])
        risks = [int(sample.get("risk_score") or 0) for sample in samples]
        trust = [int(sample.get("trust_score") or 0) for sample in samples]
        return {
            "mode": "organization_risk_dashboard",
            "organization_id": organization_id,
            "sample_count": len(samples),
            "average_risk_score": round(sum(risks) / len(risks), 2) if risks else None,
            "average_trust_score": round(sum(trust) / len(trust), 2) if trust else None,
            "open_alerts": [
                sample
                for sample in samples[-10:]
                if sample.get("assurance_status") != "assured" or sample.get("risk_drift") in {"medium", "high"}
            ],
        }


class EvidenceRetentionGovernance:
    def policy(self, *, organization_id: str, project_id: str, classification: str = "governance_evidence") -> dict[str, Any]:
        retention_days = 2555 if classification == "governance_evidence" else 365
        policy_hash = sha256(f"{organization_id}:{project_id}:{classification}:{retention_days}".encode()).hexdigest()
        return {
            "mode": "evidence_retention_governance",
            "organization_id": organization_id,
            "project_id": project_id,
            "classification": classification,
            "retention_days": retention_days,
            "disposition": "retain_then_review",
            "policy_hash": policy_hash,
        }


class FormalAssuranceReporter:
    def __init__(self) -> None:
        self._reports: dict[str, dict[str, Any]] = {}

    def report(
        self,
        *,
        organization_id: str,
        project_id: str,
        assurance: dict[str, Any],
        certificate_chain: dict[str, Any],
        policy_decision: dict[str, Any],
    ) -> dict[str, Any]:
        report_hash = sha256(
            f"{organization_id}:{project_id}:{assurance.get('assurance_status')}:{certificate_chain.get('chain_hash')}:{policy_decision.get('decision_id')}".encode()
        ).hexdigest()
        record = {
            "mode": "formal_assurance_reporting",
            "report_id": "assurance-report-" + report_hash[:12],
            "organization_id": organization_id,
            "project_id": project_id,
            "assurance_status": assurance.get("assurance_status"),
            "certificate_chain_hash": certificate_chain.get("chain_hash"),
            "policy_decision_id": policy_decision.get("decision_id"),
            "report_hash": report_hash,
        }
        self._reports[record["report_id"]] = record
        return record

    def find(self, report_id: str) -> dict[str, Any] | None:
        return self._reports.get(report_id)


_DEFAULT_OTEL = OpenTelemetryBridge()
_DEFAULT_ASSURANCE_MONITOR = ContinuousAssuranceMonitor()
_DEFAULT_RETENTION = EvidenceRetentionGovernance()
_DEFAULT_REPORTER = FormalAssuranceReporter()


def get_opentelemetry_bridge() -> OpenTelemetryBridge:
    return _DEFAULT_OTEL


def get_continuous_assurance_monitor() -> ContinuousAssuranceMonitor:
    return _DEFAULT_ASSURANCE_MONITOR


def get_evidence_retention_governance() -> EvidenceRetentionGovernance:
    return _DEFAULT_RETENTION


def get_formal_assurance_reporter() -> FormalAssuranceReporter:
    return _DEFAULT_REPORTER
