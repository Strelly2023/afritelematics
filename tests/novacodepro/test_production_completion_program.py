from __future__ import annotations

from pathlib import Path

from afritech.novacodepro.production_readiness import (
    evaluate_ga_governance,
    evaluate_operational_readiness,
    operational_readiness_program,
    production_completion_program,
    require_production_dependencies,
    validate_production_dependencies,
)


ROOT = Path(__file__).resolve().parents[2]


def test_production_readiness_fails_closed_without_external_dependencies() -> None:
    report = validate_production_dependencies("production", environ={})

    assert report["profile"] == "production"
    assert report["status"] == "BLOCKED"
    assert "NOVACODEPRO_DATABASE_URL" in report["missing"]
    assert "NOVACODEPRO_TEMPORAL_TARGET" in report["missing"]
    assert "NOVACODEPRO_EVENT_BROKERS" in report["missing"]
    assert "NOVACODEPRO_EVIDENCE_KMS_KEY_ID" in report["missing"]
    assert "NOVACODEPRO_EVIDENCE_BUCKET" in report["missing"]
    assert "NOVACODEPRO_AUDIT_VERIFIER_ROLE_ARN" in report["missing"]


def test_production_readiness_passes_only_when_required_dependencies_are_explicit() -> None:
    env = {
        "NOVACODEPRO_DATABASE_URL": "postgresql://novacodepro.example/control",
        "NOVACODEPRO_TEMPORAL_TARGET": "temporal.example:7233",
        "NOVACODEPRO_EVENT_BROKERS": "redpanda-1:9092,redpanda-2:9092,redpanda-3:9092",
        "NOVACODEPRO_SCHEMA_REGISTRY_URL": "https://schema.example",
        "NOVACODEPRO_EVIDENCE_KMS_KEY_ID": "arn:aws:kms:ap-southeast-2:111122223333:key/example",
        "NOVACODEPRO_EVIDENCE_BUCKET": "novatech-evidence-archive-ap-southeast-2",
        "NOVACODEPRO_NEO4J_URI": "neo4j+s://graph.example",
        "OTEL_EXPORTER_OTLP_ENDPOINT": "https://otel.example",
        "NOVACODEPRO_ROUTE53_ZONE_ID": "Z123456789",
        "NOVACODEPRO_GLOBAL_ACCELERATOR_ARN": "arn:aws:globalaccelerator::111122223333:accelerator/example",
        "NOVACODEPRO_AUDIT_VERIFIER_ROLE_ARN": "arn:aws:iam::444455556666:role/NovaCodeProEvidenceVerifier",
    }

    report = require_production_dependencies("production", environ=env)

    assert report["status"] == "READY"
    assert report["missing"] == []


def test_postgres_migration_declares_required_control_plane_tables_and_rls() -> None:
    migration = (ROOT / "afritech/novacodepro/persistence/migrations/0001_enterprise_control_plane.sql").read_text()
    rls = (ROOT / "afritech/novacodepro/persistence/migrations/0013_rls.sql").read_text()

    for table in (
        "identity_context_snapshots",
        "enterprise_objects",
        "enterprise_object_versions",
        "enterprise_relationships",
        "workflow_executions",
        "workflow_stages",
        "workflow_commands",
        "workflow_compensations",
        "policy_decisions",
        "risk_assessments",
        "approval_requests",
        "approval_votes",
        "agent_tasks",
        "tool_authorizations",
        "digital_twins",
        "digital_twin_states",
        "digital_twin_observations",
        "knowledge_items",
        "knowledge_reviews",
        "evidence_metadata",
        "event_outbox",
        "event_inbox",
        "projection_offsets",
        "continuous_assurance_records",
    ):
        assert f"CREATE TABLE IF NOT EXISTS {table}" in migration
        assert table in rls

    assert "ENABLE ROW LEVEL SECURITY" in rls
    assert "FORCE ROW LEVEL SECURITY" in rls
    assert "current_setting(''app.tenant_id'', true)" in rls
    assert "novacodepro_apply_security_context" in rls


def test_deployment_profile_documents_no_silent_production_fallback() -> None:
    profile = (ROOT / "deploy/novacodepro/production/production-completion-profile.yml").read_text()

    assert "production_claim_allowed: false" in profile
    assert "production_claim_allowed: true" in profile
    assert "KMS_VERIFIED" in profile
    assert "DEVELOPMENT_VERIFIED" in profile
    assert "postgres_rls_negative_tests" in profile
    assert "temporal_worker_restart" in profile
    assert "redpanda_replay" in profile
    assert "regional_failover" in profile


def test_production_completion_program_defines_objective_live_evidence_requirements() -> None:
    program = production_completion_program("production")

    assert program["status"] == "AUTOMATION_IMPLEMENTED_LIVE_EVIDENCE_PENDING"
    assert program["ga_allowed"] is False
    assert program["real_payments_enabled"] is False

    areas = {item["area"]: item for item in program["evidence_requirements"]}
    for area in (
        "Prometheus",
        "Grafana",
        "Alertmanager",
        "OpenTelemetry",
        "Backup/Restore",
        "APK Certification",
        "Device Certification",
        "PRR Approval",
        "Executive Approval",
    ):
        assert areas[area]["can_honestly_mark_complete_now"] is False

    assert program["verifiers"]["prometheus"]["required_targets"] == [
        "afritech-api",
        "nginx",
        "prometheus",
        "grafana",
        "node-exporter",
        "postgres-exporter",
        "cadvisor",
        "otel-collector",
        "alertmanager",
    ]
    assert "reports/prr/grafana/NovaRide.png" in [
        dashboard["screenshot"] for dashboard in program["verifiers"]["grafana"]["dashboards"]
    ]
    assert "ApiDown" in program["verifiers"]["alertmanager"]["alerts"]
    assert "reports/prr/traces/booking.trace.json" in [
        trace["artifact"] for trace in program["verifiers"]["opentelemetry"]["traces"]
    ]
    assert program["prr_workflow"]["status"] == "READY_FOR_PRR_APPROVAL"
    assert program["ga_governance"]["status"] == "GA_BLOCKED_PENDING_EVIDENCE_AND_HUMAN_APPROVAL"


