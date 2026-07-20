# NovaRide architecture

Mobile and web clients call the FastAPI surface, which delegates to the `afritech/novaride_runtime` domain/application modules. PostgreSQL repositories and migrations provide durable state; Redis coordinates realtime/idempotency concerns; Kafka plus the transactional outbox carries events; projections form operational read models. Wallet, maps, notification and provider integrations are adapter boundaries. Readiness, SLO, incident and replay modules support operation and recovery.

Trust boundaries require authenticated, authorised API calls; server-side fare/trip transitions; idempotency for mutations; redacted structured telemetry; encrypted transport; secret injection; and explicit separation of test/provider modes. Mobile clients are not authoritative for pricing, trip completion or payment settlement.
