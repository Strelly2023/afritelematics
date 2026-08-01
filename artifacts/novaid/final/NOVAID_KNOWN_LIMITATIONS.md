# NovaID known limitations

## Phase 5C integration limits

- The mounted production PostgreSQL application adapter is not complete.
- NovaID-specific audit completion, telemetry export, outage tests, full race matrix, two-process E2E, browser E2E, and accessibility tests are incomplete.

## Phase 5D runtime limits

- Application services still issue direct SQL through a portability facade.
- Persistence protocols and PostgreSQL repository methods are not complete for every requested operation.
- The outbox publisher, Redis consumer, races, outages, live processes, and live HTTP certificates remain incomplete.

The new security stores are in-process reference adapters. They deliberately do not claim distributed atomicity, durable audit, provider delivery, UI integration, or production readiness. Existing passkey, KYC/KYB, federation, and trust surfaces require deeper standards-based implementations and certification.
