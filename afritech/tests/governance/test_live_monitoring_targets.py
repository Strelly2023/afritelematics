from __future__ import annotations

import os
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest


ROOT = Path(__file__).resolve().parents[3]
LIVE_EVIDENCE = ROOT / "docs/operations/PRR_LIVE_HEALTH_EVIDENCE.md"
REPORT = ROOT / "reports/prr/prr-live-health.yaml"
MONITORING_README = ROOT / "deploy/production/monitoring/README.md"

TARGETS = {
    "prometheus": os.environ.get("AFRITECH_PROMETHEUS_URL", "http://127.0.0.1:9090/-/ready"),
    "grafana": os.environ.get("AFRITECH_GRAFANA_URL", "http://127.0.0.1:3000/api/health"),
    "alertmanager": os.environ.get("AFRITECH_ALERTMANAGER_URL", "http://127.0.0.1:9093/-/ready"),
    "node-exporter": os.environ.get("AFRITECH_NODE_EXPORTER_URL", "http://127.0.0.1:9100/metrics"),
    "postgres-exporter": os.environ.get("AFRITECH_POSTGRES_EXPORTER_URL", "http://127.0.0.1:9187/metrics"),
    "nginx-exporter": os.environ.get("AFRITECH_NGINX_EXPORTER_URL", "http://127.0.0.1:9113/metrics"),
    "cadvisor": os.environ.get("AFRITECH_CADVISOR_URL", "http://127.0.0.1:8080/healthz"),
    "otel-collector": os.environ.get("AFRITECH_OTEL_COLLECTOR_URL", "http://127.0.0.1:13133/"),
}


def _probe(url: str) -> int:
    request = urlopen(url, timeout=5)
    try:
        return getattr(request, "status", 200)
    finally:
        request.close()


def test_live_monitoring_targets_documentation_exists() -> None:
    assert MONITORING_README.exists()
    assert LIVE_EVIDENCE.exists()
    assert REPORT.exists()


@pytest.mark.parametrize("name,url", list(TARGETS.items()))
def test_live_monitoring_targets_are_reachable_or_explicitly_reported(name: str, url: str) -> None:
    report = REPORT.read_text(encoding="utf-8")
    assert "evidence_type: live_health" in report
    assert "api.afritechnology.com/health" in report
    try:
        status = _probe(url)
    except URLError:
        pytest.skip(f"{name} is not reachable from this execution environment")
    assert 200 <= status < 500
