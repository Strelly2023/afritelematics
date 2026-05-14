# Replay Determinism — Phase 2 Boundary (Structural)

## Layer Separation

The system is now divided into three explicit layers:

- Phase 1: Execution authority  
  Deterministic execution and replay invariants  
  (fixed, enforced, immutable)

- Phase 2a: Representational space  
  Possible forms of intent and state  
  (expanding, not yet constrained)

- Phase 2b: Equivalence space  
  Relationships between intents (e.g. duplicate, equivalent)  
  (declarative, not operational)

---

## Invariant

Execution is fixed.

Representation and equivalence may expand.

No semantic binding occurs without explicit selection.

---

## Status

- No enforcement introduced
- No runtime behavior modified
- No equivalence rules selected
``
REPLAY_DETERMINISM_PHASE_1.md
→ what must never be violated (constraints)

REPLAY_DETERMINISM_PHASE_2_SCOPE.md
→ what ambiguity is allowed to exist (scope)

REPLAY_DETERMINISM_PHASE_2_BOUNDARY.md
→ how layers are prevented from collapsing (structure)