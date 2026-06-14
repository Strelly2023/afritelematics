# ADR-0026 Logistics Custody Chain

STATUS: FUTURE GOVERNED SPECIFICATION
CLASSIFICATION: ISOLATED PRODUCT ARCHITECTURE SURFACE
GOVERNANCE MODE: PRESERVE OR ISOLATE

## Claim Discipline Statement

This document defines a deterministic chain-of-custody model for Gen-3 logistics and multi-hop mobility surfaces. It does not claim production logistics deployment, does not define proof truth, and does not expand constitutional authority.

Custody is a governed product surface. It can produce evidence, but it does not become the truth authority.

## Related Governance

- ADR: `ADR-0026`
- Rule: `RULE-046`
- Binding: `BIND-024`

## Purpose

Maintain a deterministic, replayable, verifiable chain of custody for any asset across multiple participants and handoffs.

```text
asset
  ↓
custody step
  ↓
explicit handoff
  ↓
replayable evidence
  ↓
chain hash
```

## Asset Types

- person
- package
- food
- medicine
- document
- freight

## Core Data Model

### CustodyStep

```text
step_id
from_participant
to_participant
location
timestamp
condition
evidence_hash
```

### CustodyChain

```text
chain_id
operation_id
asset_type
custody_steps
chain_hash
```

## Invariants

### IA-CUSTODY-001

```text
custody must always be continuous
```

### IA-CUSTODY-002

```text
every step must have exactly one owner
```

### IA-CUSTODY-003

```text
chain must be replayable deterministically
```

### IA-CUSTODY-004

```text
tampering with any step must change the chain hash
```

### IA-CUSTODY-005

```text
missing handoff must be detectable
```

### IA-CUSTODY-006

```text
custody transfer must be explicitly recorded
```

## Authority Boundaries

Custody may:

- record explicit handoffs
- attach evidence to each transition
- support replay reconstruction

Custody may not:

- create implicit transitions
- skip steps
- infer ownership without evidence
- define truth authority for proof, settlement, or runtime admissibility

## Proof Artifacts

Expected proof artifacts:

- `custody_chain.json`
- `custody_proof.json`

## Implementation Expectations

The implementation should provide:

- immutable custody steps
- canonical serialization
- hash-chained transitions
- validator-safe tests
- proof-ready export
- invariant validation

