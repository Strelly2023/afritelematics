from decimal import Decimal, ROUND_HALF_UP

from .models import CurrencyRate


MONEY = Decimal("0.01")


def money(value):
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def convert_currency(amount, source_currency, target_currency):
    if source_currency == target_currency:
        return money(Decimal(str(amount)))

    rate = CurrencyRate.objects.get(
        source_currency=source_currency,
        target_currency=target_currency,
        active=True,
    )
    return money(Decimal(str(amount)) * rate.rate)
