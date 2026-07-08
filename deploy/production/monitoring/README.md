# Monitoring Foundation

This directory defines the public-pilot monitoring baseline for AfriTechnology.

## Planned Stack

- Prometheus for metrics collection
- Grafana for dashboards
- Exporters for API, NGINX, and host metrics when deployed

## What to Observe

- API latency
- request count
- error rate
- container health
- host metrics
- TLS certificate expiry

## Current Targets

- `afritech-api:8000`
- `nginx` exporter when introduced later
- `node_exporter` when introduced later

## Notes

- The Prometheus and Grafana services are intentionally profile-gated in compose.
- Health endpoints and Docker health checks provide the first-line operational probe surface.
- Structured request logs should carry request_id, client_ip, duration, status, method, and path.
