# NovaRide Event Replay Runbook

1. Snapshot current read model state.
2. Select replay scope: aggregate, correlation ID, or event range.
3. Rebuild read models idempotently.
4. Compare counts and state hash.
5. Quarantine poison events and preserve dead-letter reason.
