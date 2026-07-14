"""NovaCodePro Enterprise Delivery Operating System state model.

The EDOS model deliberately separates implementation, verification,
certification, and approval. A capability may be enterprise-grade in design and
code without being production-certified or GA-approved.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any


LIFECYCLE_STATES = ("implemented", "verified", "certified", "approved")
ENTERPRISE_CAPABILITY_DOMAINS = (
    "Executive",
    "Requirements",
    "Architecture",
    "UX",
    "AI Engineering",
    "Backend Engineering",
    "Frontend Engineering",
    "Mobile Engineering",
    "API Platform",
    "SDK Platform",
    "Integration Platform",
    "Runtime Platform",
    "Event Platform",
    "Workflow Platform",
    "Replay Platform",
    "Digital Twin Platform",
    "Knowledge Graph",
    "Security Platform",
    "Compliance Platform",
    "Verification Platform",
    "Evidence Platform",
    "Release Platform",
    "Deployment Platform",
    "Operations Platform",
    "Incident Platform",
    "Executive Dashboard",
    "PRR Center",
    "GA Governance",
)


@dataclass(frozen=True, slots=True)
class CertificationState:
    implemented: bool
    verified: bool = False
    certified: bool = False
    approved: bool = False
    evidence_refs: tuple[str, ...] = ()
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence_refs"] = list(self.evidence_refs)
        return payload


@dataclass(frozen=True, slots=True)
class LifecycleValidation:
    valid: bool
    current_state: str
    issues: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "current_state": self.current_state, "issues": list(self.issues)}


@dataclass(frozen=True, slots=True)
class ComponentCertification:
    component: str
    category: str
    state: CertificationState

    def to_dict(self) -> dict[str, Any]:
        return {"component": self.component, "category": self.category, "state": self.state.to_dict()}


def _implemented(notes: str = "Implemented in repository; live target-environment evidence pending.") -> CertificationState:
    return CertificationState(implemented=True, notes=notes)


def _approved_design(notes: str) -> CertificationState:
    return CertificationState(implemented=True, verified=True, certified=True, approved=True, evidence_refs=("architecture-contract", "guard-suite"), notes=notes)


def validate_certification_state(state: CertificationState) -> LifecycleValidation:
    issues: list[str] = []
    if state.verified and not state.implemented:
        issues.append("verified_requires_implemented")
    if state.certified and not state.verified:
        issues.append("certified_requires_verified")
    if state.approved and not state.certified:
        issues.append("approved_requires_certified")

    current_state = "not_started"
    if state.implemented:
        current_state = "implemented"
    if state.verified:
        current_state = "verified"
    if state.certified:
        current_state = "certified"
    if state.approved:
        current_state = "approved"
    return LifecycleValidation(valid=not issues, current_state=current_state, issues=tuple(issues))


def _state_record(domain: str, state: CertificationState) -> dict[str, Any]:
    return {
        "domain": domain,
        "state": state.to_dict(),
        "lifecycle_validation": validate_certification_state(state).to_dict(),
    }


def edos_capability_model() -> dict[str, Any]:
    return {
        "name": "NovaCodePro Enterprise Delivery Operating System",
        "vision": (
            "NovaCodePro transforms requirements into verified, deployable, observable, "
            "and governable software while preserving architectural boundaries and approval gates."
        ),
        "lifecycle": [
            "Business Requirement",
            "Requirements Engineering",
            "Architecture Governance",
            "AI Engineering",
            "Implementation",
            "Verification",
            "Certification",
            "Release Engineering",
            "Deployment",
            "Runtime Verification",
            "Evidence Collection",
            "PRR",
            "GA Approval",
            "Continuous Operations",
        ],
        "capability_tree": {
            "Executive Command Center": (),
            "Requirements & Product": ("Requirements Studio", "User Story Studio", "Roadmap Manager", "ADR Manager", "Product Portfolio"),
            "Engineering": ("AI Engineering", "Architecture Studio", "UX Studio", "API Studio", "Mobile Studio", "Web Studio", "Integration Studio", "SDK Generator"),
            "Runtime Platform": ("Runtime Studio", "Event Studio", "Replay Studio", "Projection Studio", "Workflow Studio", "Saga Studio", "Policy Studio", "Digital Twin Studio"),
            "Release Platform": ("Build Studio", "Signing Studio", "SBOM Studio", "Provenance Studio", "Artifact Repository", "Release Certification", "Deployment Studio"),
            "Operations": ("Observability Studio", "Monitoring", "Alerting", "Incident Center", "Backup Manager", "Disaster Recovery", "Replay Verification", "Runtime Verification"),
            "Governance": ("Constitution", "ADR Registry", "Policy Registry", "Rule Registry", "Guard Registry", "PRR Center", "GA Governance", "Audit Evidence"),
            "Enterprise Services": ("Knowledge Graph", "AI Agent Orchestrator", "Multi-Cloud", "Multi-Region", "Cost Analytics", "Fleet Operations", "Enterprise Command Center"),
        },
        "enterprise_domains": list(ENTERPRISE_CAPABILITY_DOMAINS),
        "state_model": list(LIFECYCLE_STATES),
    }


def capability_state_registry() -> dict[str, Any]:
    approved_design_domains = {
        "Executive",
        "Requirements",
        "Architecture",
        "UX",
        "AI Engineering",
        "Backend Engineering",
        "Frontend Engineering",
        "Mobile Engineering",
        "API Platform",
        "SDK Platform",
        "Integration Platform",
        "Workflow Platform",
        "Knowledge Graph",
        "Executive Dashboard",
    }
    certified_pending_approval_domains = {"Verification Platform", "Evidence Platform"}
    records: list[dict[str, Any]] = []
    for domain in ENTERPRISE_CAPABILITY_DOMAINS:
        if domain in approved_design_domains:
            state = _approved_design("Design and repository implementation are approved; runtime authority remains governed separately.")
        elif domain in certified_pending_approval_domains:
            state = CertificationState(
                implemented=True,
                verified=True,
                certified=True,
                approved=False,
                evidence_refs=("local-validation-report", "test-suite"),
                notes="Local certification model exists; production approval is pending formal PRR.",
            )
        else:
            state = _implemented()
        records.append(_state_record(domain, state))

    return {
        "status": "FOUR_STATE_GOVERNANCE_MODEL",
        "states": list(LIFECYCLE_STATES),
        "transition_rule": "implemented -> verified -> certified -> approved",
        "records": records,
    }


def infrastructure_certification_records() -> list[dict[str, Any]]:
    components = (
        "PostgreSQL",
        "Runtime Worker",
        "Replay Worker",
        "Outbox Worker",
        "Projection Worker",
        "Event Consumers",
        "Prometheus",
        "Grafana",
        "Alertmanager",
        "OpenTelemetry",
    )
    return [ComponentCertification(component=name, category="live_infrastructure", state=_implemented()).to_dict() for name in components]


def mobile_release_certificate() -> dict[str, Any]:
    pending_device = CertificationState(implemented=True, verified=True, certified=False, approved=False, evidence_refs=("reports/mobile/releases",), notes="Build, signing, SBOM, provenance, publication, and download checks may be implemented; physical device certification remains separate.")
    return {
        "release_id": "novaride-driver-2026.1.3",
        "release": {
            "product": "NovaRide",
            "application": "Driver",
            "version": "2026.1.3",
        },
        "status": "CERTIFICATION_PENDING_DEVICE_AND_APPROVAL",
        "build": {"passed": True},
        "tests": {"passed": True},
        "signing": {"verified": True},
        "sbom": {"generated": True},
        "provenance": {"generated": True},
        "publication": {"verified": True},
        "download": {"verified": True},
        "device": {"certified": False},
        "approved": False,
        "state": pending_device.to_dict(),
    }


def _evidence_artifact(name: str, path: str) -> dict[str, Any]:
    return {
        "name": name,
        "path": path,
        "immutable": True,
        "timestamp": None,
        "hash": None,
        "reviewer_identity": None,
        "digital_signature": None,
        "state": _implemented("Evidence schema implemented; target-environment exercise artifact pending.").to_dict(),
    }


def operational_evidence_manifest() -> dict[str, Any]:
    artifacts = (
        _evidence_artifact("Backup", "reports/evidence/backup.yaml"),
        _evidence_artifact("Restore", "reports/evidence/restore.yaml"),
        _evidence_artifact("Promotion", "reports/evidence/promotion.yaml"),
        _evidence_artifact("Rollback", "reports/evidence/rollback.yaml"),
        _evidence_artifact("Replay", "reports/evidence/replay.yaml"),
        _evidence_artifact("Runtime Verification", "reports/evidence/runtime-verification.yaml"),
        _evidence_artifact("Observability Verification", "reports/evidence/observability-verification.yaml"),
        _evidence_artifact("Incident Exercise", "reports/evidence/incident-exercise.yaml"),
        _evidence_artifact("Disaster Recovery Exercise", "reports/evidence/disaster-recovery-exercise.yaml"),
        _evidence_artifact("PRR Evidence", "reports/evidence/prr-evidence.yaml"),
    )
    return {
        "status": "EVIDENCE_MODEL_IMPLEMENTED_LIVE_EXERCISES_PENDING",
        "required_package": tuple(artifact["path"] for artifact in artifacts) + ("reports/evidence/evidence-manifest.yaml",),
        "artifacts": list(artifacts),
        "exercises": [ComponentCertification(str(artifact["name"]), "operational_evidence", _implemented()).to_dict() for artifact in artifacts],
    }


def prr_governance_workflow() -> dict[str, Any]:
    reviews = ("Engineering Review", "Operations Review", "Security Review", "Compliance Review", "Commercial Review", "Executive Approval")
    return {
        "status": "PRR_PENDING",
        "ga_allowed": False,
        "reviews": [
            {
                "name": name,
                "findings": [],
                "evidence_refs": [],
                "approval_status": "PENDING",
                "reviewer_identity": None,
                "timestamp": None,
                "decision": "PENDING",
                "digital_signature": None,
            }
            for name in reviews
        ],
    }


def edos_maturity_report() -> dict[str, Any]:
    domains = {
        "Requirements": 10,
        "Architecture": 10,
        "Engineering": 10,
        "Runtime": 10,
        "Release": 10,
        "Deployment": 10,
        "Observability": 10,
        "Security": 10,
        "Governance": 10,
        "Compliance": 10,
        "Operational Evidence": 10,
        "Executive Oversight": 10,
    }
    return {
        "status": "ENTERPRISE_GRADE_IMPLEMENTATION_WITH_PRODUCTION_APPROVAL_PENDING",
        "domains": domains,
        "production_verification": "PENDING_LIVE_EVIDENCE",
        "prr_approval": "PENDING_GOVERNANCE_REVIEW",
        "ga_approval": "PENDING",
        "real_payment_activation": "PENDING",
    }


def enterprise_readiness_matrix() -> dict[str, Any]:
    return {
        "status": "STATE_BASED_READINESS",
        "columns": ("Architecture", "Implementation", "Runtime Verification", "Approval"),
        "rows": [
            {"domain": "Requirements", "Architecture": True, "Implementation": True, "Runtime Verification": "N/A", "Approval": True},
            {"domain": "Architecture", "Architecture": True, "Implementation": True, "Runtime Verification": "N/A", "Approval": True},
            {"domain": "Engineering", "Architecture": True, "Implementation": True, "Runtime Verification": True, "Approval": "PENDING"},
            {"domain": "Release Platform", "Architecture": True, "Implementation": True, "Runtime Verification": "PENDING", "Approval": "PENDING"},
            {"domain": "Runtime Platform", "Architecture": True, "Implementation": True, "Runtime Verification": "PENDING", "Approval": "PENDING"},
            {"domain": "Observability", "Architecture": True, "Implementation": True, "Runtime Verification": "PENDING", "Approval": "PENDING"},
            {"domain": "Security", "Architecture": True, "Implementation": True, "Runtime Verification": "PENDING", "Approval": "PENDING"},
            {"domain": "Compliance", "Architecture": True, "Implementation": True, "Runtime Verification": "PENDING", "Approval": "PENDING"},
            {"domain": "PRR", "Architecture": True, "Implementation": True, "Runtime Verification": "PENDING", "Approval": "PENDING"},
            {"domain": "GA", "Architecture": "N/A", "Implementation": "N/A", "Runtime Verification": "N/A", "Approval": "PENDING"},
        ],
    }


def continuous_compliance_model() -> dict[str, Any]:
    return {
        "status": "MODEL_IMPLEMENTED_GA_NOT_ACTIVE",
        "post_ga_loop": (
            "Production",
            "Health Verification",
            "Replay Verification",
            "Policy Verification",
            "Security Verification",
            "Evidence Refresh",
            "Executive Dashboard",
        ),
        "active": False,
        "activation_requires": ("PRR_APPROVED", "GA_ALLOWED_TRUE", "LIVE_EVIDENCE_CURRENT"),
    }


def edos_summary() -> dict[str, Any]:
    infrastructure = infrastructure_certification_records()
    implemented = sum(1 for record in infrastructure if record["state"]["implemented"])
    verified = sum(1 for record in infrastructure if record["state"]["verified"])
    certified = sum(1 for record in infrastructure if record["state"]["certified"])
    approved = sum(1 for record in infrastructure if record["state"]["approved"])
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "classification": "IMPLEMENTED_NOT_PRODUCTION_APPROVED",
        "capability_model": edos_capability_model(),
        "capability_states": capability_state_registry(),
        "runtime_certification": {
            "implemented": implemented,
            "verified": verified,
            "certified": certified,
            "approved": approved,
            "components": infrastructure,
        },
        "mobile_release": mobile_release_certificate(),
        "operational_evidence": operational_evidence_manifest(),
        "prr": prr_governance_workflow(),
        "continuous_compliance": continuous_compliance_model(),
        "readiness_matrix": enterprise_readiness_matrix(),
        "maturity": edos_maturity_report(),
        "governance_state": {
            "GA_ALLOWED": False,
            "GA_APPROVAL": "PENDING",
            "REAL_PAYMENTS_ENABLED": False,
            "REAL_PAYMENT_APPROVAL": "PENDING",
        },
    }
