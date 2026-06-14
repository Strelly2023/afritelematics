# AfriMobility Intelligence Layer

ADR-0033 defines the advisory-only intelligence surface for Gen-3 mobility.

## Purpose

Provide deterministic forecasts, anomaly signals, and optimization suggestions
without becoming truth, proof, replay, dispatch, or settlement authority.

## Governance Rules

- Intelligence is advisory only.
- Intelligence output must be deterministic.
- Intelligence must be replayable from the same inputs.
- Intelligence must not mutate external system state.
- Intelligence must not override dispatch, proof, replay, or settlement.

## Proof Boundary

The intelligence layer emits reference-only proof artifacts.
The proof payload may describe the advisory result, but it must not become
system authority.

