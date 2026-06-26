# NovaTech Observability and SRE Standard

Every production service declares owners, service tier, SLIs, SLO targets,
measurement windows, error budget, burn-rate alerts, dependency objectives,
RTO, RPO, capacity limits, runbooks, and escalation.

Required telemetry includes request rate, errors, duration, saturation,
availability, policy denials, schema failures, idempotency outcomes, evidence
production, signature failures, replay mismatch, federation health, tenant
isolation violations, and AI policy/approval outcomes where applicable.

Logs, metrics, and traces carry correlation, operation, tenant-safe, contract,
schema, and deployment identifiers. Secrets and unnecessary personal data are
prohibited. Telemetry is evidence-supporting but is not itself execution
authority. Exhausted error budgets block risky releases unless an approved
exception records owner, scope, duration, and remediation.
