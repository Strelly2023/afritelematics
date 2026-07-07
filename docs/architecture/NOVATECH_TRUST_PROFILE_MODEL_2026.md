# NovaTech Trust Profile Model 2026

NovaTech uses trust profiles to describe identity confidence, device assurance, compliance posture, and operational status across NovaID and NovaPay.

## Shared Principles

- Trust profiles are descriptive records, not authorization engines.
- NovaID owns identity trust.
- NovaPay owns wallet and agent trust.
- NovaTrust owns evidence, signatures, and audit trails.
- NovaAI remains advisory only.

## Required Trust Fields

- Identity status
- Verification level
- Email verification
- Phone verification
- Device trust
- Biometric verification
- Organization verification where applicable
- Role verification
- Compliance status
- Last security review
- Fraud risk
- Operational status

## NovaID Trust Profile

- Identity verification status
- Verification level
- Email verification
- Phone verification
- Device trust
- Biometric verification
- Organization verification
- Role verification
- Compliance status
- Last security review
- Risk score

## NovaPay Trust Profile

- Identity status
- Verification level
- Device trust
- Compliance status
- Fraud risk
- Operational status
- Security score
- Wallet status
- KYC status
- Settlement status
- Evidence status

## Evidence Rule

Any financial activity must generate NovaTrust evidence, including:

- Ledger entry
- Settlement record
- Digital signature
- Replay evidence
- Audit package
- PDF receipt

## Boundaries

- Trust profiles do not replace product-specific workflow rules.
- Trust profiles do not move ride logic into NovaPay.
- NovaAI can advise on risk, but cannot approve identity or payments.
