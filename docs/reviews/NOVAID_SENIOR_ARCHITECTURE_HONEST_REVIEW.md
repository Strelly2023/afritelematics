# NovaID Senior Architecture Honest Review

**Review date:** 2026-07-29
**Review type:** architecture, security, operability, and assurance review
**Decision:** **NO-GO for production, public pilot, or GA**

## Executive verdict

NovaID has a serious and increasingly capable identity-security core. The repository contains tenant-aware domain models, lifecycle state machines, password and session controls, rotating refresh families, WebAuthn ceremonies, recovery workflows, PostgreSQL and Redis adapters, outbox delivery, audit replay, observability primitives, and a substantial new biometric/eKYC domain.

NovaID is not yet one coherent production identity platform. It currently contains two authority stacks, two persistence models, catalogue-level standards claims that exceed implemented protocol behavior, a broken local regression baseline, incomplete production migration coverage, and no production persistence or API composition for the new eKYC/biometric capability.

The honest classification is:

| Dimension | Status |
| --- | --- |
| Domain architecture | **Strong but fragmented** |
| Local security implementation | **Substantial** |
| Current local regression baseline | **PASS — 617 passed; 13 infrastructure-dependent skips** |
| Canonical identity authority | **NOT CONSOLIDATED** |
| Production schema/migrations | **INCOMPLETE** |
| PostgreSQL/Redis distributed assurance | **Previously locally exercised; not current-release certified** |
| WebAuthn | **Protocol implementation present; browser/device/FIDO assurance absent** |
| Biometrics and eKYC | **Rich local domain; not production integrated or independently validated** |
| Federation/OIDC/SAML/VC | **Catalogue/metadata surface, not complete standards implementation** |
| Operational readiness | **PARTIAL** |
| Security/compliance certification | **ABSENT** |
| Production / GA | **BLOCKED** |

## Evidence from this review

The initial combined `tests/novaid` and `afritech/tests/novaid` run stopped
after five failures. The senior remediation pass fixed the lockout
transaction boundary, schema-fragile test setup, WebAuthn adapter contract,
policy-history identifier generation, and passwordless session activation.

The final combined run completed with:

- **617 passed**
- **0 failed**
- **13 infrastructure-dependent skips**
- **12 warnings**

The skipped tests cover PostgreSQL, Redis, PostgreSQL runtime/races,
PostgreSQL WebAuthn/recovery races, Redis coordination, and distributed
delivery because their integration infrastructure was unavailable.

Focused new eKYC/domain tests pass, but focused success does not override the combined-suite failure.

## Architecture strengths worth preserving

### Tenant-aware core

The typed domain and durable authentication layers consistently carry tenant identity through identities, memberships, sessions, credentials, recovery, and security events. Tenant-negative tests exist, and the new biometric repositories scope reads by tenant.

### Fail-closed production composition

The durable runtime rejects SQLite in production, requires a PostgreSQL URL, issuer, audience, signing key, and—when configured as required—Redis. This is the correct direction.

### Security state is more than token self-containment

Access-token validation rechecks session state, identity state, membership state, security version, revocation, idle expiry, absolute expiry, tenant, issuer, audience, signature, and authentication strength. That is materially stronger than trusting JWT claims alone.

### WebAuthn and recovery depth

The codebase includes registration/authentication ceremonies, passwordless and step-up paths, credential lifecycle, signature-counter policy, Redis challenge coordination, recovery codes, governed recovery approval, outbox delivery, and distributed event handling.

### Biometric/eKYC domain safety

The new domain models avoid raw media and biometric templates, use reference-based evidence, enforce tenant/context boundaries, model consent, capture environment, liveness, document authenticity, document-selfie matching, and final verification decisions, and reject dangerous payload fields.

### Honest historical evidence labels

Many NovaID artifacts explicitly say “local verification only,” “not FIDO certification,” “not production certification,” and “not GA certification.” Those non-claims are correct and must remain.

## P0 — release-blocking architecture gaps

### NID-ARCH-001: Two NovaID authority stacks are mounted

`afritech.api.app` mounts both:

- `afritech.api.novaid_api.build_novaid_router()`
- `afritech.novaid.runtime.build_default_durable_router()`

Both use the `/v1/novaid` prefix, but they do not share an aggregate, repository, authorization model, or lifecycle:

