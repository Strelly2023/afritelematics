# NovaID next actions

1. Implement the PostgreSQL-backed application unit-of-work adapter and production composition.
2. Run the full lifecycle through a live server backed by PostgreSQL and Redis.
3. Add atomic authentication, access-token, password, and session audit events.
4. Complete telemetry export and execute race, Redis outage, and two-process matrices.
5. Replace the transitional SQL facade with explicit repository calls and implement the outbox publisher/consumer lifecycle.

Implement PostgreSQL credential/session/refresh-family migrations and wire the security primitives into authenticated FastAPI endpoints. Then execute tenant-isolation and concurrent refresh-reuse tests against PostgreSQL and Redis before any pilot gate is reconsidered.
