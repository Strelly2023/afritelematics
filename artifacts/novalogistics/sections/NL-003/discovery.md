# NL-003 security discovery

Baseline: `8a8bea7627971a6e7fcaa317b898d1fdba90ad5f` on `feature/product-factory-enterprise-sdlc`.

## Shared contracts reused

- NovaID `TenantMembership`, `MembershipStatus`, authorization decisions, permissions, roles, and lifecycle services establish the platform vocabulary.
- NovaID persistence already owns identity and credential records; NovaLogistics must not query or duplicate that database.
- NovaLogistics NL-002 supplies tenant-scoped persistence, optimistic concurrency, migrations, deterministic JSON, and transactional outbox conventions.
- Existing request/correlation identifier and immutable audit-event conventions are retained.

## Ownership boundary

NovaID remains authority for identities, sessions, credentials, authentication assurance, and service-identity status. NovaLogistics owns bounded identity references, tenant logistics memberships, role assignments, effective logistics permissions, service scopes, authorization decisions, and audit attribution.

## Design

- Immutable human, service, and anonymous principals with no raw-token field.
- Explicit role and permission enums; platform-only roles cannot be assigned by tenant administrators.
- Invited/active/suspended/revoked/expired membership lifecycle with optimistic versioning.
- Deterministic fail-closed authorization and resource ownership/assignment policies.
- Tenant resolver accepts a header only after membership validation and rejects conflicting sources.
- Versioned NovaID status adapter protocol with deterministic test adapter and unavailable/invalid failure states.
- Migration `0002_novalogistics_authorization` adds indexed membership, service-identity, and authorization-audit tables without altering NovaID storage.

Impersonation is deferred: no canonical safe NovaLogistics support-access flow exists. Unrelated NovaPay, architecture, administration, recovery, local database, and cache files are excluded.