- the ecosystem router uses `NovaIDEcosystem` plus the generic `NovaIDRepository`;
- the durable router uses normalized identity/session/WebAuthn repositories and security-version enforcement.

The ecosystem service can directly mark an identity verified from supplied method/evidence references. It also exposes passkey, biometric, federation, consent, OAuth-client, and trust records through a generic JSON-record repository. The durable service implements materially stronger security ceremonies and persistence.

**Risk:** split-brain identity authority, inconsistent tenant enforcement, incompatible verification states, duplicate identities, and routes that appear equally authoritative.

**Required exit condition:** select one canonical command/query model and production database. Move presentation/catalogue endpoints behind read models. Deprecate or remove mutation endpoints that bypass the canonical aggregate. Publish one route and authority map and enforce it in tests.

### NID-ARCH-002: Local regression baseline — closed in this pass

The combined local suite now passes. Direct positional identity inserts were
replaced with named-column setup, and failed authentication records its abuse
counter outside the transaction that deliberately rolls back the rejected
authentication.

Passwordless WebAuthn sessions now transition from `PENDING_MFA` to `ACTIVE`
with `PHISHING_RESISTANT` strength in the same transaction that creates the
refresh family.

**Remaining assurance:** PostgreSQL/Redis integration and race suites must run
without skips in a provisioned certification environment.

### NID-ARCH-003: Production migration ledger — locally closed

`0009_canonical_identity_profile.sql` is now included in the accepted
production migration ledger.

**Remaining assurance:** add PostgreSQL eKYC/biometric migrations and test
fresh install, every supported upgrade path, rollback/forward-fix, schema
checksum, and mixed-version deployment behavior.

### NID-ARCH-004: New biometric/eKYC capability is SQLite-only

Biometric consent, enrollment, verification, liveness, document evidence, and identity-verification persistence are implemented in the SQLite schema/repository path. Equivalent PostgreSQL migrations, repositories, runtime wiring, and public/admin API composition were not found.

**Risk:** a locally tested domain cannot run in the production-required PostgreSQL composition. Any production claim would be false.

**Required exit condition:** add normalized PostgreSQL schema and repositories, transactional orchestration/outbox, tenant isolation and concurrency tests, retention/deletion jobs, API authorization, and production-equivalent evidence.

### NID-ARCH-005: Standards catalogue overstates protocol capability

The public catalogue declares OAuth 2.1, OpenID Connect, SAML 2.0, FIDO2/WebAuthn, and Verifiable Credentials profiles. Some endpoints emit configuration or metadata, but a complete authorization server, OIDC conformance surface, SAML IdP/SP implementation, SCIM service, VC issuer/verifier lifecycle, and certified FIDO deployment are not established.

**Risk:** consumers may treat documentation metadata as an interoperable, certified security protocol.

**Required exit condition:** label each entry `CATALOGUE`, `PARTIAL`, `IMPLEMENTED`, or `CERTIFIED`; remove unsupported grants/claims; run applicable conformance suites; publish exact supported profiles and non-claims.

### NID-ARCH-006: Cryptographic key management is development-grade

The durable access-token service supports only HS256 with one environment-provided shared secret. There is no established asymmetric signing, `kid`, JWKS publication, online rotation, overlap window, emergency revocation, KMS/HSM custody, or auditable signing operation.

**Risk:** every verifier needs the signing secret; compromise affects issuance and verification; safe rotation and multi-service trust are not demonstrated.

**Required exit condition:** use asymmetric keys held by KMS/HSM or an equivalent managed signer; publish JWKS; support `kid`, scheduled and emergency rotation, overlap, cache invalidation, algorithm allowlists, key-use audit, and compromise rehearsal.

## P1 — security and domain gaps

### NID-SEC-001: Brute-force and abuse controls are incomplete as a platform

The lockout regression must be fixed. Beyond it, durable distributed throttles are required for registration, login, OTP issue/verify/resend, password reset, recovery, WebAuthn challenge creation, biometric attempts, device enrollment, and high-risk administration.

Rate limits must be tenant-, identity-, identifier-, device-, IP/network-, and risk-aware without enabling user enumeration.

### NID-SEC-002: Authentication and token audit is partial

Existing artifacts acknowledge incomplete durable events for access issuance/validation, session transitions, password operations, delivery retries, and rejection paths.

