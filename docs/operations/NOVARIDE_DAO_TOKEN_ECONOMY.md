# NovaRide DAO Token Economy

## Purpose

NovaRide DAO Token Economy is an advisory protocol layer that models token incentives, proposal governance, treasury allocation, and on-chain proof planning.

It does not mint tokens, move treasury assets, or override NovaPower policy.

## API Surface

- `GET /v1/economy/protocol`

## Model Outputs

- NovaToken supply and circulation posture
- governance participation and proposal queue
- treasury allocation plan
- on-chain batch plan for proposal and treasury proofs

## Operating Rules

- Token economics SHALL remain advisory until a governed execution layer approves it.
- Governance proposals SHALL be routed through policy and replay controls.
- Treasury allocations SHALL remain policy-gated.
- On-chain proof planning SHALL not become direct execution authority.
