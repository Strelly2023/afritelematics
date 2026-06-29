# NovaRide Event Idempotency Rules

Status: CANONICAL DEDUPLICATION POLICY
Classification: DUPLICATION PREVENTION SURFACE

## Goal

Prevent duplicate side effects during retries, replays, and delivery failures.

## Idempotency Requirements

- every command path must have an idempotency key
- every event producer must persist dedupe metadata
- every execution service must reject duplicate side effects
- every payment action must be idempotent

## Recommended Key Composition

```text
<tenant_id>:<aggregate_id>:<event_type>:<command_id>
```

## Storage Rules

- idempotency keys must be scoped by tenant
- used keys must be retained long enough for retry windows and recovery
- consumed keys must not be reused for a different semantic action

## Replay Rule

Replayed events must not trigger duplicate external provider calls.

