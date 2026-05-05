"""
AfriTech Kernel Core

This module defines the minimal, immutable kernel surface
required for constitutional completeness.

The kernel core provides:
- A semantic anchor for kernel identity
- A stable namespace for future formal binding
- Zero executable authority by itself

IMPORTANT:
- This file is constitutionally IMMUTABLE
- Any modification requires ADR → Epoch → Reseal
- Do NOT import runtime, guards, registry, or IO layers
"""

from __future__ import annotations


# ---------------------------------------------------------------------
# Kernel identity
# ---------------------------------------------------------------------

KERNEL_NAME: str = "afritech.kernel"
KERNEL_ROLE: str = "CONSTITUTIONAL_CORE"
KERNEL_STATUS: str = "IMMUTABLE"


# ---------------------------------------------------------------------
# Kernel versioning (semantic, not executable)
# ---------------------------------------------------------------------

KERNEL_VERSION_MAJOR: int = 1
KERNEL_VERSION_MINOR: int = 0
KERNEL_VERSION_PATCH: int = 0

KERNEL_VERSION: str = (
    f"{KERNEL_VERSION_MAJOR}."
    f"{KERNEL_VERSION_MINOR}."
    f"{KERNEL_VERSION_PATCH}"
)


# ---------------------------------------------------------------------
# Constitutional assertions (documentation-level)
# ---------------------------------------------------------------------

"""
Constitutional assertions:

1. The kernel defines structural constraints, not behavior.
2. The kernel may not depend on runtime, guards, registry, or IO.
3. The kernel must remain stable across epochs unless explicitly evolved.
4. The kernel exists to bound authority, not to exercise it.
"""


# ---------------------------------------------------------------------
# Reserved extension points (NON-EXECUTABLE)
# ---------------------------------------------------------------------

class KernelInvariant:
    """
    Marker class for future formal invariants.

    This class is intentionally empty.
    It exists solely to reserve a stable
    reference point for proof integration.
    """
    pass


class KernelType:
    """
    Marker class for future kernel types.

    No runtime semantics are permitted here.
    """
    pass


# ---------------------------------------------------------------------
# End of kernel core
# ---------------------------------------------------------------------
