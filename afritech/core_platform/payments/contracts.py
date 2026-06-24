"""Shared payment adapter contracts for NovaPay."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from afritech.core_platform.models import PaymentIntent


@dataclass(frozen=True)
class PaymentProviderResult:
    provider: str
    provider_reference: str
    status: str
    settlement_status: str
    raw: dict[str, object]


class PaymentProviderAdapter(Protocol):
    name: str

    def authorize(self, intent: PaymentIntent) -> PaymentProviderResult:
        ...
