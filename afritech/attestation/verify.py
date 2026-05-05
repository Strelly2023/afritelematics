from __future__ import annotations

from afritech.state.state import State
from afritech.state.equality import compute_state_hash_pre_attestation


def verify_state(state: State) -> State:
    """
    Verify a State and return a new State with verified attestation.

    Guarantees:
    - hash is computed without self-reference
    - verified=True is explicit
    - input State is not mutated
    """

    expected_hash = compute_state_hash_pre_attestation(state)

    if state.attestation.state_hash != expected_hash:
        raise ValueError("STATE_HASH_MISMATCH")

    return State(
        kernel_hash=state.kernel_hash,
        epoch=state.epoch,
        registry=state.registry,
        vm=state.vm,
        governance=state.governance,
        provenance=state.provenance,
        attestation=type(state.attestation)(
            state_hash=state.attestation.state_hash,
            verified=True,
        ),
    )