# AfriTech Formal Constitutional Proofs

This directory contains **formal proofs of constitutional properties**
for the AfriTech system, written in **Lean**.

⚠️ IMPORTANT — READ BEFORE EDITING
---------------------------------

Formal proofs in this directory **do not grant authority** to runtime
behavior.

AfriTech’s constitutional legitimacy is enforced by:
- executable constraints
- composite constitutional profiles
- a stateless constitutional gateway
- import-topology confinement
- runtime admissibility enforcement
- CI enforcement

Formal methods come **after** coercive execution topology is frozen.

This directory exists to **prove properties of an already-unavoidable
system**, not to replace executable law with theory.

---

## Scope of Formalization

Formal proofs in this directory are limited to **exactly three properties**:

1. **Invariant Non-Contradiction**  
   No two declared constitutional invariants contradict each other.

2. **Closure Under Legal Transition**  
   If all invariants hold before a legal transition,
   they hold after the transition.

3. **Impossibility of Valid Bypass**  
   No state transition that violates an invariant can be
   constitutionally admissible.

Anything outside this scope does **not** belong here.

---

## Boundary Principle

Formal reasoning begins **only after** the following are true:

- All mutation-capable code is topologically confined
- All mutation flows pass through the constitutional gateway
- All constitutional invariants are executable and enforced
- CI prevents import-level bypass
- Runtime enforces caller admissibility
- Replay determinism is canonicalized

Until these conditions hold, formal proofs are meaningless.

This directory therefore **assumes** executable inevitability
and reasons about its consequences.

---

## Files

### `constitutional_consistency.lean`

Defines:
- abstract constitutional types
- semantic relations (holds, legal, apply)
- the three constitutional theorems
- the boundary axiom linking executable law to formal reasoning

Proofs are intentionally deferred (`sorry`) until topology freezes.

This is **honest incompleteness**, not unfinished work.

---

## Rules for Contributors

- Do NOT add runtime logic here
- Do NOT encode executable behavior in Lean
- Do NOT “prove” topology — topology is enforced by code
- Do NOT remove `sorry` placeholders prematurely
- Do NOT extend scope without architectural approval

Formal proofs must reflect the executable system,
never substitute for it.

---

## Constitutional Ethos

> Law is enforced by execution, not by argument.  
> Proof comes after inevitability, not before.

If this directory ever becomes necessary for correctness,
the architecture has already failed.

It exists to prove that it did not.
``