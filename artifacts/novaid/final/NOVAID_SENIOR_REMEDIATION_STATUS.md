# NovaID senior remediation status

**Date:** 2026-07-29
**Decision:** repository-actionable local baseline complete; production and
external assurance remain blocked.

## Closed in this pass

- Durable failed-login counters commit independently from rejected
  authentication transactions.
- Canonical identity schema tests use explicit named columns and no longer
  depend on table column order.
- Migration `0009_canonical_identity_profile.sql` is part of the production
  migration revision ledger.
- SQLite and PostgreSQL WebAuthn counter adapters share the integer row-count
  contract expected by the application service.
- Tenant WebAuthn policy history creates durable identifiers and preserves the
  governed reason.
- Passwordless WebAuthn sessions become `ACTIVE` with
  `PHISHING_RESISTANT` strength before refresh credentials are committed.
- Canonical tenant, biometric, document, liveness, face, and final identity
  verification domain/persistence increments are included in the NovaID
  source and test scope.

## Executable evidence

Final local command:

```text
venv/bin/python -m pytest -q tests/novaid afritech/tests/novaid -rs
```

Result:

```text
617 passed, 13 skipped, 12 warnings
```

The 13 skips require PostgreSQL and/or Redis integration infrastructure and
cover production runtime, races, WebAuthn/recovery concurrency, Redis
coordination, and distributed delivery.

## Honest remaining blockers

- The generic NovaID ecosystem surface and durable authentication surface
  remain separate authority models and require a governed consolidation
  migration.
- New biometric/eKYC persistence remains local SQLite evidence until
  PostgreSQL schema/repositories and runtime/API wiring are implemented.
- Current PostgreSQL/Redis integration, race, outage, and two-process
  certification must run without skips.
- HS256 environment-secret signing remains pending asymmetric KMS/HSM-backed
  signing, JWKS, key IDs, and rotation.
- Browser and physical-device WebAuthn, FIDO MDS/conformance, biometric
  accuracy/fairness/spoof evaluation, accessibility, penetration testing,
  privacy/compliance review, backup/restore, HA/failover, load/soak, pilot,
  PRR, and authenticated GA approval require external environments or
  authorities.

No external or production certification is claimed by this status.
