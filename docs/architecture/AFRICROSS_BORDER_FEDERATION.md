# AfriRide Cross-Border Federation

ADR-0037 introduces a deterministic cross-border federation surface that consumes legal compliance outputs and emits replayable cross-border transition records without introducing authority leakage.

## Boundary

- Cross-border federation is read-only and reference-only.
- Federation cannot override proof, replay, settlement, dispatch, custody, trust, regulator certification, or legal compliance.
- Federation artifacts must remain hash-stable and replayable.

