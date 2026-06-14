# ADR-0028: Federated Mobility Trust Network

## Status

Accepted

## Purpose

The Federated Mobility Trust Network is a deterministic, evidence-backed trust layer for the Gen-3 mobility stack.
It accumulates trust signals from verified dispatch, custody, settlement, anomaly, and dispute outcomes.

The trust network influences dispatch and federation decisions, but it does not become truth authority.

## System Position

```text
AfriID
  ↓
Federated Mobility Trust Network
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

- maintain deterministic trust profiles for mobility participants
- derive trust only from verified operational evidence
- keep event history replayable and explainable
- expose a canonical proof artifact for external audit surfaces
- feed updated trust into dispatch as an input, not as authority

## Non-Responsibilities

- the trust network does not approve or reject proof
- the trust network does not execute payments
- the trust network does not alter replay authority
- the trust network does not override admissibility decisions

## Trust Inputs

- successful deliveries and completed operations
- custody integrity and handoff continuity
- settlement completion and dispute outcomes
- anomaly detection and trust degradation events
- verified evidence linkage from governed operations

## Invariants

- Same verified event sequence produces the same trust score.
- Trust stays within bounded limits.
- Tampering with event history changes trust state.
- Trust is derived only from verified operations.
- Trust does not become a new authority surface.

## Proof Surface

- trust_profile.json
- trust_profile_proof.json

## Governance Boundary

This ADR introduces a governed trust model only. It does not redefine proof semantics,
runtime authority, settlement authority, or replay authority.
