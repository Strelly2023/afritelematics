"""Money primitives."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str

    @classmethod
    def of(cls, amount: str | int | Decimal, currency: str) -> "Money":
        return cls(amount=Decimal(str(amount)), currency=currency.upper())

    def as_dict(self) -> dict[str, str]:
        return {"amount": format(self.amount, "f"), "currency": self.currency}