Every security decision needs an atomic, privacy-filtered, correlation-bound event with actor, subject, tenant, policy version, reason codes, assurance change, and outcome. Audit writes must share the transaction or outbox boundary with the state change.

### NID-SEC-003: Authorization is inconsistent between surfaces

The ecosystem API relies mainly on broad roles such as `CUSTOMER`, `OPERATOR`, and `ADMIN`; the durable authentication API combines bearer validation, tenant headers, authentication strength, and selected role checks. Resource ownership and tenant/organization semantics are not uniformly expressed.

Adopt one policy decision layer for role, permission, ownership, tenant, assurance, risk, device, and purpose checks. Test deny-by-default behavior for every mutation and sensitive read.

### NID-SEC-004: Recovery remains the highest-risk account path

Recovery workflows exist, but production proof must cover social engineering, operator collusion, stale factors, lost devices, compromised sessions, notification, cooling-off, two-person approval where required, recovery cancellation, and post-recovery containment.

No recovery path may produce assurance higher than the verified evidence supports.

### NID-SEC-005: WebAuthn assurance is not yet deployable assurance

Protocol-level software authenticator tests are valuable, but browser/origin integration, physical platform and roaming authenticators, Android/iOS lifecycle, attestation trust, enterprise policy, passkey sync semantics, backup eligibility/state, FIDO MDS, accessibility, and account-recovery interaction remain unverified.

### NID-SEC-006: Biometric and identity-proofing risk governance is incomplete

The internal models are strong, but production requires:

- provider trust and contract boundaries;
- algorithm/version allowlists and rollback;
- spoof/presentation-attack evaluation;
- demographic performance and bias assessment;
- threshold calibration by use case;
- manual-review workflow and reviewer separation;
- consent withdrawal and derived-data deletion;
- retention and jurisdiction policy;
- age/dependent and vulnerable-user handling;
- data-subject access/correction;
- independent privacy, legal, and security review.

No internal unit test can certify algorithm accuracy, liveness resistance, fairness, or legal compliance.

### NID-SEC-007: Privacy enforcement is modelled but not operationally closed

Consent and safe metadata exist, yet there is no demonstrated platform-wide deletion/retention engine, legal-hold policy, cryptographic erasure, provider deletion receipt, export/redaction workflow, or restoration behavior that prevents deleted biometric data from reappearing.

## P1 — data and distributed-systems gaps

### NID-DATA-001: Repository abstraction is incomplete

Application services still use direct SQL and a portability adapter. SQLite `?` parameter conventions and database-specific behavior leak into services.

Complete typed repositories and unit-of-work contracts for every aggregate. Keep SQL in adapters. Add contract tests that run identically against SQLite development and PostgreSQL production implementations.

### NID-DATA-002: Event and aggregate versioning needs one compatibility policy

Domain events have canonical encoding, and outboxes are versioned, but the platform needs a published compatibility model for schema evolution, consumers, replay, tombstones, PII redaction, and event upcasting.

### NID-DATA-003: Distributed consistency evidence is stale or incomplete

Historical artifacts report local PostgreSQL/Redis and two-process exercises, while the current run skipped those suites. Required current evidence includes races for registration, refresh reuse, password reset, lockout, WebAuthn counters, recovery approval, biometric attempts, consent revocation, and duplicate/out-of-order events.

### NID-DATA-004: Redis semantics require explicit safety classification

For each Redis use, declare whether Redis is authoritative, a coordination layer, or a cache. Define fail-open/fail-closed behavior, database reconstruction, TTL semantics, cluster failover, eviction, flush, network partition, stale replica, and replay behavior.

## P1 — operational gaps

### NID-OPS-001: Background worker lifecycle is not production-certified

Publishers and consumers exist, but deployment ownership, graceful drain, lease recovery, poison messages, dead-letter alerting, backpressure, autoscaling, and rolling-upgrade compatibility require current evidence.

### NID-OPS-002: Observability is locally instrumented, not operationally proven

Metrics and JSONL traces exist. Missing proof includes external metrics/tracing backend delivery, dashboards, SLOs, alert thresholds, paging, correlation across API/database/Redis/provider calls, PII controls, sampling policy, and incident rehearsal.

### NID-OPS-003: Backup, restore, HA, and disaster recovery are not certified

