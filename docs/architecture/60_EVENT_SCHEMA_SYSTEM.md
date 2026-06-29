# NovaRide Event Schema System

Status: CANONICAL EVENT CONTRACT SYSTEM
Classification: PLATFORM MEMORY AND REPLAY SURFACE

Purpose: define the authoritative event model for NovaRide. Every meaningful
state change in the platform must be represented as a versioned, tenant-scoped,
append-only event.

## System Rule

```text
If it changes platform truth, it must emit an event.
If it emits an event, it must be schema-bound.
If it is schema-bound, it must be registry-resolved.
If it is registry-resolved, it must be compatibility-checked.
```

## Event Model Layers

### 1. Envelope

The outer transport contract. It is stable across domains.

### 2. Domain Payload

The business data for a specific event type.

### 3. Decision Trace

The control-plane metadata that explains why the event was allowed.

### 4. Registry Metadata

The versioned schema reference and compatibility information.

## Authoritative Event Families

### Identity and tenancy

- `organization.created.v1`
- `organization.updated.v1`
- `account.created.v1`
- `account.role_assigned.v1`
- `subscription.activated.v1`
- `feature_flag.evaluated.v1`

### Mobility lifecycle

- `ride.requested.v1`
- `ride.matched.v1`
- `ride.accepted.v1`
- `ride.arriving.v1`
- `ride.arrived.v1`
- `trip.started.v1`
- `trip.completed.v1`
- `trip.cancelled.v1`

### Dispatch and driver state

- `driver.presence.updated.v1`
- `dispatch.assignment_created.v1`
- `dispatch.assignment_released.v1`

### Payments and ledger

- `payment.authorized.v1`
- `payment.captured.v1`
- `payment.failed.v1`
- `wallet.debited.v1`
- `wallet.credited.v1`
- `transaction.recorded.v1`

### Trust and compliance

- `policy.decision_recorded.v1`
- `approval.requested.v1`
- `approval.granted.v1`
- `approval.rejected.v1`
- `trust.score_updated.v1`
- `compliance.decision_recorded.v1`
- `inspection.completed.v1`

### Support and disputes

- `support.ticket_created.v1`
- `support.dispute_opened.v1`
- `support.refund_requested.v1`
- `support.refund_processed.v1`

### Verification and evidence

- `receipt.issued.v1`
- `receipt.verified.v1`
- `public.verification.completed.v1`
- `audit.recorded.v1`

## Design Constraints

- every event has a tenant identifier
- every event has a stable schema version
- every event has a correlation identifier
- every event has a causation chain
- every event is immutable after write
- every event can be replayed
- every event can be traced to a decision or approval when applicable

## Canonical Event Shapes

The platform uses a shared envelope and domain-specific payloads.

### Shared envelope fields

- `event_id`
- `event_type`
- `schema_version`
- `occurred_at`
- `recorded_at`
- `tenant_id`
- `organization_id`
- `subject`
- `actor`
- `resource`
- `correlation_id`
- `causation_id`
- `idempotency_key`
- `sequence`
- `partition_key`
- `source`
- `visibility`
- `decision_trace`
- `payload`

### Payload rule

Payloads must contain only domain data for the event type. They must not store
control-plane decisions unless the event is itself a decision event.

## Deep Schema Design Example

### `trip.completed.v1`

```json
{
  "event_id": "uuid",
  "event_type": "trip.completed.v1",
  "schema_version": 1,
  "occurred_at": "2026-06-29T05:00:00Z",
  "recorded_at": "2026-06-29T05:00:01Z",
  "tenant_id": "org_123",
  "organization_id": "org_123",
  "subject": {
    "type": "trip",
    "id": "trip_456"
  },
  "actor": {
    "type": "driver",
    "id": "driver_789",
    "role": "DRIVER"
  },
  "resource": {
    "type": "ride",
    "id": "ride_456"
  },
  "correlation_id": "corr_abc",
  "causation_id": "evt_trip_started_123",
  "idempotency_key": "trip.completed:trip_456",
  "sequence": 18,
  "partition_key": "trip_456",
  "source": "trip-service",
  "visibility": "tenant",
  "decision_trace": {
    "policy_id": "policy.trip.complete.v3",
    "policy_version": "2026.06",
    "approval_id": null,
    "flag_evaluation": {
      "phase13.execution.enabled": false
    }
  },
  "payload": {
    "ride_id": "ride_456",
    "trip_id": "trip_456",
    "driver_id": "driver_789",
    "passenger_id": "pass_222",
    "final_fare": "24.60",
    "currency": "AUD",
    "distance_meters": 8230,
    "duration_seconds": 1140,
    "route_distance_meters": 8400,
    "route_duration_seconds": 1200,
    "status": "completed"
  }
}
```

### `payment.captured.v1`

```json
{
  "event_id": "uuid",
  "event_type": "payment.captured.v1",
  "schema_version": 1,
  "occurred_at": "2026-06-29T05:00:02Z",
  "recorded_at": "2026-06-29T05:00:02Z",
  "tenant_id": "org_123",
  "organization_id": "org_123",
  "subject": {
    "type": "payment",
    "id": "pay_123"
  },
  "actor": {
    "type": "system",
    "id": "novapay",
    "role": "SYSTEM"
  },
  "resource": {
    "type": "ride",
    "id": "ride_456"
  },
  "correlation_id": "corr_abc",
  "causation_id": "evt_trip_completed_999",
  "idempotency_key": "payment.captured:pay_123",
  "sequence": 19,
  "partition_key": "payment_ride_456",
  "source": "novapay-service",
  "visibility": "tenant",
  "decision_trace": {
    "policy_id": "policy.payment.capture.v2",
    "policy_version": "2026.06",
    "approval_id": null,
    "flag_evaluation": {}
  },
  "payload": {
    "payment_id": "pay_123",
    "ride_id": "ride_456",
    "amount": "24.60",
    "currency": "AUD",
    "provider": "stripe",
    "provider_capture_id": "pi_abc",
    "status": "captured"
  }
}
```

## Required Event Domains

### Control-plane events

- policy decisions
- flag evaluations
- approval records

### Execution events

- ride lifecycle
- driver presence
- dispatch assignment
- payments
- wallet updates

### Evidence events

- audit records
- receipt issuance
- public verification
- replay outcomes

## Schema Ownership

Each event family has a single owning service. No other service may redefine
the schema without a version bump and registry entry.

## Minimum Guarantees

- deterministic serialization
- stable field ordering for signature computation
- explicit null handling
- tenant keys on every event
- replay-safe domain payloads

