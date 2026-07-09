# PRR Tracing Evidence

This document records the tracing evidence used for PRR readiness.

## Required Fields

- request_id generated
- trace_id generated
- span_id generated
- traceparent propagated
- response headers include X-Request-ID
- response headers include X-Trace-Id
- response headers include X-Span-Id
- OpenTelemetry collector config present
- traces pipeline present
- metrics pipeline present

## Implementation Sources

- `afritech/middleware/request_logging.py`
- `deploy/production/monitoring/opentelemetry/otel-collector.yml`

## Notes

Structured request logging preserves correlation identifiers across API responses and logs.
