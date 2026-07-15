"""NovaCodePro enterprise completion standard.

Completion is intentionally multi-dimensional. Repository implementation,
operational verification, and governance approval are separate states and must
not be collapsed into a single "done" flag.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import hashlib
import json
from typing import Any


COMPLETION_LEVELS = (
    "Repository Complete",
    "Operationally Verified",
    "Governance Approved",
    "Production Ready",
    "General Availability",
)

REPOSITORY_DELIVERABLES = (
    "Architecture",
    "Domain Models",
    "Services",
    "Persistent Stores",
    "REST APIs",
    "SDKs",
    "Portal UI",
    "CLI",
    "Automation",
    "Documentation",
    "Evidence Models",
    "Governance Models",
    "Tests",
    "CI Validation",
)

REPOSITORY_VALIDATIONS = (
    "Static Analysis",
    "Type Checking",
    "Unit Tests",
    "Integration Tests",
    "Contract Tests",
    "Governance Tests",
    "Security Scans",
    "Build Verification",
)

OPERATIONAL_VERIFICATIONS = (
    "Design synchronization",
    "Visual regression",
    "Accessibility automation",
    "Telemetry collection",
    "Experiment execution",
    "Knowledge graph synchronization",
    "Digital twin simulation",
    "Container deployment",
    "Monitoring",
    "Alerting",
    "Tracing",
    "Runtime Performance",
)

GOVERNANCE_APPROVALS = (
    "UX Lead",
    "Engineering Lead",
    "Security",
    "Operations",
    "Compliance",
    "Product",
    "Executive",
)

PRODUCTION_READY_GATES = (
    "Evidence Complete",
    "Monitoring Healthy",
    "Alerts Verified",
    "Backups Verified",
    "Recovery Tested",
    "Observability Verified",
    "Performance Verified",
    "Security Verified",
    "Compliance Verified",
)

COMPLETION_DOMAINS = (
    "UXOS Services",
    "APIs",
    "Portal",
    "Design Integration",
    "Visual Regression",
    "Accessibility",
    "Analytics",
    "Experimentation",
    "Knowledge Graph",
    "Digital UX Twin",
    "PRR",
    "GA Promotion",
)


@dataclass(frozen=True, slots=True)
class CompletionEvidence:
    id: str
    capability: str
    environment: str
    execution_time: str
    executor: str
    status: str
    artifacts: tuple[str, ...] = ()
    metrics: dict[str, Any] | None = None
    logs: tuple[str, ...] = ()
    screenshots: tuple[str, ...] = ()
    trace_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        body = asdict(self)
        body["artifacts"] = list(self.artifacts)
        body["logs"] = list(self.logs)
        body["screenshots"] = list(self.screenshots)
        body["trace_ids"] = list(self.trace_ids)
        body["metrics"] = dict(self.metrics or {})
        body["digital_signature"] = sign_record(body)
        return body


def _timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sign_record(payload: dict[str, Any]) -> str:
    material = {key: value for key, value in payload.items() if key != "digital_signature"}
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def completion_standard_model() -> dict[str, Any]:
    return {
        "name": "NovaCodePro Enterprise Completion Standard",
        "status": "STANDARD_IMPLEMENTED",
        "levels": list(COMPLETION_LEVELS),
        "level_1_repository_complete": {
            "deliverables": list(REPOSITORY_DELIVERABLES),
            "validation": list(REPOSITORY_VALIDATIONS),
            "status_shape": {
                "repository_complete": True,
                "operational_verified": False,
                "governance_approved": False,
            },
        },
        "level_2_operationally_verified": {
            "requires_live_execution": True,
            "verifications": list(OPERATIONAL_VERIFICATIONS),
            "evidence": ["Logs", "Metrics", "Traces", "Screenshots", "Reports", "Checksums", "Signed Records", "Deployment Results"],
        },
        "level_3_governance_approved": {
            "required_approvals": list(GOVERNANCE_APPROVALS),
            "approval_record": {
                "reviewer": "required",
                "role": "required",
                "decision": "APPROVED|REJECTED",
                "timestamp": "required",
                "comments": "required",
                "digital_signature": "required",
            },
        },
        "level_4_production_ready": {
            "gates": list(PRODUCTION_READY_GATES),
            "production_ready": False,
            "ga_allowed": False,
        },
        "level_5_general_availability": {
            "requires": ["PRR Approved", "Executive Authorization", "GA Promotion"],
            "ga_allowed": False,
        },
        "continuous_operational_validation": ["Deployment", "Verification", "Evidence", "Monitoring", "Drift Detection", "Revalidation", "Updated Evidence"],
        "invariants": {
            "ga_allowed": False,
            "real_payments_enabled": False,
            "rule": "Both remain false until repository implementation, operational verification, and governance approvals are complete.",
        },
    }


def completion_dashboard() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for domain in COMPLETION_DOMAINS:
        rows.append(
            {
                "domain": domain,
                "repository": domain != "GA Promotion",
                "operational": False,
                "governance": "PENDING",
            }
        )
    return {
        "status": "DIMENSIONAL_COMPLETION_DASHBOARD",
        "columns": ["Repository", "Operational", "Governance"],
        "rows": rows,
        "ga_allowed": False,
        "real_payments_enabled": False,
    }


def evaluate_completion_state(
    repository_complete: bool,
    operational_verified: bool,
    governance_approved: bool,
    production_ready_gates: dict[str, bool] | None = None,
    executive_authorized: bool = False,
) -> dict[str, Any]:
    gates = production_ready_gates or {}
    production_ready = bool(
        repository_complete
        and operational_verified
        and governance_approved
        and all(gates.get(gate, False) for gate in PRODUCTION_READY_GATES)
    )
    ga_allowed = bool(production_ready and executive_authorized)
    if ga_allowed:
        level = "General Availability"
    elif production_ready:
        level = "Production Ready"
    elif governance_approved:
        level = "Governance Approved"
    elif operational_verified:
        level = "Operationally Verified"
    elif repository_complete:
        level = "Repository Complete"
    else:
        level = "Incomplete"
    body = {
        "level": level,
        "repository_complete": repository_complete,
        "operational_verified": operational_verified,
        "governance_approved": governance_approved,
        "production_ready": production_ready,
        "ga_allowed": ga_allowed,
        "real_payments_enabled": False,
        "missing_production_gates": [gate for gate in PRODUCTION_READY_GATES if not gates.get(gate, False)],
        "evaluated_at": _timestamp(),
    }
    body["digital_signature"] = sign_record(body)
    return body


def build_completion_evidence(payload: dict[str, Any], evidence_id: str | None = None) -> dict[str, Any]:
    evidence = CompletionEvidence(
        id=evidence_id or str(payload.get("id") or "completion-evidence"),
        capability=str(payload.get("capability") or "NovaCodePro capability"),
        environment=str(payload.get("environment") or "development"),
        execution_time=str(payload.get("execution_time") or _timestamp()),
        executor=str(payload.get("executor") or "NovaCodePro"),
        status=str(payload.get("status") or "EVIDENCE_PENDING"),
        artifacts=tuple(payload.get("artifacts") or ()),
        metrics=dict(payload.get("metrics") or {}),
        logs=tuple(payload.get("logs") or ()),
        screenshots=tuple(payload.get("screenshots") or ()),
        trace_ids=tuple(payload.get("trace_ids") or ()),
    )
    return evidence.to_dict()

