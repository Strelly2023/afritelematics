# Repository Truth Authority Declaration

## Canonical Truth Kernel

The authoritative kernel for this repository is:

> afritech/

This designation is machine- and human-binding.

---

## Kernel Definitions

### Canonical System (Authoritative)

Path:
- afritech/

Properties:
- Defines all state identity rules
- Defines validity conditions
- Defines transition semantics
- Defines verification logic
- Defines registry binding rules
- Defines Merkle commitment rules
- Defines proof export semantics

Status:
- ACTIVE
- AUTHORITATIVE
- SOURCE OF TRUTH

---

### Legacy System (Non-Authoritative)

Path:
- afritech_v1/

Properties:
- Historical implementation of runtime-centric system design
- May compute or simulate state internally
- Does NOT define truth, validity, or identity

Status:
- LEGACY
- NON-TRUTH-SOURCE
- READ-ONLY FOR REFERENCE

---

## Global Authority Rule

All of the following concepts are defined exclusively by `afritech/`:

- State identity
- State validity
- System correctness
- Trust verification
- Registry admission
- Proof correctness

Any computation or assertion from `afritech_v1/` is invalid for these purposes.

---

## Conflict Resolution Rule

If `afritech/` and `afritech_v1/` disagree on any of the following:

- state validity
- identity
- registry membership
- verification result

Then the result is resolved deterministically as:

> accept(afritech/) = TRUE  
> accept(afritech_v1/) = FALSE

This rule is non-overridable within this repository.

---

## Structural Principle

Correctness is determined by structural position in the dependency graph, not runtime execution.

Dependency order:

State → Guards → Transition → Verification → Registry → Merkle → Proof

Any system outside this chain is not authoritative for truth.