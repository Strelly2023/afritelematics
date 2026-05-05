from __future__ import annotations

from afritech.state.state import State
from afritech.guards.engine import GuardResult, Guard


# ---------------------------------------------------------------------
# Guard: Kernel hash must not change
# ---------------------------------------------------------------------

def kernel_hash_immutable(state: State, transition) -> GuardResult:
    candidate = transition(state)

    if candidate.kernel_hash != state.kernel_hash:
        return GuardResult(False, "KERNEL_HASH_IMMUTABLE")

    return GuardResult(True)


# ---------------------------------------------------------------------
# Guard: Provenance must not be pre-modified by transition
# ---------------------------------------------------------------------

def forbid_provenance_override(state: State, transition) -> GuardResult:
    candidate = transition(state)

    if candidate.provenance != state.provenance:
        return GuardResult(False, "PROVENANCE_OVERRIDE_FORBIDDEN")

    return GuardResult(True)


# ---------------------------------------------------------------------
# Guard: Attestation must not be pre-set as verified
# ---------------------------------------------------------------------

def forbid_preverified_attestation(state: State, transition) -> GuardResult:
    candidate = transition(state)

    if candidate.attestation.verified:
        return GuardResult(False, "PREVERIFIED_ATTESTATION_FORBIDDEN")

    return GuardResult(True)


# ---------------------------------------------------------------------
# Export invariant guards
# ---------------------------------------------------------------------

INVARIANT_GUARDS: tuple[Guard, ...] = (
    kernel_hash_immutable,
    forbid_provenance_override,
    forbid_preverified_attestation,
)