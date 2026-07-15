from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OTEL = ROOT / "deploy/production/monitoring/opentelemetry/otel-collector.yml"
OTEL_CONFIG = ROOT / "deploy/production/monitoring/opentelemetry/config.yaml"
OTEL_PIPELINES = ROOT / "deploy/production/monitoring/opentelemetry/pipelines.yaml"
OTEL_EXPORTERS = ROOT / "deploy/production/monitoring/opentelemetry/exporters.yaml"
COMPOSE = ROOT / "deploy/production/docker-compose.trust-node.yml"
PROMETHEUS = ROOT / "deploy/production/monitoring/prometheus/prometheus.yml"
MIDDLEWARE = ROOT / "afritech/middleware/request_logging.py"
APP = ROOT / "afritech/api/app.py"
OTEL_WIRING = ROOT / "afritech/observability/opentelemetry.py"


def test_opentelemetry_configuration_and_trace_correlation_exist() -> None:
    assert OTEL.exists()
    assert OTEL_CONFIG.exists()
    assert OTEL_PIPELINES.exists()
    assert OTEL_EXPORTERS.exists()
    text = OTEL_CONFIG.read_text(encoding="utf-8")
    for item in (
        "receivers:",
        "otlp:",
        "extensions:",
        "health_check:",
        "processors:",
        "exporters:",
        "traces:",
        "metrics:",
        "logs:",
        "0.0.0.0:4317",
        "0.0.0.0:4318",
        "0.0.0.0:9464",
        "0.0.0.0:13133",
    ):
        assert item in text

    middleware = MIDDLEWARE.read_text(encoding="utf-8")
    for item in ("trace_id", "span_id", "parent_span_id", "traceparent", "X-Trace-Id", "X-Span-Id"):
        assert item in middleware


def test_fastapi_production_stack_exports_otlp_and_prometheus_scrapes_collector() -> None:
    compose = COMPOSE.read_text(encoding="utf-8")
    for item in (
        "AFRITECH_OTEL_ENABLED",
        "OTEL_SERVICE_NAME: afritech-api",
        "OTEL_EXPORTER_OTLP_ENDPOINT: http://otel-collector:4318",
        "./monitoring/opentelemetry/config.yaml:/etc/otelcol-contrib/config.yaml:ro",
        '"127.0.0.1:4317:4317"',
        '"127.0.0.1:4318:4318"',
        '"127.0.0.1:13133:13133"',
        '"9464"',
    ):
        assert item in compose

    prometheus = PROMETHEUS.read_text(encoding="utf-8")
    assert "job_name: otel-collector" in prometheus
    assert "otel-collector:9464" in prometheus


def test_fastapi_opentelemetry_instrumentation_is_optional_and_wired() -> None:
    app_text = APP.read_text(encoding="utf-8")
    assert "configure_fastapi_observability(app)" in app_text

    wiring = OTEL_WIRING.read_text(encoding="utf-8")
    for item in (
        "FastAPIInstrumentor",
        "OTLPSpanExporter",
        "RequestsInstrumentor",
        "LoggingInstrumentor",
        "otel_dependency_unavailable",
        "/v1/traces",
    ):
        assert item in wiring
