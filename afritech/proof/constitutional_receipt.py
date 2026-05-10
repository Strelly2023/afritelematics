# afritech/proof/constitutional_receipt.py

"""
AfriTech Constitutional Receipt
===============================

Proof that constitutional law was executed,
not merely that an outcome was produced.

A ConstitutionalReceipt binds:
- executed law
- authority context
- epoch identity
- registry identity
- execution surface identity
- surface admission proof

If an execution has no valid ConstitutionalReceipt,
it is constitutionally NON-EXISTENT.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable, Tuple

from afritech.kernel.constitutional_context import ConstitutionalContext


# ---------------------------------------------------------------------
# CONSTITUTIONAL RECEIPT (IMMUTABLE)
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ConstitutionalReceipt:
    """
    Immutable proof of constitutional law execution.
    """

    # Core identity
    authority_id: str
    epoch_number: int
    registry_hash: str

    # CLOSED-WORLD EXECUTION WITNESSES (I8)
    execution_surface_hash: str
    surface_validation_hash: str

    # Executed law
    invariants_executed: Tuple[str, ...]

    # Receipt identity
    receipt_hash: str

    # -------------------------------------------------------------
    # CONSTRUCTION (CANONICAL)
    # -------------------------------------------------------------

    @staticmethod
    def from_context(
        ctx: ConstitutionalContext,
        *,
        invariants_executed: Iterable[str],
    ) -> "ConstitutionalReceipt":
        """
        Construct a constitutional receipt from an explicit
        ConstitutionalContext and the set of invariants executed.

        Rules:
        - invariants are sorted deterministically
        - surface witnesses are explicitly bound
        - hash composition is stable and replay-safe
        - no field may be inferred or defaulted
        """

        # ---------------------------------------------------------
        # Validate invariants
        # ---------------------------------------------------------

        invariants: Tuple[str, ...] = tuple(sorted(invariants_executed))

        if not invariants:
            raise ValueError(
                "ConstitutionalReceipt requires at least one executed invariant"
            )

        # ---------------------------------------------------------
        # CLOSED-WORLD WITNESS BINDING (I8)
        # ---------------------------------------------------------

        if not ctx.execution_surface_hash:
            raise ValueError(
                "execution_surface_hash missing from ConstitutionalContext"
            )

        execution_surface_hash = ctx.execution_surface_hash

        # For CLOSED_WORLD, validation hash == admitted surface hash
        surface_validation_hash = execution_surface_hash

        # ---------------------------------------------------------
        # HASH COMPOSITION (CANONICAL)
        # ---------------------------------------------------------

        payload = "|".join(
            (
                ctx.authority_id,
                str(ctx.epoch.number),
                ctx.registry_hash,
                execution_surface_hash,
                surface_validation_hash,
                ",".join(invariants),
            )
        ).encode("utf-8")

        receipt_hash = sha256(payload).hexdigest()

        return ConstitutionalReceipt(
            authority_id=ctx.authority_id,
            epoch_number=ctx.epoch.number,
            registry_hash=ctx.registry_hash,
            execution_surface_hash=execution_surface_hash,
            surface_validation_hash=surface_validation_hash,
            invariants_executed=invariants,
            receipt_hash=receipt_hash,
        )