# NovaID Identity Framework 2026

NovaID is the identity and authentication layer for NovaTech. It verifies who a user or organization is, then exposes that identity to NovaPay, NovaRide, and other NovaTech services through explicit APIs and trust contracts.

## Product Boundary

- NovaID authenticates and verifies identity.
- NovaPay executes financial services.
- NovaRide handles mobility only.
- NovaTrust records evidence and audit trails.
- NovaAI remains advisory only.

## Identity Types

| Type | Purpose | Verification Level |
| --- | --- | --- |
| Personal | Digital identity for individual users | 6 |
| Business | Digital identity for organizations | 5 |
| Employee | Workforce identity | 5 |
| Partner | Identity for external organizations and integration partners | 5 |
| Inspector | Identity for audit, compliance, and regulatory personnel | 6 |

## Shared Security Controls

- Email verification
- Phone verification
- Multi-factor authentication
- Device registration
- Biometric authentication where supported
- Login history
- Session management
- Passwordless authentication optional
- Security alerts
- Account recovery
- Audit logging

## Verification Levels

| Level | Description |
| --- | --- |
| 0 | Account created |
| 1 | Email verified |
| 2 | Phone verified |
| 3 | Government identity verified |
| 4 | Biometric identity verified |
| 5 | Profession or organization verified |
| 6 | Fully trusted identity with continuous compliance monitoring |

## Trust Attributes

Every NovaID identity maintains:

- Identity verification status
- Verification level
- Email verification
- Phone verification
- Device trust
- Biometric verification
- Organization verification where applicable
- Role verification
- Compliance status
- Last security review
- Risk score

## Implementation Notes

- Use the identity type that matches the legal and operational context.
- Keep verification risk-based and least-privilege by default.
- Do not reuse NovaPay or NovaRide business logic inside NovaID.
- Use NovaTrust for evidence, not for identity decisions.
- Use NovaAI only for advisory guidance, never for identity approval.

## NovaID App Surfaces

### Personal

- Home
- Verify
- Documents
- Security
- Activity
- Profile

### Business

- Overview
- Business Verify
- Representatives
- Documents
- Access
- Audit
- Settings

### Employee

- Dashboard
- Employment
- Access
- Tasks
- Security
- Profile

### Partner

- Overview
- Partner Verify
- Integrations
- Credentials
- Compliance
- Support
- Settings

### Inspector

- Dashboard
- Inspections
- Cases
- Evidence
- Reports
- Security
- Profile

## Common API Shape

- Authentication: login, logout, OTP, MFA
- Profile: read and update identity profile
- Verification: personal, business, employee, partner, inspector
- Documents: upload and status
- Biometric: liveness and face matching
- Consent: grant and revoke
- Activity: history and event stream
- Audit: signed export and replay trace
- Devices: trusted device management
- Freeze: temporary account freeze and recovery
