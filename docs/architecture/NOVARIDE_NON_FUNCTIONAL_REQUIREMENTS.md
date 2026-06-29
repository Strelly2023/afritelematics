# NovaRide Non-Functional Requirements

Status: PLATFORM QUALITY BASELINE
Classification: OPERATIONAL REQUIREMENTS SURFACE

Purpose: define the measurable operational quality requirements for NovaRide.

## Requirement Classes

### Availability

- Core platform target: 99.9% for non-deployment windows
- Control plane target: 99.95% for read operations
- Execution plane target: 99.9% for bounded execution flows
- Public verification target: 99.9%

### Latency

- auth and tenant resolution: p95 < 250ms
- policy evaluation: p95 < 150ms
- flag evaluation: p95 < 100ms
- dispatch decision: p95 < 500ms
- ride state transition write: p95 < 300ms
- payment capture path: p95 < 800ms excluding external provider latency

### Throughput

- platform must support bursty ride request traffic
- control-plane read surfaces must scale independently from execution services
- event ingestion must scale without blocking user-facing writes

### Consistency

- tenant identity must be consistent across all surfaces
- event ordering must be deterministic per aggregate
- wallet and payment updates must be strongly consistent within their ledgers

### Durability

- authoritative records must survive instance failure
- event history must be replayable after restore
- audit and proof data must retain integrity across backups

### Recovery

- RPO for core operational data: defined per environment but never unbounded
- RTO for controlled-pilot environments: bounded and documented
- DR steps must restore control plane before enabling execution plane

### Security

- all tenant-scoped requests authenticated
- all control-plane actions authorized
- all high-risk actions approved when required
- all secrets managed outside source control

### Governance

- every executed action must be auditable
- every governed action must have a decision trace
- every schema change must be versioned
- every rollout must be explainable

### Observability

- logs
- metrics
- traces
- structured audit events
- replay evidence

### Data Freshness

- dashboard projections may lag authoritative events but must declare freshness
- public verification results must reference their source timestamp
- stale projections may not override authoritative state

## SLO Baseline

| Surface | SLO |
| --- | --- |
| Rider booking | high availability and low latency |
| Driver acceptance | bounded response time |
| Operator live map | near-real-time refresh |
| Control-plane decisions | deterministic and explainable |
| Public verification | fast and read-only |

## Do Not Accept

- unbounded retries without idempotency
- hidden state mutation
- control decisions without trace
- direct provider calls from apps
- orphan events without tenant scope

