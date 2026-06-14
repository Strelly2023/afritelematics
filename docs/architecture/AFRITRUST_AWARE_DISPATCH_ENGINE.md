# ADR-0025 Trust-Aware Dispatch Engine

STATUS: FUTURE GOVERNED SPECIFICATION
CLASSIFICATION: ISOLATED PRODUCT ARCHITECTURE SURFACE
GOVERNANCE MODE: PRESERVE OR ISOLATE

## Claim Discipline Statement

This document defines the Gen-3 trust-aware dispatch specification surface. It does not claim deployment, does not claim authority over truth, and does not expand AfriTech proof boundaries.

Dispatch may influence operational selection only. It may not define replay truth, proof truth, payment truth, or runtime admissibility.

## Related Governance

- ADR: `ADR-0025`
- Rule: `RULE-045`
- Binding: `BIND-023`

## Purpose

Trust-aware dispatch selects the best eligible mobility participant using deterministic evidence-aware scoring.

```text
identity + trust + constraints + route efficiency
    ↓
deterministic ranking
    ↓
replayable decision
    ↓
dispatch evidence
```

## Dispatch Objective

```text
Select the best eligible mobility participant
based on trust, reliability, route efficiency, and constraints,
while preserving replay determinism and governance boundaries.
```

## Core Inputs

- dispatch request
- candidate set from AfriID and trust scoring
- deterministic route context
- declared constraints

## Deterministic Scoring

Dispatch score is computed from deterministic component scores:

- trust score
- reliability score
- route efficiency
- constraint match
- anomaly penalty

The scoring function must not depend on randomness, hidden weights, or mutable external state.

## Invariants

### IA-DISPATCH-001

```text
same inputs -> same dispatch result
```

### IA-DISPATCH-002

```text
higher trust_score cannot be outranked by lower trust_score if the other
variables are equal
```

### IA-DISPATCH-003

```text
dispatch must be explainable from evidence
```

### IA-DISPATCH-004

```text
candidate omission must be detectable
```

### IA-DISPATCH-005

```text
dispatch decision must produce a stable hash
```

### IA-DISPATCH-006

```text
dispatch must not depend on external mutable state
```

## Authority Boundaries

Dispatch may:

- rank eligible candidates
- emit evidence
- contribute to replayable operational traces

Dispatch may not:

- validate proof truth
- define payment truth
- define runtime admissibility
- override replay or proof layers

AI assistance may be used for advisory ranking or operational context, but the final decision must remain deterministic and validator-backed.

## Proof Artifacts

Expected proof artifacts:

- `dispatch_decision.json`
- `dispatch_proof.json`
- `dispatch_decision_proof.json`

## Implementation Expectations

The implementation should provide:

- canonical request and candidate models
- deterministic ranking
- evidence completeness
- validator-safe tests
- proof artifact export
- invariant validation

