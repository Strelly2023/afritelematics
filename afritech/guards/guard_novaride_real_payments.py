"""Real payment guard."""

REAL_PAYMENTS_ENABLED = False
REAL_PAYMENT_APPROVAL = "PENDING"


def assert_real_payments_blocked() -> dict[str, object]:
    return {"REAL_PAYMENTS_ENABLED": REAL_PAYMENTS_ENABLED, "REAL_PAYMENT_APPROVAL": REAL_PAYMENT_APPROVAL}
