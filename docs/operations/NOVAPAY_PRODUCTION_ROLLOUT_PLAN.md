# NovaPay production rollout plan

This document defines the deployment shape for NovaPay as a protocol + rails + apps stack.

It complements the existing NovaTech core platform docs and is intended to be the
operational handoff for an Australia-to-Africa corridor launch.

## 1. System architecture

NovaPay is split into four deployment layers:

1. Client surfaces
   - Passenger app
   - Driver app
   - Operator app
   - Web trust explorer / admin tools

2. API and protocol layer
   - Auth gateway
   - Transfer quote API
   - Transfer execution API
   - Receipt verification API
   - Proof / trust APIs

3. Settlement and compliance layer
   - Quote validator
   - Transfer orchestrator
   - Provider router
   - Compliance screening
   - Ledger / receipt store
   - Reconciliation jobs

4. Rails and observability layer
   - PayID / bank rails
   - Mobile money adapters
   - FX / payout adapters
   - Metrics / logs / traces / alerting

### Runtime diagram

```text
Mobile / Web Apps
    |
    v
API Gateway / JWT Auth
    |
    +--> Quote Service -----> Canonical Hash / Quote Store
    |
    +--> Execute Service ----> Quote Validator
    |                          |
    |                          +--> Compliance Screen
    |                          |
    |                          +--> Provider Router
    |                          |
    |                          +--> Settlement Engine
    |                          |
    |                          +--> Receipt / Audit Ledger
    |
    +--> Verify Service -----> Receipt / Proof Verification
    |
    +--> Explorer / Ops UI ---> Search / Audit / Reconciliation
```

## 2. Service topology

| Service | Responsibility | Notes |
| --- | --- | --- |
| `novapay-api` | REST entry point | Stateless, behind WAF / LB |
| `novapay-auth` | JWT validation | Device-bound, role-aware |
| `novapay-transfer-orchestrator` | Quote, execute, verify | Canonicalization + hash enforcement |
| `novapay-settlement-router` | Route to rails | PayID, mobile money, bank deposit |
| `novapay-compliance` | KYC / AML / sanctions | Screening + limits + escalation |
| `novapay-ledger` | Immutable receipts | Audit trail, replayable |
| `novapay-reconciliation` | Batch settlement and drift checks | Scheduled jobs |
| `novapay-explorer` | Public and operator visibility | Read-only trust views |

## 3. Boundary policy

The API boundary is strict:

- no float values are accepted on transfer or execution payloads
- numeric fields are accepted as strings, integers, or Decimals only
- nested floats are rejected before model coercion
- quote execution only accepts validated canonical quotes
- provider override is rejected unless it matches the validated route hint

This is enforced in code by the transfer payload validators and the immutable
execution context.

## 4. Corridor configuration

Initial corridor scope:

| Corridor | Status | Primary rails | Payout patterns |
| --- | --- | --- | --- |
| Australia → Kenya | Launch corridor | PayID + mobile money | Bank deposit, mobile money |
| Australia → Burundi | Pilot corridor | Bank + payout partner | Bank deposit, cash pickup |
| Australia → Democratic Republic of Congo | Pilot corridor | Bank + mobile money | Mobile money, cash pickup |
| Australia → USA | Limited corridor | Bank / domestic transfer | Bank deposit |
| USA → Kenya | Expansion corridor | Bank + mobile money | Bank deposit, mobile money |
| USA → Burundi / DRC | Expansion corridor | Bank + partner payout | Bank deposit, cash pickup |
| Kenya → Australia | Return corridor | Mobile money + bank | Bank deposit |
| Burundi / DRC → Australia | Return corridor | Partner payout + bank | Bank deposit |

The launch order should be:

1. Australia → Kenya
2. Australia → Burundi
3. Australia → DRC
4. USA → Kenya
5. Return corridors after liquidity stabilizes

## 5. Compliance wiring

Compliance is embedded at execution time and after execution.

### Pre-execution checks

- identity / authentication validity
- recipient and sender screening
- sanctions list screening
- transfer amount thresholds
- corridor-specific policy rules
- provider eligibility

### Execution-time checks

- route validation
- provider lock
- amount / limit validation
- risk score escalation
- approval requirements for high-value flows

### Post-execution checks

- receipt immutability
- settlement confirmation
- reconciliation mismatch detection
- audit export
- anomaly review queue

### KYC / AML hooks

- KYC status required for live rails
- beneficial ownership capture for business accounts
- politically exposed person checks
- sanctions / watchlist screening
- structuring / velocity detection

## 6. Settlement state machine

```text
quoted
  -> validated
  -> compliance_screening
  -> provider_locked
  -> pending_settlement
  -> settled
  -> receipt_published
  -> reconciled
  -> closed

Failure paths:
  quoted -> rejected
  validated -> rejected
  compliance_screening -> escalated
  pending_settlement -> retrying
  pending_settlement -> failed
  failed -> manual_review
```

Rules:

- a quote cannot be executed without canonical hash validation
- a validated provider cannot be changed later
- a receipt hash must be stable across replay
- reconciliation must compare canonical quote, settlement, and receipt records

## 7. Rollout plan

### Phase 0 — internal hardening

- complete transfer and settlement test coverage
- run replay and tamper tests in CI
- verify all corridor adapters in sandbox mode
- confirm immutable execution context checks

### Phase 1 — restricted canary

- 1% traffic on Australia → Kenya
- low-value transfers only
- operator approval required for live settlement
- manual reconciliation daily

### Phase 2 — corridor expansion

- increase to 5%, 25%, then 50%
- add Burundi and DRC pilots
- enable automated reconciliation
- enable compliance escalation queue

### Phase 3 — multi-corridor production

- activate USA ↔ Africa corridors
- automate settlement and ledger export
- publish public trust explorer read views
- tighten fraud thresholds and velocity caps

### Phase 4 — stable operating mode

- 100% traffic for approved corridors
- continuous monitoring
- periodic corridor re-certification
- quarterly compliance and control review

## 8. Infra baseline

Recommended deployment components:

- API ingress: load balancer + WAF
- app compute: container service or Kubernetes
- datastore: PostgreSQL
- cache: Redis
- queue: SQS / managed queue
- secrets: cloud secrets manager
- key management: KMS / HSM-backed keys
- object storage: receipts, exports, evidence
- observability: logs, metrics, traces, alerting
- CI/CD: build, test, parity checks, deployment gate

## 9. Operational controls

- deploy with canary and automatic rollback on verification drift
- freeze quote and receipt schemas after each release tag
- keep deterministic corpus snapshots in CI
- require explicit approval for corridor expansion
- maintain read-only public explorer for external verification

## 10. Readiness gate

NovaPay is production-ready for a corridor only if all are true:

- quote hash parity passes
- execution context is immutable
- provider override rejection passes
- float rejection passes at API boundary
- settlement adapter is live in sandbox and production
- compliance screen is wired and tested
- reconciliation reports zero unexplained drift

