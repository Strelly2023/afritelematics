# afritech/kernel/constitutional_context.py

"""
AfriTech Constitutional Context
===============================

Canonical, immutable constitutional execution context.

This object is the SINGLE carrier of constitutional facts
for any execution, transition, reseal, or replay validation.

CRITICAL RULES:
- This object is immutable
- This object is explicitly constructed
- This object is never inferred
- This object is passed explicitly through all constitutional gateways
- This object MUST be included in constitutional receipts

If execution occurs without a ConstitutionalContext,
it is constitutionally invalid by definition.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from afritech.epoch.epoch_snapshot import EpochSnapshot


# ---------------------------------------------------------------------
# CONSTITUTIONAL CONTEXT (IMMUTABLE FACT CARRIER)
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ConstitutionalContext:
    """
    Immutable constitutional execution context.

    This object binds execution to:
    - declared authority
    - constitutional epoch
    - registry identity
    - execution surface identity
    - causal trace (optional at admission, mandatory post-execution)

    This object contains NO behavior.
    It is constitutional fact, not policy.
    """

    # -------------------------------------------------------------
    # AUTHORITY BINDING
    # -------------------------------------------------------------

    authority_id: str
    """
    Canonical authority identifier under which execution occurs.

    MUST:
    - be explicitly declared
    - match exactly one registered authority profile
    - never be inferred, derived, or escalated
    """

    # -------------------------------------------------------------
    # TEMPORAL BINDING
    # -------------------------------------------------------------

    epoch: EpochSnapshot
    """
    Normalized constitutional epoch snapshot.

    This is the ONLY epoch representation permitted inside
    constitutional enforcement logic.
    """

    # -------------------------------------------------------------
    # IDENTITY BINDINGS
    # -------------------------------------------------------------

    registry_hash: str
    """
    Canonical hash of the constitutionally sealed registry.

    Binds execution to a specific constitutional identity.
    """

    execution_surface_hash: str
    """
    Canonical hash of the admitted execution surfaces.

    Enforces closed-world execution.
    """

    # -------------------------------------------------------------
    # TRACE / CAUSALITY
    # -------------------------------------------------------------

    trace_root: Optional[str] = None
    """
    Canonical root hash of the execution trace.

    Rules:
    - MAY be None during runtime admission
    - MUST be populated after execution
    - MUST be present for replay validation
    """

    # -------------------------------------------------------------
    # STRUCTURAL SANITY (NOT LAW)
    # -------------------------------------------------------------

    def __post_init__(self) -> None:
        """
        Enforce minimal structural sanity.

        IMPORTANT:
        These checks are NOT constitutional law.
        They only prevent malformed contexts.

        All substantive constitutional invariants
        are enforced by constitutional profiles.
        """

        # Authority must be explicit
        if not isinstance(self.authority_id, str) or not self.authority_id:
            raise ValueError(
                "ConstitutionalContext requires explicit non-empty authority_id"
            )

        # Epoch must be normalized
        if not isinstance(self.epoch, EpochSnapshot):
            raise ValueError(
                "ConstitutionalContext.epoch must be an EpochSnapshot"
            )

        # Registry identity must be explicit
        if not isinstance(self.registry_hash, str) or not self.registry_hash:
            raise ValueError(
                "ConstitutionalContext requires non-empty registry_hash"
            )

        # Execution surface identity must be explicit
        if not isinstance(self.execution_surface_hash, str) or not self.execution_surface_hash:
            raise ValueError(
                "ConstitutionalContext requires non-empty execution_surface_hash"
            )

        # Trace root, if present, must be a string
        if self.trace_root is not None and not isinstance(self.trace_root, str):
            raise ValueError(
                "ConstitutionalContext.trace_root must be str or None"
            )
