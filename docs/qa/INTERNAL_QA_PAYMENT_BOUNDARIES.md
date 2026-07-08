# Internal QA Payment Boundaries

Internal QA uses simulated ledger activity only.

## Allowed
- Simulated wallet top-up
- Simulated send and receive
- Simulated cash-in and cash-out
- Simulated merchant QR payment
- Simulated refunds and disputes
- Sandbox provider responses

## Blocked
- Live card capture
- External payout execution
- Production provider credentials
- Production settlement claims
- Real customer fund movement

## Enforcement
- Receipts must flag simulated payment activity
- Provider calls must remain local or sandboxed
- NovaRide cannot execute payment-provider logic directly
- Cash remains a QA ledger concept unless controlled pilot enables a separate cash procedure
