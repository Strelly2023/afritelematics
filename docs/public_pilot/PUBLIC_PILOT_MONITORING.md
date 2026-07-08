# Public Pilot Monitoring

## Signals

- Application health.
- Payment failures and reconciliation drift.
- Identity verification latency and manual review queues.
- Ride request acceptance and trip integrity.
- Support tickets and incident escalation.

## Telemetry

- Sentry or equivalent error tracking is required.
- OpenTelemetry or equivalent tracing is required.
- Audit logs must include actor, role, device, action, result, timestamp, and environment.
