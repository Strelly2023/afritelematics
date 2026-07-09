# Monitoring Foundation

This directory contains the production-observability stack for AfriTechnology.

## Components

- Prometheus: `deploy/production/monitoring/prometheus/`
- Alertmanager: `deploy/production/monitoring/alertmanager/`
- Grafana: `deploy/production/monitoring/grafana/`
- OpenTelemetry collector: `deploy/production/monitoring/opentelemetry/`

## Coverage

- API latency
- request count
- error rate
- container health
- host metrics
- TLS certificate expiry
- platform dashboards for NovaRide, NovaPay, and NovaID

## Notes

- Monitoring services are profile-gated and disabled by default.
- Structured request logs carry request_id and trace correlation fields.
- `/health`, `/live`, `/ready`, and `/healthz` remain the health surfaces for operational checks.
