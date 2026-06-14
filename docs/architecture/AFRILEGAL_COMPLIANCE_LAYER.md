# AfriRide Legal Compliance Layer

ADR-0036 introduces a deterministic legal compliance surface that consumes regulator certification records and emits replayable compliance records without introducing authority leakage.

## Boundary

- Legal compliance is read-only and reference-only.
- Compliance cannot override proof, replay, settlement, dispatch, custody, or trust.
- Compliance artifacts must remain hash-stable and replayable.

