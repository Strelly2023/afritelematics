# NovaRide gap matrix

| Capability | Current evidence | Status | Remaining gate |
|---|---|---|---|
| Rider journeys | Expo app, API contracts, primary-journey tests | Implemented | Physical-device acceptance |
| Driver journeys | Expo app, location/offline diagnostics tests | Implemented | Background-location field trial |
| Dispatch/trip runtime | State machines, services, realtime coordination | Implemented | Load and regional failover exercise |
| Pricing/payments | Pricing package, wallet adapter, payment-safety tests | Implemented | Live provider certification |
| Safety/support | Incident service and support/operations surfaces | Implemented | Staffed incident drill |
| Operations/admin | Multiple operations, dispatch, fleet and support portals | Implemented | Install isolated portal dependencies in CI |
| Durability | PostgreSQL repositories/migrations, outbox, replay | Implemented | Run integration suite with PostgreSQL/Redis/Kafka |
| Mobile distribution | Versioned APKs, checksums and manifests | Evidence present | Rebuild after brand-manifest change |
| Security | TLS pinning, secure store, access-control tests | Partial evidence | SAST/dependency scan and external assessment |
| Observability | SLO, readiness, monitoring tests and deploy assets | Implemented | Production telemetry validation |
