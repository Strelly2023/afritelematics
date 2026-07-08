# AFRITECH Public Pilot Health Monitoring

## Health Surfaces

- `/health`
- `/live`
- `/ready`
- `/healthz`

## Container Probes

- FastAPI health checks should use `/health`
- Dashboard health checks should use the app root on port `4173`
- NGINX health checks should use `/healthz`

## Monitoring Baseline

- Prometheus for scrape-based metrics
- Grafana for dashboarding
- Structured JSON request logs for request tracing
- Alerting for error rate, latency, and container health degradation

## Operational Notes

- `/health` is the basic container probe.
- `/live` is liveness only and should stay dependency-free.
- `/ready` must fail when configuration or database checks fail.
- `/healthz` is the ingress-level probe for NGINX.

## Evidence Expectations

- Request logs should include timestamp, service, environment, level, method, path, status_code, duration_ms, request_id, and client_ip.
- structured JSON request logs should be the default request evidence format.
- Health probe failures should be actionable and low-noise.
