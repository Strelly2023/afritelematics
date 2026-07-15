from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from typing import Any


PROFILES = {"local", "integration", "uat", "production"}


@dataclass(frozen=True)
class ProductionDependency:
    name: str
    env_var: str
    required_profiles: tuple[str, ...]
    description: str


DEPENDENCIES = (
    ProductionDependency("PostgreSQL control plane", "NOVACODEPRO_DATABASE_URL", ("integration", "uat", "production"), "Authoritative RLS-backed control-plane persistence."),
    ProductionDependency("Temporal namespace", "NOVACODEPRO_TEMPORAL_TARGET", ("integration", "uat", "production"), "Durable workflow runtime with replay and signals."),
    ProductionDependency("Kafka or Redpanda brokers", "NOVACODEPRO_EVENT_BROKERS", ("integration", "uat", "production"), "Broker-backed event fabric."),
    ProductionDependency("Schema registry", "NOVACODEPRO_SCHEMA_REGISTRY_URL", ("integration", "uat", "production"), "Event compatibility enforcement."),
    ProductionDependency("KMS signing key", "NOVACODEPRO_EVIDENCE_KMS_KEY_ID", ("uat", "production"), "Asymmetric evidence signing key."),
    ProductionDependency("Immutable evidence bucket", "NOVACODEPRO_EVIDENCE_BUCKET", ("uat", "production"), "S3 Object Lock evidence store."),
    ProductionDependency("Neo4j projection", "NOVACODEPRO_NEO4J_URI", ("integration", "uat", "production"), "Typed graph traversal projection."),
    ProductionDependency("OpenTelemetry endpoint", "OTEL_EXPORTER_OTLP_ENDPOINT", ("integration", "uat", "production"), "Distributed tracing and metric export."),
    ProductionDependency("Global routing zone", "NOVACODEPRO_ROUTE53_ZONE_ID", ("production",), "Production global routing control."),
    ProductionDependency("Global accelerator", "NOVACODEPRO_GLOBAL_ACCELERATOR_ARN", ("production",), "Production multi-region traffic steering."),
    ProductionDependency("Audit verifier role", "NOVACODEPRO_AUDIT_VERIFIER_ROLE_ARN", ("production",), "Independent audit-account verification access."),
)


def runtime_profile(environment: str | None = None) -> str:
    value = str(environment or os.environ.get("NOVACODEPRO_PROFILE") or os.environ.get("NOVACODEPRO_ENVIRONMENT") or "local").strip().lower()
    if value == "prod":
        return "production"
    if value not in PROFILES:
        return "local"
    return value


def validate_production_dependencies(environment: str | None = None, environ: dict[str, str] | None = None) -> dict[str, Any]:
    profile = runtime_profile(environment)
    env = environ or os.environ
    checks: list[dict[str, Any]] = []
    missing: list[str] = []
    for dependency in DEPENDENCIES:
        required = profile in dependency.required_profiles
        value = str(env.get(dependency.env_var) or "")
        configured = bool(value)
        status = "PASS" if configured or not required else "BLOCKED"
        if required and not configured:
            missing.append(dependency.env_var)
        checks.append(
            {
                "name": dependency.name,
                "env_var": dependency.env_var,
                "required": required,
                "configured": configured,
                "status": status,
                "description": dependency.description,
            }
        )
    return {
        "profile": profile,
        "status": "READY" if not missing else "BLOCKED",
        "missing": missing,
        "checks": checks,
    }


def require_production_dependencies(environment: str | None = None, environ: dict[str, str] | None = None) -> dict[str, Any]:
    report = validate_production_dependencies(environment, environ)
    if report["status"] != "READY":
        raise RuntimeError(f"production_dependencies_missing:{','.join(report['missing'])}")
    return report


REQUIRED_PROMETHEUS_TARGETS = (
    "afritech-api",
    "nginx",
    "prometheus",
    "grafana",
    "node-exporter",
    "postgres-exporter",
    "cadvisor",
    "otel-collector",
    "alertmanager",
)

GRAFANA_DASHBOARDS = (
    ("Platform", "reports/prr/grafana/Platform.png"),
    ("API", "reports/prr/grafana/API.png"),
    ("NovaRide", "reports/prr/grafana/NovaRide.png"),
    ("NovaPay", "reports/prr/grafana/NovaPay.png"),
    ("NovaID", "reports/prr/grafana/NovaID.png"),
)

