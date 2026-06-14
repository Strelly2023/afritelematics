# ADR-0030: Mobility Market Governance

## Status

Accepted

## Purpose

Mobility Market Governance defines deterministic, evidence-aware rules for
supply-demand balancing, pricing, incentives, and allocation fairness across
the federated mobility network.

The market layer influences execution behavior, but it does not become truth
authority, proof authority, identity authority, or trust authority.

## System Position

```text
AfriID
  ↓
Local Trust Network
  ↓
Federation Layer
  ↓
Mobility Market Governance
  ↓
Trust-aware Dispatch
  ↓
Custody Chain
  ↓
Settlement Boundary
  ↓
Trust Update
```

## Core Responsibilities

- compute deterministic market prices from supply, demand, and policy signals
- emit incentive plans that can be replayed and audited
- rebalance dispatch bias over time to reduce monopolization
- preserve fairness across participants and networks
- produce proof-ready market decisions and evidence bundles

## Non-Responsibilities

- the market layer does not select a winner directly
- it does not redefine truth, proof, identity, or trust
- it does not override dispatch, custody, or settlement evidence
- it does not centralize economic authority outside the governed state

## Invariants

- Same inputs produce the same price.
- Supply-demand balance is enforced deterministically.
- Incentives are evidence-backed and replayable.
- Allocation remains balanced over time.
- Market rules are transparent and hash-stable.
- Market decisions do not override proof authority.

## Proof Surface

- market_state.json
- market_decision_proof.json

## Governance Boundary

This ADR adds market governance only. It remains isolated from AfriTech proof
truth and does not grant new authority to pricing, dispatch, or settlement.
