# ADR-0029: Federated Mobility Infrastructure

## Status

Accepted

## Purpose

The Federated Mobility Infrastructure enables multiple independent mobility
networks, fleets, merchants, and institutions to cooperate under shared
evidence and trust constraints without centralizing authority.

## System Position

```text
AfriID
  ↓
Local Trust Network
  ↓
Federation Layer
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

- admit verified participants into federated trust domains
- keep local trust and federated trust bounded and explainable
- preserve identity uniqueness across networks
- make cross-network handoffs replayable and auditable
- expose proof-ready federation state for external evidence surfaces

## Non-Responsibilities

- the federation layer does not become proof authority
- it does not override dispatch proof or custody proof
- it does not execute payment authority
- it does not centralize trust outside the governed state

## Trust Model

- local trust is the source of truth for a participant's history
- federated trust is a bounded projection used for cross-network selection
- federated trust must be deterministic and replayable

## Evidence Surface

- federation_state.json
- federation_proof.json

## Governance Boundary

This ADR introduces federation only. It does not alter AfriTech proof authority,
replay authority, or economic settlement authority.
