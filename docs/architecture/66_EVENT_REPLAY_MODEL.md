# NovaRide Event Replay Model

Status: CANONICAL REPLAY CONTRACT
Classification: DETERMINISTIC RECOVERY SURFACE

## Replay Purpose

Replay rebuilds platform state from event history and registry state.

## Replay Inputs

- append-only event stream
- registry snapshot
- schema version map
- decision trace records
- idempotency records

## Replay Guarantees

- same input stream produces same reconstructed state
- reprocessing does not duplicate side effects
- invalid or unknown versions stop replay unless explicitly migrated
- missing decision trace blocks governed replay for protected actions

## Replay Outputs

- reconstructed rides
- reconstructed wallet balances
- reconstructed approvals
- reconstructed audit trail
- reconstructed verification outputs

## Replay Rule

```text
If the stream cannot be replayed against the registry snapshot, the event
history is incomplete for governed production use.
```

