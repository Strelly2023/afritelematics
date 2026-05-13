# Replay Determinism — Phase 2 Scope (Declared)

## Scope Expansion

This phase intentionally expands the ambiguity surface to include:

- Intent repetition (duplicate commands)
- Intent equivalence (structurally or semantically identical commands)
- Failure-mode taxonomy (explicit classification of admissibility failure)

---

## Out of Scope

The following remain explicitly out of scope:

- Time
- Retries with delay
- Persistence
- Distributed execution
- Replay surface expansion

---

## Status

No semantics have been selected.

No execution behavior has been modified.

This file declares only the ambiguity classes to be explored.

git add afritech/internal/REPLAY_DETERMINISM_PHASE_2_SCOPE.md
git commit -m "Declare replay determinism phase 2 scope"