Required evidence includes encrypted backups, point-in-time recovery, restore into an isolated environment, key availability, Redis reconstruction, regional failover, measured RPO/RTO, integrity checks, and security-state correctness after restoration.

### NID-OPS-004: Capacity and resilience limits are unknown

Run load, spike, soak, and exhaustion tests for login, token validation, WebAuthn ceremonies, recovery, audit, outbox, and eKYC workflows. Establish safe saturation behavior, admission control, queue limits, and dependency timeout/circuit-breaker policy.

## P2 — product and ecosystem gaps

### NID-ECO-001: Federation, enterprise directory, and lifecycle provisioning

Implement and certify only the protocols actually needed: OIDC/OAuth conformance, SAML where required, SCIM provisioning/deprovisioning, tenant-specific IdP configuration, claim mapping, JIT rules, signing/encryption rotation, logout, and federation incident response.

### NID-ECO-002: Privileged access management is not a mature NovaID capability

PAM requires privileged identity separation, just-in-time grants, approval, step-up, session recording where lawful, break-glass custody, command/action audit, automatic expiry, and periodic access review.

### NID-ECO-003: Device trust and attestation need real platform integration

Metadata fields and trust labels are not equivalent to verified Android Play Integrity, Apple App Attest/DeviceCheck, secure key storage, device binding, key rotation, device loss, jailbreak/root policy, and risk-based fallback.

### NID-ECO-004: User and operator experiences need accessibility and safety validation

Registration, authentication, passkeys, recovery, consent, verification, manual review, error states, and account closure need browser/mobile E2E, WCAG assessment, localization, low-connectivity behavior, and usable security testing.

## Required architecture decisions

Before further feature expansion, approve ADRs for:

1. canonical NovaID authority and retirement of the generic mutation stack;
2. aggregate boundaries for tenant, identity, membership, credential, session, verification, and consent;
3. PostgreSQL schema and migration ownership;
4. token format, asymmetric key custody, and rotation;
5. WebAuthn attestation and FIDO MDS policy;
6. recovery assurance and approval policy;
7. biometric provider, consent, retention, deletion, and fairness policy;
8. event schema compatibility and replay;
9. Redis authority/failure semantics;
10. standards support and conformance claims;
11. audit immutability, access, export, and retention;
12. production SLO, RPO, RTO, and regional topology.

## Closure sequence

| Order | Gate | Exit evidence |
| ---: | --- | --- |
| 1 | Restore baseline | Clean worktree; all local NovaID tests pass with no unexplained critical skips. |
| 2 | Consolidate authority | One canonical mutation stack, one production repository, one route/permission map. |
| 3 | Repair schema lifecycle | Migration ledger includes current identity/eKYC schema; fresh/upgrade/rollback tests pass on PostgreSQL. |
| 4 | Complete production adapters | PostgreSQL eKYC/biometric repositories and transactional outbox pass contract and isolation tests. |
| 5 | Close core security | Lockout, rate limiting, audit atomicity, recovery, asymmetric signing, and key rotation pass adversarial tests. |
| 6 | Certify distributed runtime | PostgreSQL/Redis races, outages, reconstruction, workers, two-process/API, and rolling upgrades pass. |
| 7 | Certify client ceremonies | Browser and physical-device WebAuthn, mobile device trust, accessibility, and recovery journeys pass. |
| 8 | Complete independent assurance | Penetration, privacy, biometric, accessibility, and applicable regulatory reviews are closed. |
| 9 | Operational certification | Load/soak, backup/restore, HA/failover, observability, SLO alerts, and incident exercises pass. |
| 10 | Controlled pilot and PRR | Authenticated pilot outcomes, risk acceptance, approvals, immutable build, SBOM, signatures, and release evidence align. |

## Final senior architecture decision

NovaID should continue as a controlled engineering program, but feature expansion should pause where it creates additional identity authority, persistence, or standards surfaces.

The immediate architectural objective is not “more NovaID.” It is **one NovaID**:

- one canonical identity aggregate;
- one production persistence and migration chain;
- one authorization and assurance model;
- one security event model;
- one standards claim register;
- one immutable release evidence chain.

Until the P0 gaps are closed and the P1 production evidence is current, the senior architecture decision remains:

> **NO-GO — strong local security engineering, but not yet a coherent or certified production identity authority.**
