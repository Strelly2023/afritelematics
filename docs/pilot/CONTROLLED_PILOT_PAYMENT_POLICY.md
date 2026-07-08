# Controlled Pilot Payment Policy

Controlled pilot payments are simulated and sandbox-only by default.

Rules:
- `payment_mode = SIMULATED_AND_SANDBOX`
- live payments are disabled
- real charging is disabled
- external payouts are disabled
- cash is recorded as a controlled-pilot ledger procedure only
- NovaRide must not execute payment provider logic
- NovaPay owns payment execution
- NovaTrust evidence is required for financial activity

The pilot may test card, wallet, QR, cash-in, cash-out, and fare settlement flows without live transfer execution.
