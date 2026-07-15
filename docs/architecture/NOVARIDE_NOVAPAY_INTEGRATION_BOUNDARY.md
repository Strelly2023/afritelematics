# NovaRide and NovaPay Integration Boundary

NovaRide stores payment intent, wallet, settlement, payout, refund, and financial product references.

NovaRide must not:
- write ledgers
- execute settlement
- issue payouts
- approve loans
- bind insurance
- mark real payments complete without NovaPay confirmation

Current state: `REAL_PAYMENTS_ENABLED=false`.
