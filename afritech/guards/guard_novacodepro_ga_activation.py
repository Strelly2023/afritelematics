from __future__ import annotations


def verify_ga_separate_from_payments(payload: dict[str, object]) -> bool:
    return payload.get("real_payments_enabled") is not True
