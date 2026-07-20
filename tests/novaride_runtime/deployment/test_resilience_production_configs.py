from __future__ import annotations

from pathlib import Path


def test_resilience_alert_rules_include_emergency_queue_provider_and_sync_alerts() -> None:
    alerts = Path("config/novaride/resilience/alert_rules.yaml").read_text()

    for name in [
        "NovaRideEmergencyPathUnavailable",
        "NovaRideOfflineQueueBacklog",
        "NovaRideProviderFallbackSpike",
        "NovaRideSyncOldestCommand",
    ]:
        assert name in alerts

    for metric in [
        "novaride_emergency_path_available",
        "novaride_offline_queue_depth",
        "novaride_provider_fallback_total",
        "novaride_offline_sync_age_seconds",
    ]:
        assert metric in alerts


def test_circuit_breaker_config_has_emergency_fast_failover() -> None:
    config = Path("config/novaride/resilience/circuit_breakers.yaml").read_text()

    assert "card_primary:" in config
    assert "emergency_dispatch:" in config
    assert "failure_threshold: 2" in config
    assert "open_duration_seconds: 15" in config
    assert "half_open_max_calls: 1" in config


def test_kubernetes_topology_enforces_zone_spread_and_readiness() -> None:
    topology = Path("config/novaride/resilience/kubernetes_topology.yaml").read_text()

    assert "topologySpreadConstraints:" in topology
    assert "topology.kubernetes.io/zone" in topology
    assert "whenUnsatisfiable: DoNotSchedule" in topology
    assert "podAntiAffinity:" in topology
    assert "readinessProbe:" in topology
    assert "startupProbe:" in topology


def test_dr_exercises_require_recovery_evidence_package() -> None:
    exercises = Path("config/novaride/resilience/dr_exercises.yaml").read_text()

    for exercise in [
        "zone_loss_simulation",
        "database_primary_failure",
        "payment_provider_outage",
        "offline_queue_replay",
        "emergency_path_verification",
    ]:
        assert exercise in exercises

    for evidence in [
        "detection_time",
        "failover_time",
        "rto_result",
        "rpo_result",
        "evidence_package",
    ]:
        assert evidence in exercises
