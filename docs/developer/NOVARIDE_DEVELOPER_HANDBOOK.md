# NovaRide Developer Handbook

Status: DEVELOPER OPERATING GUIDE
Classification: ENGINEERING WORKFLOW SURFACE

Purpose: explain how to change NovaRide safely.

## Basic Rule

```text
Do not add behavior in the app layer that belongs to the platform layer.
```

## How To Add A Command

1. define the command intent
2. assign the owning service
3. define the policy check
4. define the idempotency key
5. define the emitted events
6. define failure behavior
7. write contract tests
8. write replay tests

## How To Add An Event

1. register the event type
2. define the envelope and payload
3. assign the partition key
4. define compatibility mode
5. define who owns the event
6. define consumers
7. add schema tests
8. add replay tests

## How To Add A Workflow

1. identify the business process
2. identify control-plane gates
3. identify compensation steps
4. define workflow state transitions
5. bind workflow steps to events
6. test rollback and retry

## How To Add A Projection

1. define the read use case
2. define the source events
3. define rebuild behavior
4. define freshness expectations
5. define tenant scope
6. define cache invalidation behavior

## How To Certify A Schema

1. register the schema
2. validate compatibility
3. validate envelope compliance
4. validate tenant scoping
5. validate replay safety
6. publish the registry revision

## How To Migrate A Contract

1. add the new version
2. preserve the old version
3. update consumers
4. run compatibility tests
5. gate rollout with flags
6. deprecate only after consumers migrate

## Local Developer Expectations

- use the canonical docs tree
- preserve tenant isolation
- keep side effects idempotent
- do not bypass policy services
- do not call providers directly from UI code
- keep tests near the changed boundary

