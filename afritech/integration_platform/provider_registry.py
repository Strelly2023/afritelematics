"""Registry for governed external providers."""

from __future__ import annotations

from dataclasses import asdict
from urllib.parse import urlparse

from .contracts import ProviderDefinition
from .errors import IntegrationConfigurationError

_ALLOWED_ENVIRONMENTS = {"local", "development", "test", "integration", "staging", "controlled-pilot", "public-pilot", "production", "disaster-recovery"}


def _normalize(value: str) -> str:
    return str(value or "").strip()


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[tuple[str, str], ProviderDefinition] = {}

    def register(self, provider: ProviderDefinition) -> ProviderDefinition:
        provider_id = _normalize(provider.provider_id)
        product_code = _normalize(provider.product_code)
        if not provider_id or not product_code:
            raise IntegrationConfigurationError("provider_id and product_code are required")
        if (product_code, provider_id) in self._providers:
            raise IntegrationConfigurationError("duplicate provider registration")
        parsed = urlparse(provider.base_url)
        if parsed.scheme not in {"https", "http"}:
            raise IntegrationConfigurationError("provider base_url must be http(s)")
        if provider.authentication_type.lower() not in {
            "api_key",
            "bearer_token",
            "oauth2",
            "oauth_client_credentials",
            "mutual_tls",
            "hmac_signature",
            "jwt_assertion",
            "basic_auth",
            "signed_headers",
        }:
            raise IntegrationConfigurationError("unsupported provider authentication")
        if provider.timeout_seconds <= 0:
            raise IntegrationConfigurationError("provider timeout_seconds must be positive")
        if provider.retry_policy == "no-retry" and provider.live_mode and provider.environment not in {"development", "test", "integration", "staging", "controlled-pilot", "public-pilot", "production"}:
            raise IntegrationConfigurationError("live providers require an approved environment")
        if provider.environment not in _ALLOWED_ENVIRONMENTS:
            raise IntegrationConfigurationError("unsupported provider environment")
        self._providers[(product_code, provider_id)] = provider
        return provider

    def resolve(self, product_code: str, provider_id: str) -> ProviderDefinition:
        key = (_normalize(product_code), _normalize(provider_id))
        if key not in self._providers:
            raise IntegrationConfigurationError("provider not found")
        return self._providers[key]

    def list_product_providers(self, product_code: str) -> tuple[ProviderDefinition, ...]:
        normalized = _normalize(product_code)
        return tuple(provider for (owner, _), provider in self._providers.items() if owner == normalized)

    def disable(self, product_code: str, provider_id: str) -> ProviderDefinition:
        provider = self.resolve(product_code, provider_id)
        disabled = ProviderDefinition(**{**asdict(provider), "enabled": False})
        self._providers[(_normalize(product_code), _normalize(provider_id))] = disabled
        return disabled

    def snapshot(self) -> dict[str, object]:
        return {
            "providers": [asdict(provider) for provider in self._providers.values()],
            "provider_count": len(self._providers),
        }

