from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from afritech.state.types import (
    KernelHash,
    StateHash,
    EpochId,
    EpochInstanceId,
    TransitionId,
    RegistryState,
    VMState,
    GovernanceState,
)


# ---------------------------------------------------------------------
# Epoch projection (epoch = identity + instance + activation state)
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class EpochContext:
    """
    An epoch is not just an ID; it is an instantiated event.
    """

    id: EpochId
    instance_id: EpochInstanceId
    active: bool

    def __post_init__(self):
        if self.active and not self.instance_id:
            raise ValueError(
                "ACTIVE epoch must have an instance_id"
            )


# ---------------------------------------------------------------------
# Provenance (traceability boundary)
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class Provenance:
    """
    Links this State to its parent and the transition that produced it.
    """

    parent_hash: Optional[StateHash]
    transition_id: Optional[TransitionId]


# ---------------------------------------------------------------------
# Attestation (verification boundary)
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class Attestation:
    """
    Explicit attestation of State validity.
    """

    state_hash: StateHash
    verified: bool


# ---------------------------------------------------------------------
# Canonical GA++++ State
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class State:
    """
    Canonical GA++++ State.

    This is NOT an ontological root.
    It is a governed projection of truth constrained by:
      - constitution
      - guards
      - epochs
      - registry rules

    All transitions produce a NEW State.
    """

    # --- Trust anchor ---
    kernel_hash: KernelHash

    # --- Temporal governance context ---
    epoch: EpochContext

    # --- Governed projections ---
    registry: RegistryState
    vm: VMState
    governance: GovernanceState

    # --- Trace & verification ---
    provenance: Provenance
    attestation: Attestation
