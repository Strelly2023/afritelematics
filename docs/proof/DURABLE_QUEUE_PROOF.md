# Durable Queue Proof

## Document Classification

```text
STATUS: PRODUCTION PROOF GATE 3
CLASSIFICATION: DURABLE DELIVERY EVIDENCE SURFACE
ROLE: PROVE DURABLE QUEUE DELIVERY WITHOUT GRANTING STORAGE AUTHORITY
BOUNDARY: REDIS/POSTGRES MAY DELIVER WORK; REPLAY LOG REMAINS AUTHORITY
```

This report documents Production Proof Gate 3.

The durable queue proof gate validates that durable delivery storage can persist
and restore canonical queue records without becoming a truth source.

## Core Law

```text
Redis/Postgres may deliver work.
Redis/Postgres must never define truth.
Replay log remains authority.
```

## Required Proofs

```text
durable rows preserve canonical record hashes
restart restore preserves delivery hash
tampered durable rows are rejected
duplicate durable delivery is rejected
authority disclaimer is stored with durable rows
```

## Enforcement Surface

```text
afritech/execution/queue/durable_queue.py
afritech/tests/queue/test_durable_queue_replay.py
afritech/ci/durable_queue_validator.py
docs/proof/DURABLE_QUEUE_PROOF.md
```

The current adapter uses an in-memory deterministic backend to model the
authority boundary that Redis/Postgres-backed adapters must preserve.

Storage may persist and deliver canonical records.

Storage may not define replay truth, mutate event identity, rewrite ordering, or
override replay authority.

## Current Gate

```bash
python3 -m afritech.ci.durable_queue_validator
```

Passing this gate means durable delivery preserves replay-safe canonical queue
records across restore while rejecting mutation and duplicate delivery.
