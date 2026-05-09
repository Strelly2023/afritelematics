# afritech/guards/invariants.py

"""
Functional invariant guards for state-level validation

Design:
- PURE functions (no side effects)
- Deterministic
- Return GuardResult ONLY (no fail())
- Enforcement handled externally
"""

from typing import Callable

from afritech.guards.guard_core import GuardResult


# -------------------------------------------------------------
# Kernel hash invariant
# -------------------------------------------------------------

def kernel_hash_immutable(state, transition) -> GuardResult:

    candidate = transition(state)

    if not hasattr(state, "kernel_hash") or not hasattr(candidate, "kernel_hash"):
        return GuardResult(False, "INVALID_KERNEL_HASH_STRUCTURE")

    if candidate.kernel_hash != state.kernel_hash:
        return GuardResult(False, "KERNEL_HASH_IMMUTABLE")

    return GuardResult(True)


# -------------------------------------------------------------
# Provenance invariant
# -------------------------------------------------------------

def forbid_provenance_override(state, transition) -> GuardResult:

    candidate = transition(state)

    if not hasattr(state, "provenance") or not hasattr(candidate, "provenance"):
        return GuardResult(False, "INVALID_PROVENANCE_STRUCTURE")

    if candidate.provenance != state.provenance:
        return GuardResult(False, "PROVENANCE_OVERRIDE_FORBIDDEN")

    return GuardResult(True)


# -------------------------------------------------------------
# Attestation invariant
# -------------------------------------------------------------

def forbid_preverified_attestation(state, transition) -> GuardResult:

    candidate = transition(state)

    if not hasattr(candidate, "attestation"):
        return GuardResult(False, "INVALID_ATTESTATION_STRUCTURE")

    if not hasattr(candidate.attestation, "verified"):
        return GuardResult(False, "INVALID_ATTESTATION_FIELD")

    if candidate.attestation.verified:
        return GuardResult(False, "PREVERIFIED_ATTESTATION_FORBIDDEN")

    return GuardResult(True)


# -------------------------------------------------------------
# Export invariant guards
# -------------------------------------------------------------

INVARIANT_GUARDS = (
    kernel_hash_immutable,
    forbid_provenance_override,
    forbid_preverified_attestation,
)