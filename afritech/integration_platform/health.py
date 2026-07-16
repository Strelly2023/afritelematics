"""Integration health summaries."""

from __future__ import annotations

from dataclasses import dataclass

from .provider_registry import ProviderRegistry


@dataclass(frozen=True, slots=True)
class ProviderHealth:
    status: str
    latency_ms: int | None = None
    circuit: str | None = None


class IntegrationHealthService:
    def __init__(self, registry: ProviderRegistry) -> None:
        self._registry = registry

    def health(self, product_code: str, provider_id: str | None = None) -> dict[str, object]:
        providers = self._registry.list_product_providers(product_code)
        if provider_id:
            provider = self._registry.resolve(product_code, provider_id)
            return {
                "productCode": product_code,
                "providerId": provider.provider_id,
                "status": "ready" if provider.enabled else "disabled",
                "provider": provider,
            }
        return {
            "productCode": product_code,
            "status": "ready" if providers else "empty",
            "providers": {provider.provider_id: ProviderHealth(status="ready" if provider.enabled else "disabled") for provider in providers},
        }

