"""Payment provider abstraction for NovaPay."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol


@dataclass(frozen=True)
class ProviderPaymentRequest:
    intent_id: str
    actor_id: str
    organization_id: str
    amount: Decimal
    currency: str
    destination: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ProviderPaymentResult:
    provider: str
    provider_reference: str
    status: str
    settlement_status: str
    raw: dict[str, Any]


class PaymentProvider(Protocol):
    provider_name: str

    def execute_payment(self, request: ProviderPaymentRequest) -> ProviderPaymentResult:
        ...
