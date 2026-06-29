# NovaRide Event Envelope Schema

Status: CANONICAL ENVELOPE CONTRACT
Classification: TRANSPORT AND REPLAY CONTRACT

## Envelope Purpose

The envelope wraps every event regardless of domain. It carries routing,
tenancy, causality, decision trace, and registry metadata.

## Envelope Schema

```json
{
  "event_id": "string",
  "event_type": "string",
  "schema_version": 1,
  "occurred_at": "RFC3339 timestamp",
  "recorded_at": "RFC3339 timestamp",
  "tenant_id": "string",
  "organization_id": "string",
  "subject": {
    "type": "string",
    "id": "string"
  },
  "actor": {
    "type": "string",
    "id": "string",
    "role": "string"
  },
  "resource": {
    "type": "string",
    "id": "string"
  },
  "correlation_id": "string",
  "causation_id": "string",
  "idempotency_key": "string",
  "sequence": 1,
  "partition_key": "string",
  "source": "string",
  "visibility": "tenant|public|internal|restricted",
  "decision_trace": {
    "policy_id": "string",
    "policy_version": "string",
    "approval_id": "string|null",
    "flag_evaluation": {}
  },
  "schema_ref": {
    "registry_id": "string",
    "document_id": "string",
    "revision": "string"
  },
  "payload": {}
}
```

## Field Semantics

### `event_id`

Globally unique identifier for the event.

### `event_type`

Canonical name including semantic version, for example
`trip.completed.v1`.

### `schema_version`

Integer schema revision for the payload family.

### `tenant_id` and `organization_id`

Tenant scope for all platform truth. These must match.

### `subject`

The primary business object the event is about.

### `actor`

The principal that caused or authorized the event.

### `resource`

The object affected by the event if different from the subject.

### `correlation_id`

Groups events across a single user action or workflow.

### `causation_id`

References the direct parent event or triggering command.

### `idempotency_key`

Deduplication key for replay, retries, and delivery reprocessing.

### `sequence`

Monotonic sequence within the partition or aggregate scope.

### `partition_key`

Stable partitioning key. Usually the aggregate identifier.

### `source`

Owning service or boundary that emitted the event.

### `visibility`

- `tenant`: visible within tenant scope
- `public`: safe for public verification surfaces
- `internal`: internal-only projections
- `restricted`: governance- or security-sensitive

### `decision_trace`

Links the event back to policy evaluation, approval, and flag state.

### `schema_ref`

Registry pointer to the exact schema artifact.

## Canonical Serialization Rules

- UTF-8 JSON
- deterministic field ordering
- no duplicate keys
- explicit timestamps
- no binary payload in envelope
- payload must be JSON serializable

## Replay Requirement

If the envelope cannot reconstruct the original decision and state transition,
it is invalid.

