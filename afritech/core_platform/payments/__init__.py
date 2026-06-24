"""NovaPay provider adapters for core platform flows."""

from afritech.core_platform.payments.contracts import PaymentProviderResult
from afritech.core_platform.cbdc import CBDCProvider
from afritech.core_platform.payments.providers import (
    PayIDProvider,
    StripeProvider,
    provider_for,
)

__all__ = [
    "PaymentProviderResult",
    "CBDCProvider",
    "PayIDProvider",
    "StripeProvider",
    "provider_for",
]