def test_ga_governance_gate_fails_closed_until_evidence_and_approvals_exist() -> None:
    blocked = evaluate_ga_governance()

    assert blocked["status"] == "GA_BLOCKED"
    assert blocked["ga_allowed"] is False
    assert blocked["real_payments_enabled"] is False
    assert any(check["status"] == "PENDING" for check in blocked["evidence_checks"])
    assert any(check["status"] == "PENDING" for check in blocked["approval_checks"])

    approved = evaluate_ga_governance(
        evidence={
            "prometheus": "PASS",
            "grafana": "PASS",
            "alertmanager": "PASS",
            "opentelemetry": "PASS",
            "backup_restore": "PASS",
            "apk_certification": "PASS",
            "device_certification": "PASS",
        },
        approvals={
            "engineering": "APPROVED",
            "operations": "APPROVED",
            "security": "APPROVED",
            "compliance": "APPROVED",
            "product": "APPROVED",
            "executive": "APPROVED",
        },
    )

    assert approved["status"] == "APPROVED"
    assert approved["ga_allowed"] is True
    assert approved["real_payments_enabled"] is True


def test_operational_readiness_program_defines_workstreams_and_blocks_production_claims() -> None:
    program = operational_readiness_program("production")

    assert program["program"] == "NovaCodePro Operational Readiness Program"
    assert program["status"] == "REPOSITORY_IMPLEMENTED_LIVE_EVIDENCE_AND_GOVERNANCE_PENDING"
    assert program["maturity_layers"] == [
        "Enterprise Architecture",
        "Repository Implementation",
        "Operational Verification",
        "Governance Approval",
        "Production Operation",
    ]
    assert program["ga_allowed"] is False
    assert program["real_payments_enabled"] is False
    assert "Enterprise Command Center" in [studio["studio"] for studio in program["edos_studios"]]

    payment = program["workstreams"]["enterprise_payment_activation"]
    assert payment["status"] == "PRODUCTION_PAYMENT_ENABLEMENT_BLOCKED"
    assert "Stripe" in payment["providers"]
    assert "Mobile Money Providers" in payment["providers"]
    assert payment["common_interface"] == [
        "Authorize",
        "Capture",
        "Refund",
        "Void",
        "Dispute",
        "Settlement",
        "Webhook",
        "Reconciliation",
    ]
    assert payment["production_payments_enabled"] is False

    prr = program["workstreams"]["automated_prr_evidence"]
    assert "Evidence Producer" in prr["pipeline"]
    assert "SBOM" in prr["package_contents"]
    assert "Observability" in prr["sources"]

    twin = program["workstreams"]["digital_ux_twin"]
    assert "payment failures" in twin["simulation_scenarios"]
    assert "operational risk" in twin["estimates"]

    fabric = program["workstreams"]["enterprise_integration_fabric"]
    assert "Figma" in fabric["connectors"]["design"]
    assert "OpenTelemetry" in fabric["connectors"]["operations"]

    telemetry = program["workstreams"]["live_telemetry_platform"]
    assert telemetry["pipeline"] == [
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
    ]

    rows = {row["capability"]: row for row in program["readiness_matrix"]["capabilities"]}
    assert rows["UX Operating System"]["repository"] is True
    assert rows["UX Operating System"]["operational"] is False
    assert rows["Production Payments"]["repository"] is False
    assert rows["General Availability"]["repository"] is False


def test_operational_readiness_evaluator_requires_evidence_approvals_and_payment_checks() -> None:
    blocked = evaluate_operational_readiness()

    assert blocked["status"] == "OPERATIONAL_READINESS_BLOCKED"
    assert blocked["repository_complete"] is True
    assert blocked["operational_verified"] is False
    assert blocked["governance_complete"] is False
    assert blocked["ga_allowed"] is False
    assert blocked["real_payments_enabled"] is False

    evidence = {
        "design_sync": "PASS",
        "visual_regression": "PASS",
        "accessibility": "PASS",
        "opentelemetry": "PASS",
        "analytics": "PASS",
        "digital_ux_twin": "PASS",
        "automated_prr": "PASS",
    }
    approvals = {
        "ux": "APPROVED",
        "engineering": "APPROVED",
        "security": "APPROVED",
        "operations": "APPROVED",
        "compliance": "APPROVED",
        "prr": "APPROVED",
        "executive": "APPROVED",
    }
    ga_only = evaluate_operational_readiness(evidence=evidence, approvals=approvals)

    assert ga_only["status"] == "PRODUCTION_OPERATION_ALLOWED"
    assert ga_only["ga_allowed"] is True
    assert ga_only["real_payments_enabled"] is False
    assert any(check["status"] == "PENDING" for check in ga_only["payment_checks"])

    payment_evidence = {
        "sandbox_certification": "PASS",
        "webhook_verification": "PASS",
        "reconciliation_validation": "PASS",
        "fraud_controls": "PASS",
        "failover_testing": "PASS",
    }
    payments = evaluate_operational_readiness(evidence=evidence, approvals=approvals, payment_evidence=payment_evidence)

    assert payments["ga_allowed"] is True
    assert payments["real_payments_enabled"] is True
    assert all(check["status"] == "PASS" for check in payments["payment_checks"])
