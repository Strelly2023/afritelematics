# NovaPay Global Treasury Intelligence

## Purpose

NovaPay Global Treasury Intelligence is an advisory control surface for multi-currency treasury optimization and on-chain proof planning.

It evaluates:

- treasury liquidity
- FX exposure
- currency distribution
- stable reserve posture
- on-chain anchor batch plans

It does not move funds or submit blockchain transactions.

## API Surfaces

- `GET /v1/treasury/intelligence`
- `GET /v1/treasury/global-intelligence`

## Operating Rules

- Currency conversion recommendations SHALL remain policy-gated.
- On-chain proof plans SHALL remain advisory until explicitly executed by a governed chain worker.
- Treasury AI SHALL not bypass NovaPower.
- High-risk FX or liquidity outcomes SHALL require human review.
