# NovaRide Event Compatibility Rules

Status: CANONICAL COMPATIBILITY POLICY
Classification: SCHEMA EVOLUTION RULESET

## Compatibility Philosophy

Schema evolution must never silently break consumers, replay, or trust
verification.

## Compatibility Modes

### Backward compatible

New schema can read old events.

Allowed changes:

- add optional fields
- add new enum values only when consumers tolerate them
- widen numeric precision
- add new payload objects

### Forward compatible

Old consumers can ignore new fields.

Allowed changes:

- add optional fields
- add metadata-only fields

### Full compatible

Both backward and forward compatible.

### Breaking change

Requires a new semantic event type or major schema revision.

## Breaking Changes

The following require a new event version:

- removing a required field
- renaming a field
- changing field type incompatibly
- changing semantics without a version bump
- changing idempotency or partition strategy
- changing visibility from tenant to public or restricted
- removing decision trace from events that require it

## Allowed Changes Without Breaking

- adding optional fields with defaults
- adding new top-level metadata
- tightening validation on new fields only
- adding new event types alongside old ones

## Versioning Rules

- semantic event types must include version suffix
- payload schema version increments must be explicit
- registry revision increments whenever compatibility metadata changes
- consumers must declare supported event versions

## Consumer Behavior

Consumers must:

- ignore unknown optional fields
- reject unsupported major versions
- verify registry and schema ref before processing
- preserve idempotency on retries

## Producer Behavior

Producers must:

- emit only registered event types
- attach a valid tenant id
- attach a valid correlation id
- attach the decision trace when required
- never repurpose a versioned event type

## Replay Compatibility Rule

If an event cannot be replayed from archived registry state, it is not valid for
production history.

