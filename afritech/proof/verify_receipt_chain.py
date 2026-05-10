# afritech/proof/verify_receipt_chain.py

"""
AfriTech Constitutional Receipt Chain Verifier
==============================================

This module verifies the FULL constitutional receipt chain:

    Receipt
        → Epoch Snapshot
            → Registry Attestation
                → Registry State

RULE (HARD LAW):
If the receipt chain is broken, execution is constitutionally NON-EXISTENT.

This verifier is:
- Read-only
- Deterministic
- Fail-closed
- Non-authoritative
- Observer-free

It MUST NOT:
- mutate state
- repair history
- infer missing evidence
"""

from __future__ import annotations

from typing import Iterable

from afritech.epoch.epoch_snapshot import EpochSnapshot
from afritech.proof.constitutional_receipt import ConstitutionalReceipt


# ---------------------------------------------------------------------
# FAILURE TYPE
# ---------------------------------------------------------------------

class ReceiptChainViolation(RuntimeError):
    """Raised when the constitutional receipt chain is invalid."""
    pass


# ---------------------------------------------------------------------
# CORE VERIFICATION
# ---------------------------------------------------------------------

def verify_receipt_chain(
    *,
    registry: dict,
    attestation: object,
    epoch_history: Iterable[EpochSnapshot],
    receipts: Iterable[ConstitutionalReceipt],
) -> None:
    """
    Verify the constitutional receipt chain.

    HARD REQUIREMENTS:
    - Every epoch must have a corresponding receipt
    - Every receipt must bind to:
        - its epoch hash
        - the registry hash
        - the attestation hash
    - No extra receipts may exist
    - No epoch may exist without a receipt

    FAILURE:
    - Raises ReceiptChainViolation
    """

    if not epoch_history:
        raise ReceiptChainViolation(
            "No epoch history provided — constitutional history undefined"
        )

    if not receipts:
        raise ReceiptChainViolation(
            "No receipts provided — execution history does not exist"
        )

    # -------------------------------------------------------------
    # Index receipts by epoch number
    # -------------------------------------------------------------

    receipt_by_epoch: dict[int, ConstitutionalReceipt] = {}

    for receipt in receipts:
        if not isinstance(receipt, ConstitutionalReceipt):
            raise ReceiptChainViolation(
                f"Invalid receipt type: {type(receipt)}"
            )

        epoch_number = receipt.epoch

        if epoch_number in receipt_by_epoch:
            raise ReceiptChainViolation(
                f"Duplicate receipt for epoch {epoch_number}"
            )

        receipt_by_epoch[epoch_number] = receipt

    # -------------------------------------------------------------
    # Verify epoch → receipt bijection
    # -------------------------------------------------------------

    for epoch in epoch_history:
        if not isinstance(epoch, EpochSnapshot):
            raise ReceiptChainViolation(
                f"Invalid epoch snapshot type: {type(epoch)}"
            )

        if epoch.number not in receipt_by_epoch:
            raise ReceiptChainViolation(
                f"Epoch {epoch.number} has no corresponding receipt"
            )

    if len(receipt_by_epoch) != len(list(epoch_history)):
        raise ReceiptChainViolation(
            "Receipt count does not match epoch history length"
        )

    # -------------------------------------------------------------
    # Verify receipt bindings
    # -------------------------------------------------------------

    registry_hash = registry.get("registry_hash")
    if not registry_hash:
        raise ReceiptChainViolation(
            "Registry hash missing — cannot verify receipt bindings"
        )

    attestation_hash = getattr(attestation, "attestation_hash", None)
    if not attestation_hash:
        raise ReceiptChainViolation(
            "Attestation hash missing — receipt chain incomplete"
        )

    for epoch in epoch_history:
        receipt = receipt_by_epoch[epoch.number]

        # ---------------------------------------------------------
        # Epoch hash binding
        # ---------------------------------------------------------

        if receipt.epoch_hash != epoch.epoch_hash:
            raise ReceiptChainViolation(
                f"Epoch hash mismatch for epoch {epoch.number}: "
                f"{receipt.epoch_hash} != {epoch.epoch_hash}"
            )

        # ---------------------------------------------------------
        # Registry hash binding
        # ---------------------------------------------------------

        if receipt.registry_hash != registry_hash:
            raise ReceiptChainViolation(
                f"Registry hash mismatch in receipt for epoch {epoch.number}: "
                f"{receipt.registry_hash} != {registry_hash}"
            )

        # ---------------------------------------------------------
        # Attestation hash binding
        # ---------------------------------------------------------

        if receipt.attestation_hash != attestation_hash:
            raise ReceiptChainViolation(
                f"Attestation hash mismatch in receipt for epoch {epoch.number}: "
                f"{receipt.attestation_hash} != {attestation_hash}"
            )

        # ---------------------------------------------------------
        # Receipt structural sanity
        # ---------------------------------------------------------

        if not receipt.invariants_executed:
            raise ReceiptChainViolation(
                f"Receipt for epoch {epoch.number} declares no invariants executed"
            )

    # -------------------------------------------------------------
    # SUCCESS
    # -------------------------------------------------------------

    return None
