# NL-003 — Authentication, authorization, and multi-tenancy

Baseline: `8a8bea7627971a6e7fcaa317b898d1fdba90ad5f` on `feature/product-factory-enterprise-sdlc`.

Implemented NovaID-compatible immutable identity references; human, service, and anonymous principals; invited/active/suspended/revoked/expired tenant memberships; all 17 required roles; fine-grained permission mappings; deterministic tenant, resource-owner, assignment, platform, and service-scope authorization; auditable decisions; validated tenant resolution; a versioned fail-closed NovaID adapter boundary; durable membership/service/audit repositories; and migration `0002_novalogistics_authorization`.

NovaID remains authority for authentication, credentials, sessions, identity verification, and service status. No raw token, secret, password, passkey, biometric, or NovaID internal persistence is stored. Impersonation is deferred because no canonical safe logistics flow exists.

Tables added: `novalogistics_memberships`, `novalogistics_service_identities`, and `novalogistics_authorization_audit`, with tenant/status/identity and audit-time indexes. Membership updates use tenant/id/version conditional writes. Tenant administrators cannot assign platform roles. Service principals receive only named scopes.

Validation: 22 focused security tests; 49 total NovaLogistics tests; 8 shared NovaID tests; 54 broader logistics/persistence tests; 5 public-web tests; compile PASS. Final runtime, constitutional, unified, and diff results are enforced by staging and commit gates.

Release classification: `DEVELOPMENT_COMPLETE`. NL-004 is not started.
