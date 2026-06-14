# AfriPay Super App Design

## Product Position

AfriPay Super App is the user and operator surface for the AfriPay Financial
Operating System. It exposes wallet, remittance, merchant, escrow, payout,
liquidity, and compliance workflows without giving the client authority over
ledger truth.

## Primary Surfaces

### Mobile App

- Personal wallet with multi-currency balances
- Send money with route preview and fee breakdown
- Receive money by QR, phone, account, or agent code
- Escrow payment for rides, marketplace trades, and farmer contracts
- Community wallet for savings groups
- Offline fallback queue for USSD/SMS-assisted flows
- KYC status and document capture
- Assistant view for liquidity and balance warnings

### Merchant Dashboard

- Payment links and QR checkout
- Revenue analytics
- Subscription and invoice management
- Settlement routes and provider status
- Refund and dispute queue
- Escrow release evidence review
- Staff roles and audit log

### Treasury Console

- Provider liquidity pools by country and currency
- Low-watermark alerts
- Reservation, release, and settlement timeline
- FX lock inventory
- Route success and latency analytics
- Compliance review queue
- Live-settlement activation gate

### Developer Portal

- API keys and webhook endpoints
- Idempotency-key inspector
- Event replay explorer
- Provider adapter sandbox
- Test wallet and simulated route console

## Navigation Model

Mobile tabs:

- Home
- Send
- Wallets
- Activity
- Profile

Dashboard sections:

- Overview
- Payments
- Wallets
- Escrow
- Payouts
- Billing
- Treasury
- Compliance
- Developers

## Core Workflows

### Cross-Border Send

1. User enters recipient and amount.
2. App requests a quote.
3. Backend returns split routes, FX lock, fees, and expected timing.
4. User confirms.
5. Backend creates idempotent transaction, reserves treasury liquidity, sends via providers, posts journal, and emits events.
6. App displays receipt from backend event and ledger references.

### Escrow Payment

1. Buyer selects escrow payment.
2. Backend locks funds and creates release condition.
3. Evidence arrives from AfriRide, marketplace delivery, or farmer contract.
4. Escrow service releases or refunds based on evidence match.

### Bulk Farmer Payout

1. Cooperative uploads payout recipients.
2. Backend validates unique references and shared currency.
3. Treasury checks liquidity.
4. Payout batch is processed route by route.
5. Dashboard displays successes, failures, and retry-safe references.

## UI Principles

- Financial truth comes from backend receipts, not client state.
- Every payment state must show reference, amount, currency, route, and status.
- Risk and compliance blocks must be explicit and non-ambiguous.
- Offline states must show queued, submitted, confirmed, or failed.
- Treasury and compliance surfaces favor dense tables, filters, and audit trails.

## API Surface Required

- `POST /afripay/payments`
- `GET /afripay/payments/{reference}`
- `POST /afripay/fx/quote`
- `GET /afripay/wallets/{wallet_id}`
- `POST /afripay/escrows`
- `POST /afripay/escrows/{escrow_id}/release`
- `POST /afripay/payouts`
- `GET /afripay/treasury/pools`
- `GET /afripay/events/{aggregate_id}`
- `POST /afripay/webhooks/{provider}`

## MVP Build Order

1. Mobile wallet and send flow
2. Merchant payments dashboard
3. Treasury console
4. Compliance review queue
5. Developer sandbox
