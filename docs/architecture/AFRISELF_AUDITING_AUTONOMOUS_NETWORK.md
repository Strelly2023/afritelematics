# AfriRide Self-Auditing Autonomous Network

ADR-0038 introduces a deterministic self-auditing surface that consumes prior proof hashes and emits replayable audit snapshots without introducing authority leakage.

## Boundary

- Self-auditing is read-only and reference-only.
- Audit cannot override proof, replay, settlement, dispatch, custody, trust, regulator certification, legal compliance, cross-border federation, or public evidence.
- Audit artifacts must remain hash-stable and replayable.

