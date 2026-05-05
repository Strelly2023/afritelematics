# Repository Truth Authority Declaration

This repository contains two historical systems:

## 1. Legacy Kernel (afritech_v1/)
- Integrated runtime + VM + governance + registry system
- Internal consistency-based correctness model
- No longer authoritative for state validity or system truth

## 2. Canonical Kernel (afritech/)
- Layered trust lattice architecture
- Explicit state identity, guards, transition, verification, registry, Merkle commitment, and proof export
- Deterministic and externally verifiable correctness model

# Authority Rule

The authoritative definition of:

- State validity
- State identity
- System correctness
- Trust verification

is defined exclusively by:

> afritech/

# Legacy Status

afritech_v1/ is preserved for reference, migration, and historical traceability only.

It MUST NOT be used as a source of truth for validation, verification, or system correctness.

# Structural Principle

If afritech/ and afritech_v1/ disagree:

> afritech/ is correct by definition of system authority.

# Repository Truth Authority Declaration

This repository contains two historical systems with different truth models.

## 1. Legacy Kernel (`afritech_v1/`)
- Integrated runtime + VM + governance + registry system
- Internal consistency-based correctness model
- Preserved for reference, migration support, and historical traceability
- **Not authoritative** for state validity or system truth

## 2. Canonical Kernel (`afritech/`)
- Layered trust lattice architecture
- Explicit state identity, guards, transitions, verification, registry binding,
  Merkle commitment, and proof export
- Deterministic and externally verifiable correctness model
- **Authoritative source of system truth**

## Authority Rule

The authoritative definition of:
- State identity
- State validity
- System correctness
- Trust verification

is defined exclusively by:

> `afritech/`

## Legacy Status

`afritech_v1/` MUST NOT be used as a source of truth for:
- Validation
- Verification
- Correctness decisions
- Trust or authority assertions

Any disagreement between `afritech/` and `afritech_v1/` is resolved as:

> **`afritech/` is correct by definition of system authority.**

## Structural Principle

Correctness is enforced through explicit, inspectable boundaries.
Semantics are externalized and layered; execution does not interpret meaning.
