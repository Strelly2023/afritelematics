# NovaRide Architecture Compliance Metrics Stack

## Purpose

This runbook defines the monitoring surface for NovaRide architecture
compliance. The stack exposes validator results as Prometheus metrics and makes
them visible in Grafana without giving monitoring systems execution authority.

## Metrics Endpoint

Prometheus-compatible metrics are exposed at:

```text
/metrics/architecture/compliance
```

The endpoint reports:

- `novaride_compliance_score`
- `novaride_compliance_rules_total`
- `novaride_compliance_rules_passed`
- `novaride_compliance_rules_failed`
- `novaride_compliance_rule_passed{rule="..."}`
- `novaride_compliance_rule_issues{rule="..."}`
- `novaride_compliance_report_info{mode="...",status="..."}`

The endpoint uses the current compliance report artifact when available and
falls back to configured control status when no artifact exists.

## Prometheus

Configuration files:

- `deploy/novaride/monitoring/prometheus.yml`
- `deploy/novaride/monitoring/architecture_compliance_rules.yml`

Required scrape configuration:

```yaml
scrape_configs:
  - job_name: novaride-architecture-compliance
    metrics_path: /metrics/architecture/compliance
    static_configs:
      - targets:
          - afritech-api:8000
```

## Alerts

Alerts are defined for:

- any failed compliance rule
- compliance score below 100
- semantic OpenAPI diff failure

These alerts are advisory. NovaPower and the CI validator remain the execution
authority for deployment blocking.

## Grafana

Dashboard file:

```text
deploy/novaride/monitoring/grafana-dashboard.json
```

Panels:

- Architecture Compliance Score
- Failed Rules
- Semantic OpenAPI Diff
- Per-Rule Pass Status

## Verification

Run:

```bash
python -m architecture_validator.cli --format json --output compliance_report.json
```

Then verify:

```bash
curl http://localhost:8000/metrics/architecture/compliance
```

Expected result:

```text
novaride_compliance_score 100
novaride_compliance_rules_failed 0
```
