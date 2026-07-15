# NovaRide Runtime Runbook

1. Check `/v1/novaride/runtime/status`.
2. Check `/v1/novaride/runtime/guards`.
3. Inspect `/v1/novaride/runtime/events`.
4. Rebuild read models from event replay if projections drift.
5. Keep GA and real-payment guards disabled until governance approval.
