# NovaRide Phase 0 Domain Tables

Phase 0 is the SaaS foundation for NovaRide. It is the shared control layer for tenants, access, billing, feature control, notifications, and integrations.

For the full system database contract across mobility execution, trust, event
streaming, and evidence tables, see:

- `docs/architecture/NOVARIDE_SYSTEM_DATABASE_V1.md`

## Implemented tables

- `organizations`
- `organization_profiles`
- `accounts`
- `subscriptions`
- `catalog_features`
- `feature_flags`
- `audit_events`
- `notifications`
- `integrations`

## Table roles

- `organizations`: canonical tenant registry.
- `organization_profiles`: tenant type, status, owner, and plan metadata.
- `accounts`: user membership and role mapping per organization.
- `subscriptions`: plan and entitlement record per organization.
- `catalog_features`: global feature catalog.
- `feature_flags`: organization-scoped feature toggles.
- `audit_events`: immutable audit trail for platform actions.
- `notifications`: queued notification outbox.
- `integrations`: external connector registry.

## Phase 0 readiness contract

The Phase 0 API reports ready when:

- the tenant registry exists
- subscription control exists
- the feature catalog exists
- feature flags can be set per organization
- audit logging exists
- notification outbox exists
- integration registry exists
- provider access remains backend-only
