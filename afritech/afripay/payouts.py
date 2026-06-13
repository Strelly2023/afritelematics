"""Bulk payout and payroll support."""

from __future__ import annotations

from decimal import Decimal

from afritech.afripay.exceptions import DuplicateReference, GuardViolation
from afritech.afripay.guards import require_same_currency
from afritech.afripay.models import PayoutBatch, PayoutItem, new_id
from afritech.afripay.money import Money


class BulkPayoutService:
    def __init__(self) -> None:
        self._references: set[str] = set()

    def create_batch(self, *, initiated_by: str, items: tuple[PayoutItem, ...]) -> PayoutBatch:
        if not initiated_by:
            raise GuardViolation("initiated_by is required")
        if not items:
            raise GuardViolation("payout batch requires items")
        references = [item.reference for item in items]
        if len(set(references)) != len(references):
            raise DuplicateReference("duplicate payout item reference in batch")
        if self._references.intersection(references):
            raise DuplicateReference("payout item reference already exists")
        currency = require_same_currency(item.amount for item in items)
        total = Money.of(sum((item.amount.amount for item in items), Decimal("0.00")), currency)
        total.require_positive()
        self._references.update(references)
        return PayoutBatch(new_id("payout"), initiated_by, items, total, "queued")

    def mark_processed(self, batch: PayoutBatch) -> PayoutBatch:
        return PayoutBatch(batch.payout_id, batch.initiated_by, batch.items, batch.total, "processed")


def payout_item(recipient_id: str, amount: Money, reference: str) -> PayoutItem:
    amount.require_positive()
    if not recipient_id or not reference:
        raise GuardViolation("recipient_id and reference are required")
    return PayoutItem(recipient_id, amount, reference)

