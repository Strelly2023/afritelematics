from decimal import Decimal, ROUND_HALF_UP


MONEY = Decimal("0.01")


def _as_decimal(value):
    return Decimal(str(value))


def money(value):
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def calculate_fare(distance_km, duration_minutes, policy):
    """Calculate a deterministic fare from replay-derived trip and distance."""

    distance_cost = _as_decimal(distance_km) * policy.per_km_rate
    time_cost = _as_decimal(duration_minutes) * policy.per_minute_rate
    total = policy.base_fare + distance_cost + time_cost
    platform_fee = total * (policy.platform_fee_percent / Decimal("100"))
    driver_earnings = total - platform_fee

    return {
        "total_fare": money(total),
        "platform_fee": money(platform_fee),
        "driver_earnings": money(driver_earnings),
        "policy_id": getattr(policy, "id", None),
        "policy_name": getattr(policy, "name", None),
    }
