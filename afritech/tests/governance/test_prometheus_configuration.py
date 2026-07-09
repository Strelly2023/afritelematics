from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PROM = ROOT / "deploy/production/monitoring/prometheus/prometheus.yml"
ALERTS = ROOT / "deploy/production/monitoring/prometheus/alerts.yml"
RULES = ROOT / "deploy/production/monitoring/prometheus/recording_rules.yml"


def test_prometheus_configuration_includes_platform_scrapes_and_rules() -> None:
    for path in (PROM, ALERTS, RULES):
        assert path.exists()

    text = PROM.read_text(encoding="utf-8")
    for item in (
        "afritech-api:8000",
        "nginx-exporter:9113",
        "node-exporter:9100",
        "postgres-exporter:9187",
        "cadvisor:8080",
        "alertmanager:9093",
        "/etc/prometheus/alerts.yml",
        "/etc/prometheus/recording_rules.yml",
    ):
        assert item in text

    alerts = ALERTS.read_text(encoding="utf-8")
    for item in (
        "ApiDown",
        "NginxDown",
        "DatabaseDown",
        "ContainerUnhealthy",
        "CertificateExpirySoon",
        "CpuHigh",
        "MemoryHigh",
        "DiskHigh",
        "ApiErrorRateHigh",
        "HighLatency",
    ):
        assert item in alerts

    rules = RULES.read_text(encoding="utf-8")
    for item in (
        "afritech_api:request_rate:5m",
        "afritech_api:error_rate:5m",
        "afritech_api:p95_latency_seconds",
    ):
        assert item in rules
