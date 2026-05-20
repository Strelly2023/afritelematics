# ADR-0001: Five-Invariant Contract

STATUS: PROVEN GOVERNANCE

## Decision

AfriTech/AfriRide is governed by the five-invariant contract.

Every change must preserve:

- proof meaning
- authority boundaries
- AfriRide scope
- claim discipline
- enforcement integrity

## Operating Law

```text
preserve or isolate
```

- Protected-surface work must preserve the sealed core exactly.
- External work must remain fully decoupled from protected truth and enforcement surfaces.
- Mixed or ambiguous work is drift.

## Authority Model

```text
Proof defines truth
Core decides
API exposes
Polling confirms
WebSockets notify
Apps display
```

## Behavioral Constraint

```text
event -> trigger poll -> update UI from confirmed state
```

## Consequences

- A change that weakens enforcement is drift.
- A change that bypasses constitutional validation is drift.
- A change that introduces exceptions to the four-gate validator is drift.
- A change that alters proof meaning is drift.
- A change that couples external product code to protected proof, invariant,
  or enforcement surfaces is drift.

## Non-Authority

This ADR records the existing contract. It does not define new proof meaning,
new execution semantics, or new system claims.
