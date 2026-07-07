"""Private-development guardrails for simulated payment workflows."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


class PrivateDevelopmentPaymentError(RuntimeError):
    """Raised when a private-development payment boundary is violated."""


@dataclass(frozen=True)
class PrivateDevelopmentConfig:
    environment: str
    live_payments_enabled: bool
    real_charging_enabled: bool
    external_payouts_enabled: bool
    production_credentials_allowed: bool
    public_launch_allowed: bool
    controlled_pilot_allowed: bool
    payment_mode: str
    identity_mode: str
    apk_distribution: str


@lru_cache(maxsize=1)
def load_private_development_config() -> PrivateDevelopmentConfig:
    config_path = _repo_root() / "config" / "private_development.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    return PrivateDevelopmentConfig(
        environment=str(payload["environment"]),
        live_payments_enabled=bool(payload["live_payments_enabled"]),
        real_charging_enabled=bool(payload["real_charging_enabled"]),
        external_payouts_enabled=bool(payload["external_payouts_enabled"]),
        production_credentials_allowed=bool(payload["production_credentials_allowed"]),
        public_launch_allowed=bool(payload["public_launch_allowed"]),
        controlled_pilot_allowed=bool(payload["controlled_pilot_allowed"]),
        payment_mode=str(payload["payment_mode"]),
        identity_mode=str(payload["identity_mode"]),
        apk_distribution=str(payload["apk_distribution"]),
    )


def ensure_private_development_mode() -> PrivateDevelopmentConfig:
    config = load_private_development_config()
    if config.environment != "PRIVATE_DEVELOPMENT":
        raise PrivateDevelopmentPaymentError("private_development_required")
    return config


def guard_payment_boundary(
    *,
    provider: str,
    method: str,
    live_charge: bool = False,
    payout: bool = False,
    production_credentials_present: bool = False,
) -> None:
    config = ensure_private_development_mode()
    if config.live_payments_enabled or config.real_charging_enabled:
        raise PrivateDevelopmentPaymentError("live_payments_disabled_in_private_development")
    if live_charge or payout:
        raise PrivateDevelopmentPaymentError("live_payment_execution_blocked")
    if production_credentials_present or not config.production_credentials_allowed:
        if provider not in {"cash", "wallet", "stripe", "flutterwave"}:
            raise PrivateDevelopmentPaymentError("production_credentials_rejected")
    if provider.startswith("live_"):
        raise PrivateDevelopmentPaymentError("live_provider_rejected")
    if method not in {"card", "wallet", "cash", "regional", "split"}:
        raise PrivateDevelopmentPaymentError("unsupported_private_dev_payment_method")


def mark_simulated_payment(payload: dict[str, Any]) -> dict[str, Any]:
    config = ensure_private_development_mode()
    return {
        **payload,
        "simulated_payment": True,
        "payment_mode": config.payment_mode,
        "private_development": asdict(config),
    }


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]

