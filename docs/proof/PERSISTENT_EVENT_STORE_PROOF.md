# Persistent Event Store Proof

## Document Classification

```text
STATUS: PRODUCTION PROOF GATE 4
CLASSIFICATION: PERSISTENT EVENT STORAGE EVIDENCE SURFACE
ROLE: PROVE APPEND-ONLY EVENT PERSISTENCE WITHOUT GRANTING STORAGE AUTHORITY
BOUNDARY: DATABASE STORAGE MAY PRESERVE EVENTS; REPLAY VALIDATION REMAINS AUTHORITY
```

This report documents Production Proof Gate 4.

The persistent event store proof validates that database-shaped event storage
preserves canonical event evidence across restore without becoming a truth
source.

## Required Proofs

```text
append-only writes
canonical event hash preserved
replay from database snapshot
no update/delete mutation
same result after restart
```

## Enforcement Surface

```text
afritech/storage/postgres_event_store.py
afritech/tests/storage/test_persistent_event_store.py
afritech/ci/persistent_storage_validator.py
docs/proof/PERSISTENT_EVENT_STORE_PROOF.md
```

The current store uses an in-memory deterministic backend shaped like persisted
database rows. A future PostgreSQL implementation must preserve the same
authority boundary.

Storage may preserve and restore canonical event rows.

Storage may not mutate events, update event meaning, delete event evidence, or
define replay truth.

## Current Gate

```bash
python3 -m afritech.ci.persistent_storage_validator
```

Passing this gate means persistent event storage preserves canonical event
hashes and replay-from-snapshot equivalence while rejecting update/delete
mutation.
