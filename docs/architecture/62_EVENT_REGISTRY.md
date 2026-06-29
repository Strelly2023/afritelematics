# NovaRide Event Registry

Status: CANONICAL SCHEMA REGISTRY
Classification: EVENT VERSION AUTHORITY

Purpose: define the registry that maps event types to schema versions,
ownership, compatibility mode, and lifecycle status.

## Registry Rule

```text
No event type is valid unless it is present in the registry.
No schema version is valid unless it is attached to a registry entry.
No consumer may assume a schema without reading the registry.
```

## Registry Record Shape

```json
{
  "event_type": "trip.completed.v1",
  "domain": "trip",
  "owner_service": "trip-service",
  "schema_version": 1,
  "payload_format": "json",
  "compatibility": "backward",
  "status": "active",
  "partition_key_strategy": "aggregate_id",
  "idempotency_strategy": "aggregate_and_event_type",
  "visibility": "tenant",
  "decision_trace_required": true,
  "schema_ref": {
    "document_id": "61_EVENT_ENVELOPE_SCHEMA.md",
    "payload_document_id": "60_EVENT_SCHEMA_SYSTEM.md",
    "registry_revision": "1.0.0"
  }
}
```

## Registry Entries

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

## Lifecycle States

- `draft`
- `active`
- `deprecated`
- `retired`

## Registry Ownership

The registry is owned by the platform governance layer. Execution services may
read it. Execution services may not mutate it.