ALERT_EXERCISES = ("ApiDown", "HighCPU", "DiskSpaceLow", "TLSExpirySoon", "DatabaseUnavailable")
TRACE_EXERCISES = (
    ("booking", "reports/prr/traces/booking.trace.json"),
    ("payment", "reports/prr/traces/payment.trace.json"),
    ("emergency", "reports/prr/traces/emergency.trace.json"),
)
DEVICE_CERTIFICATION_TARGETS = (
    "Android 11",
    "Android 12",
    "Android 13",
    "Android 14",
    "Android 15",
    "Low-memory device",
    "Poor-network device",
    "Dual-SIM device",
    "Tablet",
)
DEVICE_CERTIFICATION_WORKFLOWS = (
    "Install",
    "Launch",
    "Login",
    "GPS",
    "Offline",
    "Ride",
    "Emergency",
    "Push Notifications",
    "Sync",
    "Recovery",
    "Logout",
)
PRR_APPROVAL_STAGES = (
    "Engineering Review",
    "Operations Review",
    "Security Review",
    "Compliance Review",
    "Product Review",
    "Executive Review",
)
GA_GATE_CHECKS = (
    "PRR approved",
    "Critical findings closed",
    "Operational evidence complete",
    "Release evidence complete",
    "Security approved",
    "Compliance approved",
    "Business approved",
)
AUTOMATION_WORKFLOW = (
    "Requirements",
    "Architecture Validation",
    "Implementation",
    "Testing",
    "Security Scan",
    "Build",
    "Signing",
    "SBOM",
    "Provenance",
    "Deployment",
    "Runtime Verification",
    "Prometheus Verification",
    "Grafana Validation",
    "Alert Exercise",
    "OpenTelemetry Validation",
    "Backup Verification",
    "Replay Verification",
    "APK Certification",
    "Device Certification",
    "Evidence Collection",
    "PRR Approval",
    "Executive GA Approval",
)

MATURITY_LAYERS = (
    "Enterprise Architecture",
    "Repository Implementation",
    "Operational Verification",
    "Governance Approval",
    "Production Operation",
)

EDOS_STUDIOS = (
    "Requirements Studio",
    "Architecture Studio",
    "UX Studio",
    "AI Engineering Studio",
    "API Studio",
    "Security Studio",
    "Build Studio",
    "Release Studio",
    "Deployment Studio",
    "Runtime Studio",
    "Verification Studio",
    "Replay Studio",
    "Observability Studio",
    "Evidence Studio",
    "Compliance Studio",
    "PRR Center",
    "Executive Approval Center",
    "GA Governance Center",
    "Enterprise Command Center",
)

PAYMENT_PROVIDERS = (
    "Stripe",
    "Adyen",
    "PayPal",
    "Square",
    "Braintree",
    "Regional Providers",
    "Mobile Money Providers",
    "Bank Rails",
)

PAYMENT_INTERFACE = ("Authorize", "Capture", "Refund", "Void", "Dispute", "Settlement", "Webhook", "Reconciliation")

PAYMENT_ACTIVATION_STAGES = (
    "Sandbox Integration",
    "Provider Certification",
    "Fraud Validation",
    "Security Validation",
    "Operational Validation",
    "Executive Authorization",
    "Production Payment Enablement",
)

PAYMENT_OPERATIONAL_REQUIREMENTS = (
    "sandbox_certification",
    "webhook_verification",
    "reconciliation_validation",
    "fraud_controls",
    "failover_testing",
)

PRR_EVIDENCE_SOURCES = (
    "Source Control",
    "CI/CD",
    "Security",
    "Testing",
    "Performance",
    "Accessibility",
    "Observability",
    "Architecture",
    "UX",
    "Operations",
    "Release",
    "Monitoring",
)

PRR_PACKAGE_CONTENTS = (
    "build identity",
    "release manifest",
    "SBOM",
    "provenance",
    "test results",
    "security results",
    "accessibility reports",
    "performance reports",
    "operational health",
    "deployment evidence",
    "recommendation",
)

