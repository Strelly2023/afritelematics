# ADR-0027 Settlement Boundary

STATUS: FUTURE GOVERNED SPECIFICATION
CLASSIFICATION: ISOLATED PRODUCT ARCHITECTURE SURFACE
GOVERNANCE MODE: PRESERVE OR ISOLATE

## Claim Discipline Statement

This document defines the Gen-3 settlement boundary for AfriRide mobility operations. It does not claim payment authority, live settlement authority, proof authority, or runtime authority.

Settlement is an economic consequence of verified execution. It is not truth.

## Related Governance

- ADR: `ADR-0027`
- Rule: `RULE-047`
- Binding: `BIND-025`

## Purpose

Record and validate economic outcomes based strictly on replayable, evidence-backed operations.

```text
identity
  ↓
dispatch
  ↓
custody
  ↓
settlement
  ↓
trust update
```

## Core Data Model

### SettlementRecord

```text
settlement_id
operation_id
dispatch_hash
chain_hash
participants
amounts
gross_amount
currency
status
events
settlement_hash
```

### SettlementEvent

```text
event_id
timestamp
actor
action
evidence_hash
```

## Status Lifecycle

```text
PENDING -> ELIGIBLE -> SETTLED -> DISPUTED
```

## Invariants

### IA-SETTLEMENT-001

```text
settlement must map to a valid custody chain
```

### IA-SETTLEMENT-002

```text
settlement must be deterministic
```

### IA-SETTLEMENT-003

```text
settlement must reflect custody outcome
```

### IA-SETTLEMENT-004

```text
tampering with input must change settlement hash
```

### IA-SETTLEMENT-005

```text
settlement must not depend on external mutable state
```

### IA-SETTLEMENT-006

```text
settlement must be explainable from evidence
```

## Authority Boundaries

Settlement may:

- compute deterministic economic splits
- record eligibility and settlement evidence
- support replayable audit traces

Settlement may not:

- define proof truth
- define replay truth
- define custody truth
- define payment execution authority
- override AfriPay settlement gating

AfriPay may execute a settlement instruction only after governed validation. AfriPay does not decide whether the settlement is true.

## Proof Artifacts

Expected proof artifacts:

- `settlement_record.json`
- `settlement_proof.json`

## Implementation Expectations

The implementation should provide:

- deterministic split computation
- gross and split integrity checks
- evidence-linked settlement records
- validator-safe tests
- proof artifact export
- invariant validation

