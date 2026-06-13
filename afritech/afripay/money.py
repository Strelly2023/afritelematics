"""Money primitives for AfriPay.

The domain keeps all amounts as fixed-point Decimal values quantized to the
minor-unit precision used by the rest of this repository's payment proofs.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from afritech.afripay.exceptions import GuardViolation


SUPPORTED_CURRENCIES = frozenset({"AUD", "USD", "BIF", "CDF", "KES", "TZS", "UGX", "RWF"})


def quantize_money(value: Decimal | int | str) -> Decimal:
    amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if amount < 0:
        raise GuardViolation("amount must be non-negative")
    return amount


@dataclass(frozen=True, order=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        currency = self.currency.upper()
        if currency not in SUPPORTED_CURRENCIES:
            raise GuardViolation(f"unsupported currency: {currency}")
        object.__setattr__(self, "currency", currency)
        object.__setattr__(self, "amount", quantize_money(self.amount))

    @classmethod
    def of(cls, amount: Decimal | int | str, currency: str) -> "Money":
        return cls(Decimal(str(amount)), currency)

    @property
    def is_zero(self) -> bool:
        return self.amount == Decimal("0.00")

    def require_positive(self) -> "Money":
        if self.amount <= 0:
            raise GuardViolation("amount must be positive")
        return self

    def same_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise GuardViolation("currency mismatch")

    def __add__(self, other: "Money") -> "Money":
        self.same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        self.same_currency(other)
        if other.amount > self.amount:
            raise GuardViolation("money subtraction would go negative")
        return Money(self.amount - other.amount, self.currency)

    def multiply(self, factor: Decimal | int | str) -> "Money":
        return Money(self.amount * Decimal(str(factor)), self.currency)

    def canonical(self) -> dict[str, str]:
        return {"amount": format(self.amount, ".2f"), "currency": self.currency}