DIGITAL_UX_TWIN_GRAPH = ("Users", "Journeys", "Screens", "Components", "Services", "APIs", "Infrastructure", "Telemetry", "Prediction")
DIGITAL_UX_TWIN_SCENARIOS = (
    "degraded networks",
    "GPS loss",
    "authentication failures",
    "payment failures",
    "accessibility scenarios",
    "localization",
    "offline synchronization",
    "regional routing",
    "disaster recovery",
)
DIGITAL_UX_TWIN_ESTIMATES = (
    "journey completion",
    "latency",
    "abandonment",
    "accessibility issues",
    "operational risk",
    "support demand",
)

INTEGRATION_FABRIC_CONNECTORS = {
    "design": ("Figma", "Penpot", "Storybook", "Zeroheight", "Design Tokens"),
    "engineering": ("GitHub", "CI/CD", "Package Registry", "Artifact Repository"),
    "operations": ("Prometheus", "Grafana", "OpenTelemetry", "Alertmanager", "Cloud Monitoring"),
    "accessibility": ("axe-core", "Pa11y", "Lighthouse", "Accessibility Insights"),
    "knowledge": ("Requirements", "Architecture Decisions", "Pull Requests", "Tests", "Evidence", "Releases", "Runbooks"),
}

TELEMETRY_SIGNALS = (
    "User Interactions",
    "Performance",
    "Failures",
    "Payments",
    "Journeys",
    "Accessibility",
    "Infrastructure",
    "Business KPIs",
)

TELEMETRY_PIPELINE = (
    "Application",
    "OpenTelemetry",
    "Collector",
    "Metrics",
    "Logs",
    "Traces",
    "Analytics",
    "Evidence",
    "Knowledge Graph",
    "Digital Twin",
)

EXECUTIVE_GOVERNANCE_SEQUENCE = (
    "UX Approval",
    "Engineering Approval",
    "Security Approval",
    "Operations Approval",
    "Compliance Approval",
    "PRR Approval",
    "Executive Approval",
    "Production Promotion",
)

OPERATIONAL_READINESS_CAPABILITIES = (
    ("UX Operating System", True, False, "PENDING"),
    ("AI Engineering", True, False, "PENDING"),
    ("Design Integration", True, False, "PENDING"),
    ("Visual Regression", True, False, "PENDING"),
    ("Accessibility Automation", True, False, "PENDING"),
    ("OpenTelemetry", True, False, "PENDING"),
    ("Production Analytics", True, False, "PENDING"),
    ("Digital UX Twin", True, False, "PENDING"),
    ("Automated PRR", True, False, "PENDING"),
    ("Executive Workflow", True, False, "PENDING"),
    ("Payment Sandbox", True, False, "PENDING"),
    ("Production Payments", False, False, "PENDING"),
    ("General Availability", False, False, "PENDING"),
)


