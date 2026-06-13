"""Payment provider adapter interfaces and deterministic test adapters."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import os
from typing import Protocol

from afritech.afripay.events import canonical_hash
from afritech.afripay.exceptions import ProviderFailure
from afritech.afripay.models import PaymentRoute, ProviderQuote
from afritech.afripay.money import Money


@dataclass(frozen=True)
class ProviderResult:
    provider: str
    external_reference: str
    status: str
    latency_ms: int
    raw: dict[str, object]


class PaymentProvider(Protocol):
    name: str
    rail: str

    def quote(self, amount: Money) -> ProviderQuote:
        ...

    def send(self, route: PaymentRoute) -> ProviderResult:
        ...

    def verify(self, external_reference: str) -> ProviderResult:
        ...


class SimulatedPaymentProvider:
    """Deterministic adapter for non-live rail integration.

    It models cost, speed, reliability, and failure without contacting external
    networks. Live adapters must implement the same protocol and pass the same
    orchestration guards before use.
    """

    def __init__(
        self,
        *,
        name: str,
        rail: str,
        fee_rate: Decimal | str,
        fixed_fee: Decimal | str,
        latency_ms: int,
        reliability: Decimal | str,
        max_amount: Decimal | str | None = None,
        fail: bool = False,
        supports_offline_fallback: bool = False,
    ) -> None:
        self.name = name
        self.rail = rail
        self.fee_rate = Decimal(str(fee_rate))
        self.fixed_fee = Decimal(str(fixed_fee))
        self.latency_ms = latency_ms
        self.reliability = Decimal(str(reliability))
        self.max_amount = Decimal(str(max_amount)) if max_amount is not None else None
        self.fail = fail
        self.supports_offline_fallback = supports_offline_fallback

    def quote(self, amount: Money) -> ProviderQuote:
        quoted_amount = amount
        if self.max_amount is not None and amount.amount > self.max_amount:
            quoted_amount = Money.of(self.max_amount, amount.currency)
        fee = Money.of((quoted_amount.amount * self.fee_rate) + self.fixed_fee, amount.currency)
        return ProviderQuote(
            provider=self.name,
            rail=self.rail,
            amount=quoted_amount,
            fee=fee,
            estimated_latency_ms=self.latency_ms,
            reliability=self.reliability,
            supports_offline_fallback=self.supports_offline_fallback,
        )

    def send(self, route: PaymentRoute) -> ProviderResult:
        if self.fail:
            raise ProviderFailure(f"provider failed: {self.name}")
        reference = canonical_hash(
            {
                "amount": route.amount.canonical(),
                "provider": self.name,
                "rail": self.rail,
                "route_id": route.route_id,
            }
        )[:28]
        external_reference = f"{self.name}.{reference}"
        return ProviderResult(
            self.name,
            external_reference,
            "confirmed",
            self.latency_ms,
            {
                "mode": "deterministic",
                "provider": self.name,
                "rail": self.rail,
                "reference": external_reference,
            },
        )

    def verify(self, external_reference: str) -> ProviderResult:
        if not external_reference:
            raise ProviderFailure("external_reference is required")
        return ProviderResult(
            self.name,
            external_reference,
            "confirmed",
            self.latency_ms,
            {"mode": "deterministic_verify", "provider": self.name},
        )


def default_provider_set() -> tuple[PaymentProvider, ...]:
    mode = os.environ.get("AFRIPAY_PROVIDER_MODE", "simulated").lower()
    if mode == "sandbox":
        from afritech.afripay.providers_sandbox import sandbox_provider_set

        return sandbox_provider_set()
    return (
        SimulatedPaymentProvider(
            name="mtn_mobile_money",
            rail="mobile_money",
            fee_rate="0.012",
            fixed_fee="0.20",
            latency_ms=900,
            reliability="0.97",
            max_amount="70.00",
            supports_offline_fallback=True,
        ),
        SimulatedPaymentProvider(
            name="bank_partner",
            rail="bank",
            fee_rate="0.004",
            fixed_fee="0.10",
            latency_ms=2800,
            reliability="0.93",
        ),
        SimulatedPaymentProvider(
            name="stablecoin_settlement",
            rail="digital_asset",
            fee_rate="0.006",
            fixed_fee="0.05",
            latency_ms=1300,
            reliability="0.78",
        ),
    )


def build_provider_set(mode: str) -> tuple[PaymentProvider, ...]:
    previous = os.environ.get("AFRIPAY_PROVIDER_MODE")
    os.environ["AFRIPAY_PROVIDER_MODE"] = mode
    try:
        return default_provider_set()
    finally:
        if previous is None:
            os.environ.pop("AFRIPAY_PROVIDER_MODE", None)
        else:
            os.environ["AFRIPAY_PROVIDER_MODE"] = previous
