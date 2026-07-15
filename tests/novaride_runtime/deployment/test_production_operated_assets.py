from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_production_kubernetes_assets_include_api_workers_security_and_scaling() -> None:
    root = Path("deploy/novaride/production")
    combined = "\n".join(path.read_text() for path in root.glob("*.yaml"))

    for token in [
        "kind: Deployment",
        "kind: Service",
        "kind: PodDisruptionBudget",
        "kind: HorizontalPodAutoscaler",
        "kind: ServiceAccount",
        "kind: NetworkPolicy",
        "topologySpreadConstraints",
        "podAntiAffinity",
        "readinessProbe",
        "livenessProbe",
        "startupProbe",
        "novaride-outbox-publisher",
        "novaride-provider-probes",
        "novaride-mobile-sync-worker",
        "novaride-reconciliation-worker",
        "novaride-resilience-evaluator",
        "secretRef:",
    ]:
        assert token in combined


def test_grafana_dashboards_are_valid_and_cover_required_views() -> None:
    dashboard_paths = sorted(Path("deploy/novaride/monitoring/dashboards").glob("*.json"))
    assert len(dashboard_paths) >= 12
    titles = [json.loads(path.read_text())["title"] for path in dashboard_paths]

    for title in [
        "NovaRide Executive Availability",
        "NovaRide Regional Health",
        "NovaRide Provider Health",
        "NovaRide Mobile Offline Synchronization",
        "NovaRide Circuit Breakers",
        "NovaRide Payment Resilience",
        "NovaRide Emergency Path",
        "NovaRide PostgreSQL and Outbox",
        "NovaRide Kafka and Event Processing",
        "NovaRide Multi-Zone Infrastructure",
        "NovaRide SLO and Error Budget",
        "NovaRide Incident and Recovery Evidence",
    ]:
        assert title in titles


def test_production_alerts_have_runbooks_dashboards_and_routing() -> None:
    alerts = Path("deploy/novaride/monitoring/alerts-production.yml").read_text()
    routing = Path("deploy/novaride/monitoring/alertmanager.yml").read_text()

    for alert in [
        "NovaRideEmergencyPathUnavailable",
        "NovaRideDatabasePrimaryUnavailable",
        "NovaRideKafkaUnavailable",
        "NovaRidePaymentProvidersAllUnavailable",
        "NovaRideMobileSyncBacklogBeyondRTO",
        "NovaRideEvidencePublicationFailure",
    ]:
        assert alert in alerts
    assert "runbook_url" in alerts
    assert "dashboard:" in alerts
    assert "payment-operations" in routing
    assert "emergency-operations" in routing
    assert "url_file:" in routing


def test_mobile_offline_queue_modules_use_secure_store_and_priorities() -> None:
    for path in [
        Path("rider_app/core/services/offlineQueue.service.ts"),
        Path("driver_app/core/services/offlineQueue.service.ts"),
    ]:
        source = path.read_text()
        assert "expo-secure-store" in source
        assert "@react-native-async-storage/async-storage" in source
        assert "EMERGENCY" in source
        assert "DEAD_LETTER" in source
        assert "idempotencyKey" in source


def test_dr_exercise_script_generates_machine_readable_evidence(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/novaride/run_dr_exercise.py",
            "--exercise",
            "emergency-path-verification",
            "--environment",
            "controlled_pilot",
            "--region",
            "KE",
            "--output",
            str(tmp_path),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    output_path = Path(result.stdout.strip())
    payload = json.loads(output_path.read_text())
    assert payload["final_verdict"] == "DRY_RUN_EVIDENCE_GENERATED"
    assert payload["rto_result"] == "not_live_tested"


def test_runbooks_and_docs_exist_for_operated_platform() -> None:
    required = [
        "card_provider_outage.md",
        "mobile_money_outage.md",
        "all_payment_providers_unavailable.md",
        "map_provider_outage.md",
        "sms_whatsapp_outage.md",
        "database_primary_failure.md",
        "redis_failure.md",
        "kafka_failure.md",
        "offline_synchronization_backlog.md",
        "conflict_backlog.md",
        "outbox_backlog.md",
        "availability_zone_loss.md",
        "region_isolation.md",
        "emergency_path_failure.md",
        "rollback_after_failed_deployment.md",
        "recovery_verification.md",
    ]
    runbook_dir = Path("docs/operations/novaride/runbooks")
    for name in required:
        assert (runbook_dir / name).exists()

    assert Path("docs/architecture/NOVARIDE_PRODUCTION_OPERATED_PLATFORM.md").exists()
    assert Path("docs/operations/novaride/PRODUCTION_OPERATIONS_GUIDE.md").exists()
