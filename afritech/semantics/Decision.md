# afritech/semantics/Decision.md

## Afritech Level 1 — Operational Semantics

### Decision (Canonical Definition)

A **Decision** is a logical admissibility outcome indicating whether a referenced Intent satisfies the conditions required for a valid transition within the Afritech system.

It does not execute.
It does not modify state.
It does not produce a transition.
It does not act.

It only expresses the **result of admissibility evaluation as a logical fact**.

---

## 1. Ontological Role

A Decision is:

- a logical outcome of admissibility conditions
- a structural verdict over an Intent in relation to Proof constraints
- a non-executable semantic marker

It is not:

- a command
- a permission with force
- a state change
- a transition trigger
- a runtime event
- a procedural step

---

## 2. Semantic Constraint

A Decision has no operational effect.

Formally:

- Decision ≠ execution
- Decision ≠ state mutation
- Decision ≠ transition
- Decision ≠ computation
- Decision ≠ authority enactment

A Decision is purely a **logical classification of admissibility**.

---

## 3. Relationship to Intent and Proof (Non-Procedural)

A Decision is defined only in relation to Intent and Proof as follows:

- Intent provides the reference transformation candidate
- Proof provides the admissibility witness structure
- Decision expresses whether admissibility holds

However:

- No ordering is defined
- No pipeline exists
- No temporal interpretation is permitted
- No evaluation sequence is implied

These are **co-dependent semantic objects**, not execution stages.

---

## 4. Non-Generative Principle

A Decision does not generate transitions or states.

If a transition occurs, it is defined exclusively at higher levels (Transition/Epoch semantics), not by Decision itself.

Decision does not cause anything.

---

## 5. Failure Semantics (Explicit Elimination)

A Decision does not fail.

There is no such thing as:

- invalid decision
- rejected decision artifact
- partial decision
- runtime decision error

Non-admissibility is represented as:

> absence of a valid derivable decision condition

not as a system failure.

---

## 6. Identity Principle

Two Decisions are equal if they correspond to the same admissibility evaluation over the same Intent and equivalent Proof conditions.

Identity is structural and logical, not temporal or behavioral.

---

## 7. Level Separation Guarantee

This file strictly prohibits downward semantic leakage.

A Decision does NOT refer to:

- execution
- state
- transition
- runtime evaluation
- system mutation

All such semantics are strictly defined at higher levels.

---

## 8. Canonical Interpretation

A Decision is:

> a logical statement that a transformation is admissible or not, without implying any mechanism by which that transformation is carried out.

---

## 9. Frozen Contract

The following is invariant across all higher levels:

> A Decision is never an operational trigger; it is only a logical admissibility result whose effects are realized exclusively in Transition semantics.

Any interpretation of Decision as execution control, branching mechanism, or runtime authority is invalid within Afritech.