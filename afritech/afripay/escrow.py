"""Escrow and conditional release services."""

from __future__ import annotations

from afritech.afripay.events import EventOutbox
from afritech.afripay.exceptions import GuardViolation
from afritech.afripay.models import Escrow, new_id
from afritech.afripay.money import Money


class EscrowService:
    def __init__(self, outbox: EventOutbox | None = None) -> None:
        self.outbox = outbox or EventOutbox()
        self._escrows: dict[str, Escrow] = {}

    def lock(
        self,
        *,
        transaction_id: str,
        payer_id: str,
        payee_id: str,
        total: Money,
        release_condition: str,
    ) -> Escrow:
        total.require_positive()
        if not release_condition:
            raise GuardViolation("release_condition is required")
        escrow = Escrow(new_id("escrow"), transaction_id, payer_id, payee_id, total, release_condition)
        self._escrows[escrow.escrow_id] = escrow
        self.outbox.emit("afripay.escrow.locked", {"escrow_id": escrow.escrow_id, "transaction_id": transaction_id})
        return escrow

    def release(self, escrow_id: str, evidence: str) -> Escrow:
        escrow = self._escrows[escrow_id]
        if escrow.status != "locked":
            raise GuardViolation("escrow is not locked")
        if evidence != escrow.release_condition:
            raise GuardViolation("escrow release evidence mismatch")
        escrow.status = "released"
        self.outbox.emit("afripay.escrow.released", {"escrow_id": escrow_id})
        return escrow

    def refund(self, escrow_id: str, reason: str) -> Escrow:
        escrow = self._escrows[escrow_id]
        if escrow.status != "locked":
            raise GuardViolation("escrow is not refundable")
        if not reason:
            raise GuardViolation("refund reason is required")
        escrow.status = "refunded"
        self.outbox.emit("afripay.escrow.refunded", {"escrow_id": escrow_id, "reason": reason})
        return escrow


