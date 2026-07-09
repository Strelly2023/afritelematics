from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OTEL = ROOT / "deploy/production/monitoring/opentelemetry/otel-collector.yml"
MIDDLEWARE = ROOT / "afritech/middleware/request_logging.py"


def test_opentelemetry_configuration_and_trace_correlation_exist() -> None:
    assert OTEL.exists()
    text = OTEL.read_text(encoding="utf-8")
    for item in ("receivers:", "otlp:", "processors:", "exporters:", "traces:", "metrics:"):
        assert item in text

    middleware = MIDDLEWARE.read_text(encoding="utf-8")
    for item in ("trace_id", "span_id", "parent_span_id", "traceparent", "X-Trace-Id", "X-Span-Id"):
        assert item in middleware
