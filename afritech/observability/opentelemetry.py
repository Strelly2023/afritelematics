"""Optional OpenTelemetry wiring for the FastAPI production surface."""

from __future__ import annotations

import os
from typing import Any


def configure_fastapi_observability(app: Any) -> dict[str, Any]:
    """Instrument FastAPI when OpenTelemetry dependencies are available.

    The production image installs the OTel packages. Local development and tests
    may run without them, so missing packages are reported instead of failing
    application startup.
    """

    enabled = _enabled()
    service_name = os.environ.get("OTEL_SERVICE_NAME", "afritech-api")
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    status: dict[str, Any] = {
        "enabled": enabled,
        "service_name": service_name,
        "endpoint_configured": bool(endpoint),
        "instrumented": False,
        "reason": "disabled",
    }
    app.state.opentelemetry = status
    if not enabled:
        return status

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.logging import LoggingInstrumentor
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except Exception as exc:  # pragma: no cover - depends on optional packages.
        status["reason"] = f"otel_dependency_unavailable:{exc.__class__.__name__}"
        return status

    if not endpoint:
        status["reason"] = "missing_otel_exporter_otlp_endpoint"
        return status

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": os.environ.get("AFRITECH_VERSION", "0.7.0"),
            "deployment.environment": os.environ.get(
                "AFRITECH_RUNTIME_ENVIRONMENT",
                os.environ.get("AFRITECH_ENV", "production"),
            ),
            "service.namespace": os.environ.get("OTEL_SERVICE_NAMESPACE", "afritech"),
        }
    )
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=_http_trace_endpoint(endpoint))
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
    RequestsInstrumentor().instrument()
    LoggingInstrumentor().instrument(set_logging_format=False)

    status.update({"instrumented": True, "reason": "instrumented"})
    app.state.opentelemetry = status
    return status


def _enabled() -> bool:
    value = os.environ.get("AFRITECH_OTEL_ENABLED", os.environ.get("OTEL_SDK_ENABLED", "true"))
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _http_trace_endpoint(endpoint: str) -> str:
    normalized = endpoint.rstrip("/")
    if normalized.endswith("/v1/traces"):
        return normalized
    return f"{normalized}/v1/traces"
