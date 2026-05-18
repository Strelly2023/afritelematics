# AfriTech Formal Security Surface

Status: IMPLEMENTED

This document binds formal security claims to the executable
constitutional validators. Security in AfriTech is defined as
closed-world execution, deterministic replay, canonical identity,
admissibility gating, and proof-bound receipts.

Authoritative validators:

- `afritech.ci.constitutional_validation`
- `afritech.ci.level2_formal_model_validator`
- `afritech.ci.formal_runtime_equivalence_validator`
- `afritech.ci.surface_state_resolution_validator`

Any security claim outside those declared surfaces is non-admissible.
