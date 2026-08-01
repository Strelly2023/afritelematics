# NovaID Phase 5E concurrency evidence

LOCAL VERIFICATION ONLY — NOT PRODUCTION CERTIFICATION — NOT GA CERTIFICATION.

PostgreSQL READ COMMITTED, two independent workers and pooled connections, 20 iterations each:

- Registration identical idempotency key: one identity, membership, credential, and challenge; identical response.
- Outbox publisher claim: `FOR UPDATE SKIP LOCKED`; one publication per event.

Deadlocks: 0. Serialization failures: 0. Retries: 0. Other prescribed races were not executed; CONCURRENCY_VERIFIED remains PARTIAL.
