# NovaPay GA Elite Implementation Surface

## Status

NovaPay is now implemented as a deterministic Financial Operating System core.

Implementation: ACTIVE CORE
Live Settlement: FORBIDDEN BY DEFAULT
Provider Mode: deterministic adapter unless compliance activation is explicit

The implementation lives in:

- afritech/afripay
- afritech/tests/afripay

## Implemented Modules

- wallet
- double-entry ledger
- adaptive multi-rail routing
- FX rate locking
- escrow
- bulk payouts
- billing
- KYC/AML compliance
- intelligence hooks
- event outbox
- treasury liquidity pools
- immutable event store
- Django ORM persistence
- Docker and Kubernetes deployment pack

## Production Boundary

No live-money movement may occur from deterministic adapters.

The current providers model rail cost, speed, capacity, reliability, failure, and
offline fallback. They do not contact banks, card networks, mobile-money
operators, crypto networks, or settlement systems.

Live settlement requires a separate compliance activation with real provider
credentials, jurisdictional approval, KYC/AML controls, treasury controls,
incident runbooks, and observed economic evidence.

## Financial Invariants

Provider callbacks never define ledger truth.

Ledger journals must balance per currency.

Payment references must be idempotent.

Authority fields are rejected.

Wallet balances and ledger journals are separate surfaces.

FX rates are locked before conversion.

Escrow release requires matching evidence.

Payout item references must be unique.

Treasury liquidity must be reserved before provider execution.

Live settlement requires an explicit compliance activation reference.

## Governance Chain

ADR -> INVARIANT -> BINDING -> RULE -> GUARD -> CI

NovaPay remains bounded by observed economic evidence.

No transaction means no NovaPay.

NovaTech does not create money flows. It observes, records, and proves them.

## Scope

This implementation creates a backend core that can support NovaRide, Agro
payments, remittances, merchant payments, and business finance workflows. It is
not a regulatory claim, bank license claim, deployed payment platform claim, or
production settlement claim.
