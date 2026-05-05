# afritech/semantics/Intent.md

## Afritech Level 1 — Operational Semantics

### Intent (Canonical Definition)

An **Intent** is a syntactic declaration that identifies a requested possible action within the Afritech system.

It does not execute.
It does not authorize.
It does not imply admissibility.

It only establishes that:

> “A transformation or operation is being referred to for evaluation.”

---

## 1. Ontological Role

An Intent is:

- a reference to a potential transformation
- a pre-structural semantic marker
- a non-executable expression

It is not:

- an action
- a decision
- a proof
- a state change
- a command with authority

---

## 2. Semantic Constraint

An Intent carries no validity, proof, or decision content.

Formally:

- Intent ≠ permission
- Intent ≠ execution
- Intent ≠ proof
- Intent ≠ decision

It is only a *candidate reference to a transformation*.

---

## 3. Admissibility Relationship (Deferred)

An Intent may participate in a **later admissibility structure**, in which proof and decision are jointly required for any transition to exist.

Conceptually:

Intent is evaluated together with:
- Proof (precondition witness)
- Decision (derivation outcome)
- Transition (resulting state relation)

However:

- No ordering is defined at Level 1
- No sequencing is implied
- No inference is permitted at this level
- All admissibility structure is external to Intent

Intent remains logically inert with respect to system evolution.

---

## 4. Failure Semantics (Explicit Elimination)

An Intent does not admit failure.

There is no notion of:

- rejected intent
- invalid intent state
- failed intent execution

Non-admissibility corresponds to:

> non-existence of a valid derivation structure

not a runtime failure.

---

## 5. Identity Principle

Two Intents are equal iff they denote the same abstract requested transformation.

This identity is structural, not behavioral.

No context or execution state affects identity at this level.

---

## 6. Level Separation Guarantee

This file enforces:

- No reference to Proof
- No reference to Decision
- No reference to State
- No reference to Transition
- No reference to Execution semantics

Any such constructs belong exclusively to higher levels.

---

## 7. Canonical Interpretation

An Intent is:

> a pure declaration of a candidate transformation,
> without any commitment to its realizability.

---

## 8. Frozen Contract

The following is immutable across all higher levels:

> An Intent has no operational consequence within Level 1.

All admissibility, execution, and state evolution semantics arise strictly outside this layer.