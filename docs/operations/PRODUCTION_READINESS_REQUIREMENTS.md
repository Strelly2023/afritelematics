# Production Readiness Requirements

These items are external production dependencies, not ordinary source-controlled
features. They are required to activate live NovaPay and NovaRide services in
production, but they are intentionally provisioned outside the repository for
security, regulatory, and operational reasons.

## 1. Production Credentials

Required before production deployment:

- production OAuth clients
- production JWT signing keys
- passkey / WebAuthn configuration
- MFA providers
- FCM and APNs credentials
- SMS and email provider credentials
- maps API keys
- object storage credentials
- CDN configuration
- TLS certificates
- DNS records
- production secrets
- database credentials
- Redis credentials

Repository policy:

```text
Production credentials MUST NOT be stored in source control.

They are provisioned through Secret Manager, Vault, GitHub Actions Secrets,
cloud secret managers, or environment variables.
```

## 2. Live Payment Providers

Commercial payment activation requires live provider adapters and provider-side
activation.

Supported adapter model:

- Stripe
- Flutterwave
- PayPal
- Apple Pay
- Google Pay
- bank transfer rails
- cash
- future regional providers

Per provider, production activation requires:

- live API credentials
- webhook registration
- webhook signature verification
- settlement account configuration
- refund configuration
- dispute / chargeback configuration
- provider certification where applicable

Governance rule:

```text
Provider adapters execute payments.

NovaPay Core remains the authority for ledger state, wallet balances,
settlement state, receipts, replay, and evidence.
```

## 3. App Store Deployment

Android requirements:

- production signing key
- Android App Bundle output
- Play Integrity API
- privacy policy
- Data Safety declaration
- internal testing
- closed testing
- production rollout

iOS requirements:

- Apple Developer Program membership
- distribution certificate
- App Store Connect access
- APNs production keys
- TestFlight
- Privacy Manifest
- background location justification when used
- App Review approval

Release pipeline:

```text
Commit -> Fast CI -> Full Certification -> Production Build -> Security Scan
-> Store Validation -> Internal Testing -> Closed Beta -> Production Release
```

## 4. Operational Readiness Checklist

| Requirement | NovaRide | NovaPay | Status |
| --- | --- | --- | --- |
| Production secrets | Required | Required | External dependency |
| TLS certificates | Required | Required | External dependency |
| Production database | Required | Required | External dependency |
| Redis cluster | Required | Required | External dependency |
| Monitoring | Required | Required | External dependency |
| Backups and restore | Required | Required | External dependency |
| Disaster recovery | Required | Required | External dependency |
| Live payment providers | N/A | Required | External dependency |
| Store signing | Required | Required | External dependency |
| Store consoles | Required | Required | External dependency |
| Security review | Required | Required | External dependency |
| Pilot approval | Required | Required | External dependency |
| Go-live approval | Required | Required | External dependency |

## 5. Launch Readiness Gates

Technical gates:

- all CI pipelines pass
- architecture boundary validation passes
- runtime governance validation passes
- security scan passes
- documentation validation passes
- no critical vulnerabilities remain

Operational gates:

- production credentials are provisioned
- monitoring is active
- alerting is configured
- backups are verified
- disaster recovery is tested
- incident response procedures are documented

Business gates:

- payment providers are certified for NovaPay
- merchant onboarding is complete for NovaPay
- driver onboarding is complete for NovaRide
- compliance approval is recorded
- legal approval is recorded
- executive go-live approval is recorded

## 6. Architecture Maturity Classification

| Layer | Status |
| --- | --- |
| Platform architecture | Complete |
| Core implementation | Complete |
| Governance and trust | Complete |
| CI/CD and quality | Complete |
| Production configuration | Operational requirement |
| Live external integrations | Operational requirement |
| Commercial deployment | Operational approval |

This classification separates implemented software from external activation and
launch dependencies.
