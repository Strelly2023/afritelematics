"""FX rate locking and conversion."""

from __future__ import annotations

from decimal import Decimal

from afritech.afripay.events import canonical_hash
from afritech.afripay.exceptions import GuardViolation
from afritech.afripay.models import FXConversion, FXRate, new_id
from afritech.afripay.money import Money


class FXEngine:
    def __init__(self, rates: dict[tuple[str, str], Decimal | str]) -> None:
        self._rates = {(base.upper(), quote.upper()): Decimal(str(rate)) for (base, quote), rate in rates.items()}

    def lock_rate(self, base_currency: str, quote_currency: str, provider: str = "afripay_fx") -> FXRate:
        base = base_currency.upper()
        quote = quote_currency.upper()
        if base == quote:
            rate = Decimal("1.00")
        else:
            rate = self._rates.get((base, quote))
            if rate is None:
                inverse = self._rates.get((quote, base))
                if inverse is None:
                    raise GuardViolation(f"missing FX rate: {base}/{quote}")
                rate = Decimal("1.00") / inverse
        reference = canonical_hash({"base": base, "provider": provider, "quote": quote, "rate": str(rate)})[:24]
        return FXRate(base, quote, rate, provider, f"fxlock.{reference}")

    def convert(self, *, transaction_id: str, amount: Money, to_currency: str) -> FXConversion:
        rate = self.lock_rate(amount.currency, to_currency)
        converted = Money.of(amount.amount * rate.rate, to_currency)
        return FXConversion(new_id("fxconv"), transaction_id, amount, converted, rate)


def default_fx_engine() -> FXEngine:
    return FXEngine(
        {
            ("AUD", "BIF"): "1900.00",
            ("AUD", "CDF"): "1725.00",
            ("AUD", "KES"): "84.00",
            ("AUD", "USD"): "0.66",
            ("USD", "BIF"): "2875.00",
            ("USD", "CDF"): "2600.00",
            ("USD", "KES"): "150.00",
            ("KES", "USD"): "0.0077",
            ("KES", "BIF"): "13.00",
            ("KES", "CDF"): "11.50",
        }
    )
