from decimal import Decimal, ROUND_HALF_UP


MONEY = Decimal("0.01")


def money(value):
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def calculate_tax(subtotal, tax_rate):
    subtotal_decimal = Decimal(str(subtotal))
    tax = subtotal_decimal * (Decimal(str(tax_rate)) / Decimal("100"))

    return {
        "subtotal": money(subtotal_decimal),
        "tax": money(tax),
        "total": money(subtotal_decimal + tax),
    }
