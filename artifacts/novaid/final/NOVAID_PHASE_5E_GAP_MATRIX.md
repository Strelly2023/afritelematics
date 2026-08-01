# NovaID Phase 5E gap matrix

| Capability | Result | Limitation |
|---|---|---|
| Session lifecycle/expiry/compromise | PASS locally | Administrative tenant listing not added |
| PostgreSQL mounted runtime | PASS locally | Direct SQL portability facade remains |
| Registration idempotency race | PASS | 2 workers × 20 iterations |
| Outbox claim race | PASS | 2 workers × 20 iterations |
| Remaining race scenarios | NOT_EXECUTED | No full certificate |
| Two-process HTTP | PASS locally | One positive revocation flow |
| Redis delivery semantics | PASS focused | Full real outage matrix incomplete |
| Audit/metrics/traces | PARTIAL | Local evidence; production export absent |
