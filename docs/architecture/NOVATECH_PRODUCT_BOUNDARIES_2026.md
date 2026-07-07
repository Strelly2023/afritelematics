# NovaTech Product Boundaries 2026

## Doctrine

NovaTech is a platform ecosystem, not a super app.

```text
Independent products.
Shared platform.
Optional integration.
```

NovaID, NovaPay, and NovaRide are independently usable, independently deployable, independently scalable products. They interoperate only through explicit APIs, SDK contracts, events, consent grants, and trust evidence references.

## Product Map

```text
                     NovaTech Platform
                           |
      +--------------------+--------------------+
      |                    |                    |
   NovaID               NovaPay              NovaRide
  Identity              Payments             Mobility
```

## NovaID Responsibilities

NovaID owns trusted identity and access foundations:

- Registration and login
- MFA
- Passkeys
- Biometric authentication prompts
- Identity verification
- Digital credentials
- Consent grants and revocation
- Device trust
- Access management
- Identity certificates and verification timelines

NovaID does not manage wallets, ledgers, transfers, dispatch, ride booking, fleet operations, or ride lifecycle business rules.

## NovaPay Responsibilities

NovaPay owns financial services:

- Wallets
- Ledger
- Domestic and international transfers
- Merchant payments
- Agent banking
- Business payments
- QR payments
- Settlement
- Receipts
- Reconciliation
- FX quotes and transfer tracking
- Payment risk indicators

NovaPay does not own identity verification business rules or transport workflows. When it needs user authentication or reusable identity claims, it requests them from NovaID through an approved contract.

## NovaRide Responsibilities

NovaRide owns mobility:

- Rider booking
- Driver workflow
- Dispatch
- Driver matching
- Fleet
- Ride lifecycle
- Navigation coordination
- Safety and SOS
- Corporate transport
- Ride receipts
- Trip replay

NovaRide does not implement a wallet, ledger, settlement engine, or identity authority. It may use NovaPay payment references and NovaID identity claims through approved contracts.

## Shared NovaTech Platform Responsibilities

The shared platform provides infrastructure capabilities without turning product teams into one product:

- API gateway
- Authorization policy
- RBAC and ABAC
- Notifications
- Audit
- Observability
- Analytics
- NovaTrust evidence references
- NovaAI advisory insights only
- Service discovery
- Product registry
- Shared event envelope types

Shared services must not contain app-specific product workflows such as approving a payment, dispatching a ride, or approving an identity.

## Allowed Integration Rules

- NovaPay may request NovaID authentication and verified identity claims.
- NovaRide may request NovaID authentication and verified identity claims.
- NovaRide may request NovaPay payment authorization, payment status, and receipt references.
- NovaPay and NovaRide may publish signed evidence references to NovaTrust.
- Products may publish notification events through Notification Hub.
- NovaAI may produce advisory insights, recommendations, forecasts, and risk context.
- Cross-product data sharing requires an explicit consent grant, policy basis, or operational contract.
- Products may depend on shared SDK types, design tokens, and platform events.

## Forbidden Coupling Rules

- NovaID must not import NovaPay or NovaRide app internals.
- NovaPay must not import NovaRide app internals.
- NovaRide must not import NovaPay app internals except through approved payment contracts or SDK types.
- Shared packages must not import product app internals.
- NovaAI must not dispatch rides, approve payments, approve identities, or override product business rules.
- One product release must not require another product app to be rebuilt unless a versioned contract intentionally changes.
- Product databases must not be used as integration APIs by other products.
- Product UI screens must not be copied across products as business logic.

## Customer Usage Examples

### Identity Only

```text
User -> NovaID
```

The user manages credentials, consent, device trust, and authentication. No wallet or ride account is required.

### Payments Only

```text
User -> NovaPay
```

The user sends money, receives money, uses QR pay, and views receipts. NovaID authentication can be offered but NovaRide is not required.

### Mobility Only

```text
User -> NovaRide
```

The user books rides and receives ride receipts. Payment may be cash, external provider, or NovaPay if configured.

### Identity And Payments

```text
User -> NovaID
User -> NovaPay
```

The user signs in with NovaID and uses NovaPay wallet, transfers, receipts, and risk-aware payment flows. NovaRide is not required.

### Identity And Ride

```text
User -> NovaID
User -> NovaRide
```

The user signs in with NovaID and books rides through NovaRide. Payments can remain outside NovaPay where a market supports it.

### Payments And Ride

```text
User -> NovaPay
User -> NovaRide
```

NovaRide requests NovaPay payment authorization and receipt references. NovaID can be added later without changing the ride lifecycle.

### Full Ecosystem

```text
User -> NovaID -> authenticated session
                 -> NovaPay wallet and receipts
                 -> NovaRide booking and trip replay
```

The experience is unified through consent, shared session context, events, and trust references. The products remain independently deployable.

## Release Principle

Each product keeps its own apps, APIs, persistence, business rules, ownership, and release cycle. Shared services provide reusable infrastructure and contracts only.
