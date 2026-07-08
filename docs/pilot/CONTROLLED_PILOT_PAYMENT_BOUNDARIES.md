# Controlled Pilot Payment Boundaries

Controlled Pilot keeps financial execution constrained.

## Allowed by default

- Simulated wallet top-up.
- Simulated send and receive flows.
- Simulated merchant QR payments.
- Simulated driver payouts.
- Simulated business payroll and approvals.
- Cash only through the documented pilot cash procedure.

## Blocked by default

- Live charging.
- External payouts.
- Production payment credentials.
- Public launch claims.
- General availability claims.

## Real-payment exception

Real payments are allowed only when `docs/pilot/PILOT_PAYMENT_APPROVAL.json` exists, is valid, and explicitly grants `real_payments_approved=true` for controlled pilot scope.
