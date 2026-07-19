from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from afritech.api.app import app


ROOT = Path(__file__).resolve().parents[3]
NGINX = ROOT / "deploy/production/nginx/afritechnology-platform.conf.template"
COMPOSE = ROOT / "deploy/production/docker-compose.trust-node.yml"
PROMETHEUS = ROOT / "deploy/production/monitoring/prometheus.yml"
MONITORING_README = ROOT / "deploy/production/monitoring/README.md"
SECURITY_HARDENING = ROOT / "docs/operations/AFRITECH_PUBLIC_PILOT_SECURITY_HARDENING.md"
HEALTH_MONITORING = ROOT / "docs/operations/AFRITECH_PUBLIC_PILOT_HEALTH_MONITORING.md"
MIDDLEWARE = ROOT / "afritech/middleware/request_logging.py"


def test_fastapi_health_endpoints_are_exposed(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("AFRITECH_RUNTIME_ENVIRONMENT", "PUBLIC_PILOT")
    monkeypatch.setenv("AFRIRIDE_DB_PATH", str(tmp_path / "health.sqlite3"))

    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {
        "status": "healthy",
        "service": "afritech-api",
        "version": "0.7.0",
        "environment": "PUBLIC_PILOT",
    }

    live = client.get("/live")
    assert live.status_code == 200
    assert live.json() == {"alive": True, "service": "afritech-api"}

    ready = client.get("/ready")
    assert ready.status_code == 200
    ready_payload = ready.json()
    assert ready_payload["ready"] is True
    assert ready_payload["database"] == "up"
    assert ready_payload["configuration"] == "valid"
    assert ready_payload["disk"] == "ok"
    assert ready_payload["tls"] == "ok"
    assert ready_payload["migrations"] == "applied"
    assert ready_payload["monitoring"] == "available"


def test_fastapi_ready_endpoint_returns_503_when_configuration_invalid(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("AFRITECH_RUNTIME_ENVIRONMENT", "")
    monkeypatch.setenv("AFRIRIDE_DB_PATH", str(tmp_path / "health.sqlite3"))

    client = TestClient(app)
    ready = client.get("/ready")
    assert ready.status_code == 503
    assert ready.json()["ready"] is False


def test_fastapi_health_endpoint_emits_trace_headers_when_instrumented(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("AFRITECH_RUNTIME_ENVIRONMENT", "PUBLIC_PILOT")
    monkeypatch.setenv("AFRIRIDE_DB_PATH", str(tmp_path / "health.sqlite3"))

    client = TestClient(app)
    response = client.get(
        "/health",
        headers={
            "X-NovaRide-Event-Id": "health-trace-1",
            "X-NovaRide-Device-Id": "device-health-1",
            "X-NovaRide-Client-Timestamp": "2026-07-19T15:16:32Z",
            "X-NovaRide-App-Version": "0.1",
            "X-NovaRide-Test-Mode": "true",
        },
    )

    assert response.status_code == 200
    assert response.headers["X-NovaRide-Trace-Sequence"]
    assert response.headers["X-NovaRide-Trace-Hash"]
    assert response.headers["X-AfriRide-Trace-Sequence"]
    assert response.headers["X-AfriRide-Trace-Hash"]


def test_nginx_template_contains_healthz_probe() -> None:
    text = NGINX.read_text(encoding="utf-8")
    assert "location /healthz" in text
    for host in (
        "afritechnology.com",
        "api.afritechnology.com",
        "identity.afritechnology.com",
        "trust.afritechnology.com",
        "merchant.afritechnology.com",
        "developer.afritechnology.com",
    ):
        assert host in text


def test_docker_compose_contains_healthchecks() -> None:
    text = COMPOSE.read_text(encoding="utf-8")
    assert 'test: ["CMD", "curl", "-fsS", "http://127.0.0.1:8000/health"]' in text
    assert 'test: ["CMD", "wget", "-qO-", "http://127.0.0.1:4173/"]' in text
    assert 'test: ["CMD", "wget", "-qO-", "http://127.0.0.1/healthz"]' in text
    assert "interval: 30s" in text
    assert "timeout: 5s" in text
    assert "retries: 5" in text
    assert "start_period: 30s" in text


def test_monitoring_documents_and_prometheus_config_exist() -> None:
    assert PROMETHEUS.exists()
    assert MONITORING_README.exists()
    assert SECURITY_HARDENING.exists()
    assert HEALTH_MONITORING.exists()
    assert MIDDLEWARE.exists()

    prometheus = PROMETHEUS.read_text(encoding="utf-8")
    assert "afritech-api:8000" in prometheus
    assert "nginx" in prometheus
    assert "node_exporter" in prometheus

    monitoring = MONITORING_README.read_text(encoding="utf-8")
    assert "Prometheus" in monitoring
    assert "Grafana" in monitoring
    assert "TLS certificate expiry" in monitoring

    security = SECURITY_HARDENING.read_text(encoding="utf-8")
    assert "rate limiting" in security.lower()
    assert "fail2ban" in security.lower()
    assert "TLS certificate renewal" in security

    health = HEALTH_MONITORING.read_text(encoding="utf-8")
    for item in ("/health", "/live", "/ready", "/healthz", "structured JSON request logs"):
        assert item in health


def test_structured_logging_middleware_is_present_and_documented() -> None:
    text = MIDDLEWARE.read_text(encoding="utf-8")
    for item in (
        "JsonRequestLoggingMiddleware",
        "timestamp",
        "service",
        "environment",
        "level",
        "method",
        "path",
        "status_code",
        "duration_ms",
        "request_id",
        "client_ip",
    ):
        assert item in text
