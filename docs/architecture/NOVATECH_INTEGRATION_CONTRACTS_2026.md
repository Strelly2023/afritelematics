# NovaTech Integration Contracts 2026

## Contract Principles

- Integration is explicit, versioned, and auditable.
- Products exchange references and claims, not private app internals.
- Consent grants are required for user-controlled cross-product data sharing.
- NovaAI is advisory-only and never performs final operational approval.

## NovaID To NovaPay Authentication Contract

Purpose: let NovaPay authenticate users and receive reusable identity claims.

Producer: NovaID

Consumer: NovaPay

Contract fields:

- `sessionId`
- `subjectId`
- `assuranceLevel`
- `authenticatedAt`
- `expiresAt`
- `methods`
- `deviceTrustLevel`
- `consentGrantId`
- `verifiedClaims`

Allowed use:

- Wallet login
- Transfer authorization
- High-risk action step-up
- KYC/KYB claim reuse
- Receipt identity attribution

Forbidden use:

- NovaPay cannot modify NovaID credentials.
- NovaPay cannot approve identity verification.
- NovaPay cannot bypass consent or assurance requirements.

## NovaID To NovaRide Authentication Contract

Purpose: let NovaRide authenticate riders, drivers, operators, and fleet users.

Producer: NovaID

Consumer: NovaRide

Contract fields:

- `sessionId`
- `subjectId`
- `role`
- `assuranceLevel`
- `deviceTrustLevel`
- `credentialReferences`
- `consentGrantId`
- `expiresAt`

Allowed use:

- Rider sign-in
- Driver verification badge
- Operator access
- Fleet administrator access
- Safety escalation identity context

Forbidden use:

- NovaRide cannot issue or revoke NovaID credentials.
- NovaRide cannot treat NovaID as a ride dispatch engine.
- NovaRide cannot require NovaPay unless a payment method explicitly uses it.

## NovaPay To NovaRide Payment Contract

Purpose: let NovaRide request payment authorization and retrieve payment status without embedding wallet logic.

Producer: NovaPay

Consumer: NovaRide

Contract fields:

- `paymentIntentId`
- `rideId`
- `payerId`
- `amount`
- `currency`
- `status`
- `authorizedAt`
- `capturedAt`
- `receiptReference`
- `riskIndicator`
- `failureReason`

Allowed use:

- Fare authorization
- Capture on trip completion
- Refund/dispute reference
- Ride receipt payment status

Forbidden use:

- NovaRide cannot write ledger entries directly.
- NovaRide cannot settle funds.
- NovaRide cannot approve payment risk overrides.

## NovaRide To NovaTrust Ride Evidence Contract

Purpose: record ride evidence references without exposing operational data as shared mutable state.

Producer: NovaRide

Consumer: NovaTrust

Contract fields:

- `evidenceId`
- `rideId`
- `evidenceType`
- `hash`
- `signedAt`
- `signingKeyId`
- `retentionPolicy`
- `jurisdiction`
- `replayReference`

Allowed use:

- Ride receipt verification
- Trip replay verification
- Dispute evidence
- Safety audit

Forbidden use:

- NovaTrust cannot dispatch rides.
- NovaTrust cannot mutate ride lifecycle state.

## NovaPay To NovaTrust Payment Receipt Contract

Purpose: record payment receipt evidence for audit, dispute, and reconciliation.

Producer: NovaPay

Consumer: NovaTrust

Contract fields:

- `receiptId`
- `paymentIntentId`
- `ledgerEntryId`
- `hash`
- `signature`
- `issuedAt`
- `amount`
- `currency`
- `payerReference`
- `payeeReference`

Allowed use:

- Digital receipts
- Transaction certificates
- Audit packages
- Dispute support
- Settlement reconciliation

Forbidden use:

- NovaTrust cannot approve payment authorization.
- NovaTrust cannot create ledger entries.

## Notification Hub Event Contract

Purpose: standardize cross-product notification delivery.

Producer: any product or shared platform service

Consumer: Notification Hub

Contract fields:

- `eventId`
- `product`
- `eventType`
- `recipientId`
- `channels`
- `priority`
- `title`
- `body`
- `deepLink`
- `evidenceReference`
- `createdAt`

Allowed use:

- Push notifications
- Email notifications
- SMS notifications
- In-app notifications
- Transfer and ride status updates

Forbidden use:

- Notification Hub cannot change product business state.
- Notification Hub cannot infer consent where none exists.

## NovaAI Advisory-Only Contract

Purpose: provide insights while preserving product ownership of decisions.

Producer: NovaAI

Consumer: NovaID, NovaPay, NovaRide, operators, support, compliance, and product dashboards

Contract fields:

- `insightId`
- `product`
- `subjectReference`
- `category`
- `confidence`
- `recommendation`
- `rationale`
- `sourceSignals`
- `createdAt`
- `expiresAt`
- `humanReviewRequired`

Allowed use:

- Risk context
- Advisory recommendations
- Forecasts
- Support suggestions
- Compliance queue prioritization
- Fleet and payment monitoring insights

Forbidden use:

- NovaAI cannot dispatch rides.
- NovaAI cannot approve payments.
- NovaAI cannot approve identity.
- NovaAI cannot override consent.
- NovaAI cannot mutate product ledgers, credentials, or ride lifecycle state.

## Versioning

Contracts are versioned by document year and SDK export name. Breaking changes require a new contract version and a staged migration plan for every consuming product.
