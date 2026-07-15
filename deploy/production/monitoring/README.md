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

## OpenTelemetry pipeline

Production FastAPI exports OTLP/HTTP traces to `http://otel-collector:4318`.
The collector accepts:

- OTLP/gRPC on `4317`
- OTLP/HTTP on `4318`
- health checks on `13133`
- Prometheus collector metrics on `9464`

Prometheus scrapes `otel-collector:9464`, and Grafana is provisioned with the
in-cluster Prometheus datasource at `http://prometheus:9090`.

Bring up the monitoring profile:

```bash
docker compose \
  -f deploy/production/docker-compose.trust-node.yml \
  --profile monitoring up -d
```

Verify the pipeline:

```bash
curl -fsS http://127.0.0.1:13133/
curl -fsS https://api.afritechnology.com/health
docker compose -f deploy/production/docker-compose.trust-node.yml logs --tail=120 otel-collector
```

Prometheus targets should include:

- `afritech-api`
- `otel-collector`
- `nginx-exporter`
- `node-exporter`
- `postgres-exporter`
- `cadvisor`

Operational verification should collect evidence, not approvals:

```bash
python3 scripts/novacodepro/run_operational_verification_v1.py \
  --environment production \
  --release 2026.1.1 \
  --base-url https://novacodepro.afritechnology.com \
  --api-url https://api.afritechnology.com \
  --evidence-dir reports/novacodepro/operational-verification
```

PRR approval, executive approval, GA authorization, and real-payment activation
remain separate governance decisions.
