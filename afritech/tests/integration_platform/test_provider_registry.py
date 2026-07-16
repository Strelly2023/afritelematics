from __future__ import annotations

import pytest

from afritech.integration_platform import ProviderDefinition, ProviderRegistry


def test_provider_registry_registers_and_resolves_provider() -> None:
    registry = ProviderRegistry()
    provider = registry.register(
        ProviderDefinition(
            provider_id="maps-primary",
            product_code="novaride",
            provider_type="REST",
            base_url="https://maps.example.com",
            environment="staging",
            region="AU",
            authentication_type="api_key",
            timeout_seconds=10,
            retry_policy="provider-read",
            circuit_breaker_policy="default",
            rate_limit_policy="standard",
        )
    )

    assert registry.resolve("novaride", "maps-primary") == provider
    assert registry.list_product_providers("novaride")[0].provider_id == "maps-primary"


def test_provider_registry_rejects_duplicate_provider_ids() -> None:
    registry = ProviderRegistry()
    registry.register(
        ProviderDefinition(
            provider_id="maps-primary",
            product_code="novaride",
            provider_type="REST",
            base_url="https://maps.example.com",
            environment="staging",
            region="AU",
            authentication_type="api_key",
            timeout_seconds=10,
            retry_policy="provider-read",
            circuit_breaker_policy="default",
            rate_limit_policy="standard",
        )
    )

    with pytest.raises(Exception):
        registry.register(
            ProviderDefinition(
                provider_id="maps-primary",
                product_code="novaride",
                provider_type="REST",
                base_url="https://maps.example.com",
                environment="staging",
                region="AU",
                authentication_type="api_key",
                timeout_seconds=10,
                retry_policy="provider-read",
                circuit_breaker_policy="default",
                rate_limit_policy="standard",
            )
        )

