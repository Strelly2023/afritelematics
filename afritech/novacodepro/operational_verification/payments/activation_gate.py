from __future__ import annotations

from .policy import REQUIRED_PAYMENT_CONTROLS


def evaluate_payment_activation(evidence: dict[str, str] | None = None) -> dict[str, object]:
    evidence = evidence or {}
    checks = [{"id": control, "status": "PASS" if evidence.get(control) == "PASS" else "PENDING"} for control in REQUIRED_PAYMENT_CONTROLS]
    enabled = all(check["status"] == "PASS" for check in checks)
    return {
        "current_state": "ENABLED" if enabled else "DISABLED",
        "checks": checks,
        "real_payments_enabled": enabled,
    }