def _timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stable_signature(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _evidence_requirement(
    area: str,
    engineering: str,
    evidence_type: str,
    artifacts: tuple[str, ...],
    collector: str,
    live_evidence_required: bool = True,
    human_approval_required: bool = False,
) -> dict[str, Any]:
    return {
        "area": area,
        "engineering": engineering,
        "live_evidence_required": live_evidence_required,
        "human_approval_required": human_approval_required,
        "status": "EVIDENCE_PENDING" if live_evidence_required else "WORKFLOW_READY",
        "can_honestly_mark_complete_now": False,
        "evidence_type": evidence_type,
        "collector": collector,
        "artifacts": list(artifacts),
    }


def prometheus_target_verifier_spec() -> dict[str, Any]:
    return {
        "name": "NovaCodePro Monitoring Verifier",
        "source": "Prometheus API /api/v1/targets",
        "required_targets": list(REQUIRED_PROMETHEUS_TARGETS),
        "pass_condition": "Every required target has health == up in the production Prometheus target set.",
        "evidence_schema": {
            "verification": "PASS|FAIL",
            "targets": {"healthy": 0, "unhealthy": len(REQUIRED_PROMETHEUS_TARGETS)},
            "timestamp": "required",
            "environment": "production",
            "signature": "required",
        },
        "artifact": "reports/prr/prometheus-targets.yaml",
    }


def grafana_dashboard_validator_spec() -> dict[str, Any]:
    return {
        "name": "NovaCodePro Grafana Dashboard Validator",
        "checks": [
            "Dashboard exists",
            "Datasource connected",
            "Panels loaded",
            "Queries executed",
            "No panel errors",
            "Screenshot captured",
        ],
        "dashboards": [{"name": name, "screenshot": path} for name, path in GRAFANA_DASHBOARDS],
        "pass_condition": "Every required dashboard renders and produces an immutable screenshot artifact.",
    }


def alertmanager_exercise_spec() -> dict[str, Any]:
    return {
        "name": "NovaCodePro Alertmanager Exercise",
        "alerts": list(ALERT_EXERCISES),
        "checks": ["Alert created", "Alert received", "Alert routed", "Notification delivered", "Notification acknowledged"],
        "evidence_schema": {
            "alert": "required",
            "delivery": "email|sms|push|chat|webhook",
            "status": "PASS|FAIL",
            "acknowledged": "required",
            "signature": "required",
        },
        "artifact": "reports/prr/alertmanager-exercise.yaml",
    }


def opentelemetry_trace_verifier_spec() -> dict[str, Any]:
    return {
        "name": "NovaCodePro OpenTelemetry End-to-End Trace Verifier",
        "path": ["NGINX", "API", "Booking Engine", "Postgres", "Event Store", "Replay", "Response"],
        "checks": ["trace_id", "span_id", "parent relationships", "timings", "attributes"],
        "traces": [{"scenario": scenario, "artifact": artifact} for scenario, artifact in TRACE_EXERCISES],
        "pass_condition": "Each scenario records a complete distributed trace with valid parent-child span relationships.",
    }


def backup_restore_exercise_spec() -> dict[str, Any]:
    return {
        "name": "NovaCodePro Backup and Restore Exercise",
        "backup_scope": ["Database", "Evidence", "Certificates", "Configuration", "Release artifacts"],
        "restore_target": "Clean environment",
        "verification": ["Row counts", "Checksums", "Health endpoints", "Replay consistency", "Application startup"],
        "evidence_schema": {"backup": "PASS|FAIL", "restore": "PASS|FAIL", "verified": "PASS|FAIL", "signature": "required"},
        "artifact": "reports/prr/backup-restore-exercise.yaml",
    }


def apk_certification_spec() -> dict[str, Any]:
    return {
        "name": "NovaCodePro Mobile Release Certification",
        "applications": ["Rider", "Driver"],
        "checks": [
            "Version",
            "Package ID",
            "Signing certificate",
            "Release manifest",
            "SHA256",
            "SBOM",
            "SLSA provenance",
            "API endpoint",
            "Environment",
            "Permissions",
            "Network Security Config",
            "Play Integrity",
            "SafetyNet if applicable",
        ],
        "artifacts": ["Release Report", "APK Manifest", "SHA256", "SBOM", "Provenance", "Signing Report"],
        "pass_condition": "Fresh signed artifacts pass all release certification checks.",
    }


def physical_device_certification_spec() -> dict[str, Any]:
    return {
        "name": "NovaCodePro Physical Device Certification",
        "simulation_allowed": False,
        "required_devices": list(DEVICE_CERTIFICATION_TARGETS),
        "workflows": list(DEVICE_CERTIFICATION_WORKFLOWS),
        "evidence": ["Video", "Screenshots", "Logs", "APK hash", "Device model", "Android version"],
        "status": "PHYSICAL_DEVICE_EVIDENCE_REQUIRED",
    }


def prr_approval_workflow_spec() -> dict[str, Any]:
    return {
        "name": "NovaCodePro PRR Center",
        "status": "READY_FOR_PRR_APPROVAL",
        "stages": [
            {
                "stage": stage,
                "decision_required": True,
                "decision": "PENDING",
                "required_fields": ["reviewer", "role", "decision", "timestamp", "signature", "evidence_refs"],
            }
            for stage in PRR_APPROVAL_STAGES
        ],
        "approved_when": "All mandatory stages record APPROVED decisions with signatures and evidence references.",
        "ga_eligible": False,
    }


def ga_governance_engine_spec() -> dict[str, Any]:
    return {
        "name": "NovaCodePro GA Governance Engine",
        "status": "GA_BLOCKED_PENDING_EVIDENCE_AND_HUMAN_APPROVAL",
        "checks": [{"name": check, "status": "PENDING"} for check in GA_GATE_CHECKS],
        "transition_rule": "Only authenticated human governance authorities may approve GA after evidence and PRR are complete.",
        "ga_allowed": False,
        "real_payments_enabled": False,
        "audit_required": True,
        "signature_required": True,
    }


def payment_activation_workstream() -> dict[str, Any]:
    return {
        "name": "Enterprise Payment Activation",
        "principle": "Payment activation remains isolated from product deployment.",
        "providers": list(PAYMENT_PROVIDERS),
        "common_interface": list(PAYMENT_INTERFACE),
        "lifecycle": list(PAYMENT_ACTIVATION_STAGES),
        "operational_requirements": list(PAYMENT_OPERATIONAL_REQUIREMENTS),
        "status": "PRODUCTION_PAYMENT_ENABLEMENT_BLOCKED",
        "repository_complete": True,
        "operational_verified": False,
        "governance_approved": False,
        "production_payments_enabled": False,
        "completion_rule": "No provider is operational until sandbox certification, webhook verification, reconciliation validation, fraud controls, and failover testing pass with signed evidence.",
    }


def automated_prr_evidence_workstream() -> dict[str, Any]:
    return {
        "name": "Automated PRR Evidence",
        "pipeline": ["Evidence Producer", "Evidence Store", "Evidence Validator", "PRR Package Generator", "Review Dashboard"],
        "sources": list(PRR_EVIDENCE_SOURCES),
        "package_contents": list(PRR_PACKAGE_CONTENTS),
        "review_model": "Reviewers validate signed evidence rather than collecting evidence manually.",
        "status": "EVIDENCE_AGGREGATION_IMPLEMENTED_LIVE_EVIDENCE_PENDING",
    }


def digital_ux_twin_workstream() -> dict[str, Any]:
    return {
        "name": "Digital UX Twin",
        "model": list(DIGITAL_UX_TWIN_GRAPH),
        "simulation_scenarios": list(DIGITAL_UX_TWIN_SCENARIOS),
        "estimates": list(DIGITAL_UX_TWIN_ESTIMATES),
        "production_user_impact": "NONE",
        "status": "MODEL_IMPLEMENTED_PRODUCTION_TELEMETRY_PENDING",
    }


def enterprise_integration_fabric_workstream() -> dict[str, Any]:
    return {
        "name": "Enterprise Integration Fabric",
        "connectors": {domain: list(connectors) for domain, connectors in INTEGRATION_FABRIC_CONNECTORS.items()},
        "sync_evidence": ["timestamps", "provenance", "audit records", "evidence", "digital signatures"],
        "status": "CONNECTOR_FABRIC_IMPLEMENTED_CREDENTIALS_AND_LIVE_SYNC_PENDING",
    }


def live_telemetry_platform_spec() -> dict[str, Any]:
    return {
        "name": "Live Telemetry Platform",
        "signals": list(TELEMETRY_SIGNALS),
        "pipeline": list(TELEMETRY_PIPELINE),
        "feeds": ["Analytics", "Evidence", "Knowledge Graph", "Digital Twin", "Governance"],
        "status": "TELEMETRY_PIPELINE_IMPLEMENTED_PRODUCTION_INGESTION_PENDING",
    }


def operational_readiness_matrix() -> dict[str, Any]:
    return {
        "status": "REPOSITORY_IMPLEMENTED_OPERATIONAL_AND_GOVERNANCE_PENDING",
        "columns": ["Repository", "Operational", "Governance"],
        "capabilities": [
            {
                "capability": capability,
                "repository": repository,
                "operational": operational,
                "governance": governance,
            }
            for capability, repository, operational, governance in OPERATIONAL_READINESS_CAPABILITIES
        ],
    }


def operational_readiness_program(environment: str = "production") -> dict[str, Any]:
    body = {
        "program": "NovaCodePro Operational Readiness Program",
        "environment": environment,
        "status": "REPOSITORY_IMPLEMENTED_LIVE_EVIDENCE_AND_GOVERNANCE_PENDING",
        "generated_at": _timestamp(),
        "maturity_layers": list(MATURITY_LAYERS),
        "edos_studios": [
            {
                "studio": studio,
                "owns": ["APIs", "domain models", "persistent stores", "events", "evidence", "governance rules", "dashboards", "audit history"],
            }
            for studio in EDOS_STUDIOS
        ],
        "workstreams": {
            "enterprise_payment_activation": payment_activation_workstream(),
            "automated_prr_evidence": automated_prr_evidence_workstream(),
            "digital_ux_twin": digital_ux_twin_workstream(),
            "enterprise_integration_fabric": enterprise_integration_fabric_workstream(),
            "live_telemetry_platform": live_telemetry_platform_spec(),
        },
        "executive_governance": {
            "sequence": list(EXECUTIVE_GOVERNANCE_SEQUENCE),
            "invariants": {
                "repository_complete": True,
                "operational_verified": False,
                "governance_complete": False,
                "ga_allowed": False,
                "real_payments_enabled": False,
            },
            "transition_rule": "Only authenticated approvals plus signed live evidence may permit GA or production payment enablement.",
        },
        "readiness_matrix": operational_readiness_matrix(),
        "ga_allowed": False,
        "real_payments_enabled": False,
    }
    body["signature"] = _stable_signature({key: value for key, value in body.items() if key not in {"generated_at", "signature"}})
    return body


def evaluate_operational_readiness(
    evidence: dict[str, str] | None = None,
    approvals: dict[str, str] | None = None,
    payment_evidence: dict[str, str] | None = None,
) -> dict[str, Any]:
    evidence = evidence or {}
    approvals = approvals or {}
    payment_evidence = payment_evidence or {}
    required_evidence = {
        "design_sync": "Design workspace synchronization",
        "visual_regression": "Visual regression execution",
        "accessibility": "Accessibility automation",
        "opentelemetry": "OpenTelemetry production traces",
        "analytics": "Production analytics ingestion",
        "digital_ux_twin": "Digital UX Twin telemetry synchronization",
        "automated_prr": "Automated PRR package generation",
    }
    required_approvals = {
        "ux": "UX Approval",
        "engineering": "Engineering Approval",
        "security": "Security Approval",
        "operations": "Operations Approval",
        "compliance": "Compliance Approval",
        "prr": "PRR Approval",
        "executive": "Executive Approval",
    }
    evidence_checks = [
        {"id": key, "name": name, "status": "PASS" if evidence.get(key) == "PASS" else "PENDING"}
        for key, name in required_evidence.items()
    ]
    approval_checks = [
        {"id": key, "name": name, "status": "APPROVED" if approvals.get(key) == "APPROVED" else "PENDING"}
        for key, name in required_approvals.items()
    ]
    payment_checks = [
        {"id": key, "name": key.replace("_", " ").title(), "status": "PASS" if payment_evidence.get(key) == "PASS" else "PENDING"}
        for key in PAYMENT_OPERATIONAL_REQUIREMENTS
    ]
    operational_verified = all(item["status"] == "PASS" for item in evidence_checks)
    governance_complete = all(item["status"] == "APPROVED" for item in approval_checks)
    payment_verified = all(item["status"] == "PASS" for item in payment_checks)
    ga_allowed = bool(operational_verified and governance_complete)
    real_payments_enabled = bool(ga_allowed and payment_verified)
    body = {
        "status": "PRODUCTION_OPERATION_ALLOWED" if ga_allowed else "OPERATIONAL_READINESS_BLOCKED",
        "repository_complete": True,
        "operational_verified": operational_verified,
        "governance_complete": governance_complete,
        "ga_allowed": ga_allowed,
        "real_payments_enabled": real_payments_enabled,
        "evidence_checks": evidence_checks,
        "approval_checks": approval_checks,
        "payment_checks": payment_checks,
        "generated_at": _timestamp(),
    }
    body["signature"] = _stable_signature({key: value for key, value in body.items() if key not in {"generated_at", "signature"}})
    return body


def production_completion_evidence_requirements() -> list[dict[str, Any]]:
    return [
        _evidence_requirement("Prometheus", "Monitoring verifier implemented", "target_status", ("reports/prr/prometheus-targets.yaml",), "prometheus_target_verifier"),
        _evidence_requirement("Grafana", "Dashboard validator implemented", "dashboard_rendering", tuple(path for _, path in GRAFANA_DASHBOARDS), "grafana_dashboard_validator"),
        _evidence_requirement("Alertmanager", "Alert simulation implemented", "actual_notification", ("reports/prr/alertmanager-exercise.yaml",), "alertmanager_exercise"),
        _evidence_requirement("OpenTelemetry", "Trace verifier implemented", "real_distributed_traces", tuple(path for _, path in TRACE_EXERCISES), "opentelemetry_trace_verifier"),
        _evidence_requirement("Backup/Restore", "Backup and restore exercise automation implemented", "successful_restore", ("reports/prr/backup-restore-exercise.yaml",), "backup_restore_exercise"),
        _evidence_requirement("APK Certification", "Mobile release certification implemented", "fresh_signed_artifacts", ("reports/mobile/releases/production/release-certificate.yaml",), "apk_certification"),
        _evidence_requirement("Device Certification", "Device certification checklist implemented", "physical_devices", ("reports/mobile/device-certification/",), "physical_device_certification"),
        _evidence_requirement("PRR Approval", "Executable PRR workflow implemented", "board_signatures", ("reports/prr/prr-approval-certificate.yaml",), "prr_center", human_approval_required=True),
        _evidence_requirement("Executive Approval", "GA governance engine implemented", "executive_authorization", ("reports/prr/ga-approval-record.yaml",), "ga_governance_engine", human_approval_required=True),
    ]


def production_completion_program(environment: str = "production") -> dict[str, Any]:
    body = {
        "program": "NovaCodePro Production Completion Program",
        "environment": environment,
        "status": "AUTOMATION_IMPLEMENTED_LIVE_EVIDENCE_PENDING",
        "generated_at": _timestamp(),
        "governance_principle": "Implementation, verification, certification, and approval remain separate states.",
        "ga_allowed": False,
        "real_payments_enabled": False,
        "completion_rule": "No production capability is complete until live evidence and required human approvals are recorded.",
        "evidence_requirements": production_completion_evidence_requirements(),
        "verifiers": {
            "prometheus": prometheus_target_verifier_spec(),
            "grafana": grafana_dashboard_validator_spec(),
            "alertmanager": alertmanager_exercise_spec(),
            "opentelemetry": opentelemetry_trace_verifier_spec(),
            "backup_restore": backup_restore_exercise_spec(),
            "apk_certification": apk_certification_spec(),
            "device_certification": physical_device_certification_spec(),
        },
        "prr_workflow": prr_approval_workflow_spec(),
        "ga_governance": ga_governance_engine_spec(),
        "automation_workflow": list(AUTOMATION_WORKFLOW),
    }
    body["signature"] = _stable_signature({key: value for key, value in body.items() if key not in {"generated_at", "signature"}})
    return body


def evaluate_ga_governance(evidence: dict[str, str] | None = None, approvals: dict[str, str] | None = None) -> dict[str, Any]:
    evidence = evidence or {}
    approvals = approvals or {}
    required_evidence = {
        "prometheus": "Prometheus target verification",
        "grafana": "Grafana dashboard rendering",
        "alertmanager": "Alertmanager notification delivery",
        "opentelemetry": "OpenTelemetry distributed traces",
        "backup_restore": "Backup and restore verification",
        "apk_certification": "Rider and Driver APK certification",
        "device_certification": "Physical device certification",
    }
    required_approvals = {
        "engineering": "Engineering Review",
        "operations": "Operations Review",
        "security": "Security Review",
        "compliance": "Compliance Review",
        "product": "Product Review",
        "executive": "Executive Review",
    }
    evidence_checks = [
        {"id": key, "name": name, "status": "PASS" if evidence.get(key) == "PASS" else "PENDING"}
        for key, name in required_evidence.items()
    ]
    approval_checks = [
        {"id": key, "name": name, "status": "APPROVED" if approvals.get(key) == "APPROVED" else "PENDING"}
        for key, name in required_approvals.items()
    ]
    passed = all(item["status"] == "PASS" for item in evidence_checks)
    approved = all(item["status"] == "APPROVED" for item in approval_checks)
    body = {
        "status": "APPROVED" if passed and approved else "GA_BLOCKED",
        "ga_allowed": bool(passed and approved),
        "real_payments_enabled": bool(passed and approved),
        "evidence_checks": evidence_checks,
        "approval_checks": approval_checks,
        "audit_record_required": True,
        "cryptographic_signature_required": True,
        "generated_at": _timestamp(),
    }
    body["signature"] = _stable_signature({key: value for key, value in body.items() if key not in {"generated_at", "signature"}})
    return body
