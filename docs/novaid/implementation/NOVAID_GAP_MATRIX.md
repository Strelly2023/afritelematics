# NovaID gap matrix

| Requirement | Area | Evidence | Status | Missing / next implementation |
|---|---|---|---|---|
| NI-AUT-001 | Password storage | `afritech/novaid/security.py` invariant tests | IMPLEMENTED_AND_VERIFIED | Integrate credential table and breached-password provider |
| NI-AUT-002 | Registration/login | existing service/API | PARTIALLY_IMPLEMENTED | Ownership workflow, enumeration protection, durable rate limits |
| NI-MFA-001 | Purpose-bound OTP | security module tests | IMPLEMENTED_AND_VERIFIED | Provider delivery, distributed throttling, audit outbox |
| NI-PSK-001 | WebAuthn | passkey metadata methods | MOCK_ONLY | Standards library ceremonies, origin/RP/signature verification, device evidence |
| NI-SES-001 | Refresh rotation/reuse | security module tests | IMPLEMENTED_AND_VERIFIED | PostgreSQL atomic adapter and API integration |
| NI-SES-002 | Session revocation | security module tests | IMPLEMENTED_NOT_VERIFIED | Distributed propagation test and API integration |
| NI-TEN-001 | Tenant isolation | organization filter and prior tests | PARTIALLY_IMPLEMENTED | Mandatory tenant key and request-scoped negative suite on every resource |
| NI-RBAC-001 | Server authorization | service role checks | PARTIALLY_IMPLEMENTED | governed bindings, expiry, SoD, stale-token invalidation |
| NI-VRF-001 | Identity verification | deterministic abstractions | MOCK_ONLY | encrypted evidence, provider contracts, manual-review state machine |
| NI-FED-001 | Federation | metadata surfaces | PARTIALLY_IMPLEMENTED | signed assertion/token validation and certification |
| NI-PAM-001 | Privileged access | no sufficient evidence | MISSING | complete time-bound elevation workflow |
| NI-PRV-001 | Consent/privacy | consent records | PARTIALLY_IMPLEMENTED | versioned notices, retention and request fulfillment |
| NI-AUD-001 | Immutable audit | trust records | PARTIALLY_IMPLEMENTED | append-only schema, access controls and restoration evidence |
| NI-REL-001 | Production release | no executed certification | BLOCKED_EXTERNAL | infrastructure, keys, providers, physical devices and independent assurance |

All security, privacy, compliance, operational, and release impacts are high for incomplete P0 rows. No incomplete row may be inferred complete from a route, UI, test name, screenshot, or prior artifact.
