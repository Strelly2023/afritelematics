"""NovaPay provider adapters for core platform flows."""

from afritech.core_platform.payments.contracts import PaymentProviderResult
from afritech.core_platform.payments.providers import (
    PayIDProvider,
    StripeProvider,
    provider_for,
)

__all__ = [
    "PaymentProviderResult",
    "PayIDProvider",
    "StripeProvider",
    "provider_for",
]
