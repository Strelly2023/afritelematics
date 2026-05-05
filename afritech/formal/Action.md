# afritech/formal/Action.md

## Afritech Level 2 — Formal System

### Action Space Definition

The action space is defined as a primitive abstract set:

\[
A
\]

where:

- \(A\) is a non-empty set of abstract actions
- Each element \(a \in A\) represents a potential system request abstraction
- No internal structure of elements of \(A\) is assumed at this level

---

## 1. Ontological Status

An action is a formal object representing a *potential interaction with the system*.

An action is not:
- an execution
- a command
- a runtime event
- a state modification

An action is:

> a syntactic placeholder for a possible admissibility evaluation.

---

## 2. Identity Principle

Action equality is strict identity in the set \(A\):

For \(a_1, a_2 \in A\),

\[
a_1 = a_2
\]

means:
- they are the same element of \(A\)
- no weaker equivalence notion exists at Level 2

No notions of:
- semantic equivalence
- behavioral equivalence
- contextual equivalence

are defined.

---

## 3. Structural Inertness

Actions do not execute, trigger, or evaluate.

An action has no causal power.

All effects are mediated externally through relations:

\[
Relation \subseteq S \times A \times S
\]

(defined formally in Transition.md)

---

## 4. Isolation Principle

Actions are independent of:

- States \(S\)
- Proof system \( \Pi \)
- Governance relation \( \vdash \)
- Security constraints \( \blacklozenge \)
- Epoch ordering \( \Delta_{epoch} \)

These systems operate on actions but are not contained within them.

---

## 5. Admissibility (Non-Primitive Concept)

There is no intrinsic predicate:

\[
Admissible(a)
\]

Instead:

> An action is meaningful only through its participation in the global transition relation.

Formally, admissibility is relational:

\[
\exists s, s' \in S : Transition(s, a, s')
\]

(defined formally in Transition.md)

---

## 6. Non-Execution Principle

Actions do not execute.

There is:
- no runtime invocation
- no evaluation semantics
- no side effects

Actions are purely abstract elements of \(A\).

---

## 7. Relationship to Other Components

| Component | Relationship to Action |
|-----------|------------------------|
| Intent | Level 1 semantic origin of action |
| Proof | witness enabling admissibility |
| Decision | derivability constraint over action |
| State | domain and codomain of transitions |
| Transition | relation involving actions |
| Epoch | ordering of transitions involving actions |
| Failure | absence of admissible relation |

---

## 8. Role in System Definition

The action space is part of the system tuple:

\[
\mathbf{AFRITECH} = (S, A, \Pi, \vdash, \blacklozenge, \Delta_{epoch})
\]

All system evolution is expressed via relations involving \(A\), not computation inside \(A\).

---

## 9. Core Invariant (Frozen)

> An action has no semantics except those induced by its participation in admissible transitions between states.

---

## 10. Summary

- \(A\) is a primitive abstract set of actions
- actions are structureless and inert
- no execution or computation exists in actions
- all meaning is relational via transitions
- admissibility is external, not intrinsic

---