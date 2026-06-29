# NovaRide Service Catalog

Status: CANONICAL SERVICE INVENTORY
Classification: PLATFORM OPERATING MODEL

Purpose: document the owned services, responsibilities, contracts, and event
surfaces of NovaRide.

## Catalog Entries

### NovaID

- responsibility: authentication, identity, roles, tenant membership
- owns: user identity, account mapping, access claims
- emits: account.created.v1, account.role_assigned.v1

### NovaPay

- responsibility: wallets, authorizations, captures, refunds, payouts
- owns: payment lifecycle and ledger updates
- emits: payment.authorized.v1, payment.captured.v1, wallet.debited.v1, wallet.credited.v1

### Dispatch Engine

- responsibility: allocate drivers to rides
- owns: assignment decisions and dispatch state
- emits: ride.matched.v1, dispatch.assignment_created.v1

### Trip Service

- responsibility: ride lifecycle state transitions
- owns: trip state and ride progression
- emits: trip.started.v1, trip.completed.v1, trip.cancelled.v1

### Pricing Engine

- responsibility: fare calculation, surge, promotions
- owns: pricing decisions and estimates
- emits: policy.decision_recorded.v1 when decisions are governed

### Driver Service

- responsibility: driver presence, availability, acceptance
- owns: driver status
- emits: driver.presence.updated.v1, ride.accepted.v1

### Fleet Service

- responsibility: fleet ownership, vehicle assignment, utilization
- owns: fleet records
- emits: inspection.completed.v1 when tied to compliance workflows

### Support Service

- responsibility: tickets, disputes, refund requests, case handling
- owns: support workflows
- emits: support.ticket_created.v1, support.refund_requested.v1

### Notification Service

- responsibility: push, email, SMS, operational alerts
- owns: outbound notification queue
- emits: notification delivery records

### Maps and Routing Service

- responsibility: ETA, route projection, pickup precision
- owns: routing projections
- emits: routing state updates when needed

### Policy Engine

- responsibility: deterministic rule evaluation
- owns: policy decisions and explanations
- emits: policy.decision_recorded.v1

### Feature Flag Service

- responsibility: rollout control and runtime gating
- owns: flag evaluations
- emits: feature_flag.evaluated.v1

### Approval Service

- responsibility: human approvals and exceptions
- owns: approvals
- emits: approval.requested.v1, approval.granted.v1, approval.rejected.v1

### Workflow Orchestrator

- responsibility: multi-step governed business flows
- owns: workflow instances and transitions
- emits: workflow step events

### Trust Engine

- responsibility: trust scoring and anomaly detection
- owns: trust projections
- emits: trust.score_updated.v1

### Compliance Engine

- responsibility: compliance gating and evidence assessment
- owns: compliance decisions
- emits: compliance.decision_recorded.v1

## Service Contract Rules

- every service declares owned aggregates
- every service declares produced and consumed events
- every service declares its failure mode
- every service declares its tenant isolation behavior
- every service declares its idempotency strategy

