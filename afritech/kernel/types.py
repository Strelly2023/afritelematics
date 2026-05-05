"""
AfriTech Kernel Types

This module defines purely declarative kernel types used to
describe structural concepts of the AfriTech system.

These types:
- Carry NO runtime behavior
- Introduce NO executable authority
- Exist to support formal reasoning and future proof binding

Any modification requires ADR → Epoch → Registry reseal.
"""

from __future__ import annotations

from typing import Final


# ---------------------------------------------------------------------
# Kernel type markers
# ---------------------------------------------------------------------

class KernelType:
    """
    Base marker for all kernel-level types.

    This class has no behavior and exists solely as a
    stable reference point for formal semantics.
    """
    pass


class Invariant(KernelType):
    """
    Marker for a kernel invariant.

    Invariants describe properties that must hold across
    all legal system states, independent of execution.
    """
    pass


class Proof(KernelType):
    """
    Marker for a formal proof.

    Proofs are logical artifacts, not executable code.
    """
    pass


class Authority(KernelType):
    """
    Marker for authority classification.

    Authority types are declarative and must not encode
    decision-making logic.
    """
    pass


class Identity(KernelType):
    """
    Marker for identity constructs.

    Identity here is symbolic and constitutional,
    not authentication or runtime identity.
    """
    pass


# ---------------------------------------------------------------------
# Canonical kernel constants (semantic only)
# ---------------------------------------------------------------------

KERNEL_LAYER_NAME: Final[str] = "KERNEL"
KERNEL_LAYER_ROLE: Final[str] = "STRUCTURAL_CONSTRAINTS"
KERNEL_LAYER_MUTABILITY: Final[str] = "IMMUTABLE"


# ---------------------------------------------------------------------
# End of kernel types
# ---------------------------------------------------------------------