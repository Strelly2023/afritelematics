# NovaID NID-P1-002 Local Implementation Certificate

Date: 2026-07-29

Scope: NID-P1-002 — tenant authorization foundation

Evidence class: source review and deterministic local automated tests

## Certified implementation surface

| Work item | Implementation | Verification |
|---|---|---|
| 2A Tenant Aggregate | Canonical tenant type, tier, legal entity, brand, settings, security policy, metadata, lifecycle and optimistic versioning | Existing tenant aggregate, value-object, boundary and lifecycle suites |
| 2B Membership Aggregate | Governed status machine, validity window, roles, direct permissions, metadata, optimistic versioning and immutable lifecycle events | `test_nid_p1_002_authorization.py` |
| 2C Permission Model | Tenant-scoped roles, allow/deny permissions, wildcards, ownership, device, assurance and authentication-strength constraints | `test_nid_p1_002_authorization.py` |
| 2D Authorization Context | Tenant, actor identity, membership, resource/action, resource tenant/owner, authentication, assurance, device, risk and trace identifiers | `test_nid_p1_002_authorization.py` |
| 2E Authorization Policy Engine | Deny by default; tenant and actor binding; explicit-deny precedence; membership validity; risk, step-up and ownership decisions; stable reason codes | `test_nid_p1_002_authorization.py` |
| 2F Persistence Expansion | PostgreSQL migration 0010, SQLite parity tables, shared repository contract, role grants, effective assignments and immutable policy versions | `test_nid_p1_002_persistence.py` |
| 2G Certification | Focused architectural tests plus the complete NovaID regression suite | This certificate and recorded commands below |

## Security invariants exercised

- No authorization without an active and effective membership.
- No cross-tenant resource, membership, role, or permission use.
- Actor identity and membership identifiers must be bound to the request context.
- Explicit deny takes precedence over allow.
- Missing grants are denied.
- Elevated risk and insufficient authentication controls produce step-up, not allow.
- Critical risk, failed ownership, expired assignments, and terminal memberships deny access.
- Decisions carry a policy version, reason codes, and matched permission keys.

## Automated evidence

Focused architecture command:

```text
python -m pytest -q \
  tests/novaid/test_nid_p1_002_authorization.py \
  tests/novaid/test_nid_p1_002_persistence.py \
  tests/novaid/test_canonical_tenant_aggregate.py \
  tests/novaid/test_tenant_lifecycle_service.py \
  tests/novaid/test_tenant_boundary_service.py
```

Result: `56 passed`.

Complete NovaID regression command:

```text
python -m pytest -q tests/novaid afritech/tests/novaid
```

Result: `645 passed, 13 skipped`.

## Certification boundary

This is a local implementation certificate. It does not claim production
deployment, live PostgreSQL execution, penetration testing, external audit,
operational approval, or environment-specific performance evidence. The
skipped tests remain environment-dependent and do not become certified by
this document.
