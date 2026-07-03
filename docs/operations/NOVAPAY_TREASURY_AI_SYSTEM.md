# NovaPay Treasury AI System

## Purpose

NovaPay Treasury AI is an advisory-only control layer that evaluates the current treasury snapshot and produces liquidity, reserve, and capital-allocation recommendations.

It does not move money, call banks directly, or bypass NovaPower policy controls.

## Inputs

- `/v1/treasury/snapshot`
- liquidity positions
- prefunding accounts
- settlement exposures
- ledger checkpoint and reconciliation status

## Outputs

- liquidity ratio
- reserve headroom
- prefunding gap
- risk level
- treasury decision
- provider recommendations
- stress-test scenarios

## API Surfaces

- `GET /v1/treasury/snapshot`
- `GET /v1/treasury/intelligence`

## Operating Rules

- Treasury AI SHALL remain advisory only.
- All capital movements SHALL remain policy-gated by NovaPower.
- All settlement actions SHALL remain auditable and replayable.
- High-risk treasury outcomes SHALL require human review.
