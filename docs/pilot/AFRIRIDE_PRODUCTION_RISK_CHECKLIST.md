# AfriRide Production Risk Checklist

Status: OPERATIONAL HARDENING CHECKLIST

Purpose: identify what can break in the trust pipeline and how to detect it before or during pilot execution.

## 1. Storage Backend Risk

Risk:

- Postgres behaves differently from SQLite in JSON, timestamps, ordering, or connection handling

Detection:

- replay diff checker reports mismatches
- Postgres-backed boot fails
- proof endpoint output changes after migration

Controls:

- run runtime validation checklist
- keep SQLite rollback snapshot
- use deterministic cutover gate before rollout

## 2. Trace Ordering Risk

Risk:

- `sequence_id` loses global monotonic behavior
- trace writes become non-deterministic under concurrency

Detection:

- duplicate `sequence_id`
- replay mismatch
- broken hash chain

Controls:

- preserve `sequence_id` uniqueness
- validate `trace_events` ordering after smoke tests
- add concurrency audit before larger rollout

## 3. Identity Attribution Risk

Risk:

- client-provided actor identity leaks past middleware
- JWT binding regresses

Detection:

- spoofing test fails
- stored `actor_id` differs from authenticated principal expectations

Controls:

- keep identity override tests in CI
- review trace rows for pilot rides
- reject any route path that bypasses auth + trace middleware

## 4. Receipt Divergence Risk

Risk:

- receipt hash changes across backends or restarts

Detection:

- replay diff checker mismatch
- receipt endpoint mismatch before/after restart

Controls:

- use receipt determinism tests
- compare cutover receipts on sample rides
- block cutover if any mismatch occurs

## 5. Replay Regression Risk

Risk:

- replay result differs from the authoritative trace

Detection:

- `replay_verified` false
- evidence status `REJECTED`

Controls:

- keep replay determinism tests in CI
- rebuild derived tables only from trace
- never treat projection tables as truth

## 6. Secret and JWT Risk

Risk:

- token secret leaks
- stale secret invalidates clients unexpectedly
- no key rotation plan

Detection:

- unexpected auth failures
- unauthorized token acceptance

Controls:

- move secret to managed secret storage
- define rotation window and key rollout process
- audit token issuance endpoint usage

## 7. Backup and Recovery Risk

Risk:

- restore succeeds technically but proof outputs change

Detection:

- replay diff checker mismatch after restore
- receipt drift after recovery

Controls:

- verify backups by replay, not just by restore success
- keep deterministic post-restore validation mandatory

## 8. Derived Table Misuse Risk

Risk:

- application starts trusting `replay_snapshots`, `evidence_records`, or `receipt_records` as truth

Detection:

- proof routes bypass trace-backed derivation
- inconsistent behavior between projection rows and live replay

Controls:

- preserve the rule that derived tables are disposable
- code review any feature touching derived tables

## 9. Operational Visibility Risk

Risk:

- errors occur in trace or replay path with no usable signal

Detection:

- operators cannot distinguish auth issues from replay issues
- no structured logs for ride or trace identifiers

Controls:

- add structured logging with `ride_id`, `event_id`, `actor_id`
- add alerting on replay/evidence failures

## 10. Pilot Field Risk

Risk:

- real drivers/riders fail flows despite repository correctness

Detection:

- incomplete rides
- token handling failures on real devices
- operator intervention needed to finish basic flow

Controls:

- small controlled rollout first
- observer present
- one route, one driver, one rider initially

## Global Stop Conditions

Stop the pilot or cutover if any occur:

- replay mismatch
- receipt mismatch
- broken trace identity attribution
- repeated auth failures for valid users
- inability to reconstruct a completed ride from trace
- backup restore produces different proof outputs
