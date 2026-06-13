"""AfriPay runtime configuration."""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class EnvironmentConfig:
    live_settlement_enabled: bool = False
    deterministic_provider_mode: bool = True
    compliance_activation_reference: str | None = None

    @classmethod
    def from_env(cls) -> "EnvironmentConfig":
        live = os.environ.get("AFRIPAY_LIVE_SETTLEMENT_ENABLED", "false").lower() == "true"
        activation = os.environ.get("AFRIPAY_COMPLIANCE_ACTIVATION_REFERENCE") or None
        return cls(
            live_settlement_enabled=live,
            deterministic_provider_mode=not live,
            compliance_activation_reference=activation,
        )

    def require_live_activation(self) -> None:
        from afritech.afripay.exceptions import GuardViolation

        if self.live_settlement_enabled and not self.compliance_activation_reference:
            raise GuardViolation("live settlement requires compliance activation reference")
