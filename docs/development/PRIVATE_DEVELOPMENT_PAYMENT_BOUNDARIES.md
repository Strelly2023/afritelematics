# Private Development Payment Boundaries

## Boundary Rules

- NovaRide must not execute real payment provider logic.
- NovaPay must not move real money in private development.
- NovaID must remain identity and authentication only.
- NovaTrust evidence is required, but it is simulated in private development.
- NovaAI remains advisory only.

## Supported Simulated Flows

- NovaPay wallet top-up
- send money
- receive money
- cash-in
- cash-out
- merchant QR payment
- refund
- driver payout simulation
- business bulk payment simulation
- NovaRide fare charge simulation

## Enforcement Notes

- live providers are rejected
- real charging is blocked
- payout execution is blocked
- production credentials are rejected
- receipts must label the action as simulated

