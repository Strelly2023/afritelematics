# AfriPay GA Elite Technical Whitepaper

## Executive Summary

AfriPay GA Elite is a deterministic Financial Operating System for African
commerce and diaspora value transfer. It combines wallet accounting,
multi-rail payment orchestration, treasury liquidity control, FX locking,
compliance gating, event replay, and governance-backed financial invariants.

The current implementation is an active core with live settlement disabled by
default. Deterministic providers simulate rail behavior until compliance,
provider credentials, treasury policy, and operational activation are approved.

## Strategic Thesis

African commerce is fragmented across mobile-money operators, banks, agent
networks, cash workflows, remittance providers, and emerging digital settlement
rails. Existing systems usually optimize one channel. AfriPay optimizes across
channels.

AfriPay is positioned as infrastructure, not only an app. It can power AfriRide
driver earnings, AgroSolidarite farmer payments, merchant checkout, NGO
disbursement, savings groups, escrow, billing, and cross-border remittance.

## Architecture

AfriPay is organized into five layers:

- Financial core: wallet, ledger, transactions, FX, escrow, payouts, billing
- Orchestration: adaptive routing, provider adapters, route execution, failover
- Treasury: provider liquidity pools, reservations, settlement, low-watermark alerts
- Governance and trust: compliance, authority-field rejection, idempotency, audit events
- Experience: mobile app, merchant dashboard, treasury console, developer APIs

## Deterministic Financial Core

The core uses fixed-point money values, explicit currencies, idempotent
references, and double-entry journals. Wallet balances are user-facing state.
Ledger journals are the financial record. This separation prevents client or
provider state from silently redefining financial truth.

Implemented invariants:

- Amounts must be positive.
- Currencies must be supported.
- Ledger entries must balance per currency.
- Payment references must be unique.
- Provider callbacks cannot include authority fields.
- FX conversion requires a locked rate.
- Escrow release requires matching evidence.
- Payout references must be unique.

## Adaptive Multi-Rail Routing

The routing engine scores providers by cost, latency, reliability, and
preference. It can split one payment across multiple rails. A transfer can use
mobile money for instant partial delivery and bank rails for lower-cost
settlement.

The GA Elite+ upgrade makes routing liquidity-aware. Route allocation now
considers:

- provider quote capacity
- treasury liquidity available for the provider and currency
- user preference: balanced, cheapest, fastest, reliable

## Treasury and Liquidity

Treasury is the economic control layer. It tracks provider liquidity pools,
reserved funds, low-watermark alerts, and settlement depletion. Payment
execution now follows:

1. Plan route.
2. Reserve provider liquidity.
3. Execute provider adapter.
4. Settle reservation on success.
5. Release reservation on failure.
6. Emit immutable treasury events.

This prevents mathematically valid routing from becoming economically blind.

## Event Replay and Audit

AfriPay includes an append-only event store with hash chaining and aggregate
replay. This supports debugging, audit reviews, event reconstruction, and
future event-sourced projections.

Events record routing, treasury reservation, settlement, escrow, and payment
completion without granting event consumers authority over ledger truth.

## Compliance and Live Settlement Boundary

The compliance engine applies KYC level checks, party risk scoring, and
jurisdiction-specific review thresholds. Example: AU to BI transfers have a
lower review threshold than generic cross-border flows.

Live settlement is disabled by default through environment config:

- `AFRIPAY_LIVE_SETTLEMENT_ENABLED=false`
- deterministic provider mode is active
- compliance activation reference is required for live settlement

This protects the project legally and operationally while allowing serious
engineering of the financial core.

## Django Persistence

The Django ORM app provides production persistence models for:

- parties and KYC profiles
- wallets and currency accounts
- transactions and payment routes
- ledger accounts, journals, and lines
- FX rates and conversions
- treasury liquidity pools and reservations
- escrow, payouts, subscriptions, invoices
- provider transactions
- event records
- idempotency keys

The persistence service adds row-level locking for idempotency and treasury
reservations using `select_for_update()` inside `transaction.atomic()` blocks.

## Deployment

The deployment pack includes:

- Dockerfile
- local compose stack
- Kubernetes namespace
- API deployment and service
- worker deployment
- Postgres StatefulSet and service
- Redis deployment and service
- config and secret templates

Default deployment keeps live settlement disabled.

## Investor-Grade Differentiation

AfriPay combines the strongest parts of known payment systems:

- Stripe-style developer infrastructure
- PayPal-style wallet abstraction
- M-Pesa-style mobile-money reach
- Western Union-style remittance use case
- AfriTech-style deterministic replay and governance

The strategic advantage is embedded demand from ecosystem use cases: rides,
agriculture, logistics, merchant payments, and community finance.

## Roadmap

Phase 1: deterministic core and persistence

- wallet, ledger, routing, treasury, FX, escrow, payouts, billing
- Django ORM and migration
- Docker and Kubernetes pack
- super app design

Phase 2: API implementation

- REST endpoints
- webhook ingestion
- idempotent request handling
- event replay endpoint

Phase 3: regulated pilot

- sandbox provider adapters
- compliance procedures
- treasury operating runbook
- limited closed-user pilot

Phase 4: live settlement activation

- licensed provider integrations
- monitoring and incident response
- jurisdiction-specific compliance expansion
- external audit

## Conclusion

AfriPay GA Elite is no longer just a planned financial surface. It is now a
governed deterministic financial core with a production path, a safety boundary,
and an architecture capable of becoming financial infrastructure for African
commerce.
