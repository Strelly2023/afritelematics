"""Shared HTTP client for governed integrations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from time import perf_counter
from typing import Any

import httpx

from .contracts import IntegrationContext, IntegrationResponse
from .errors import IntegrationConfigurationError, IntegrationProviderError, IntegrationTimeoutError
from .provider_registry import ProviderRegistry
from .retry import RetryPolicy, retry_transient


def _build_headers(context: IntegrationContext, extra: Mapping[str, str] | None = None, idempotency_key: str | None = None) -> dict[str, str]:
    headers = {
        "accept": "application/json",
        "x-request-id": context.request_id,
        "x-correlation-id": context.correlation_id,
        "x-trace-id": context.trace_id,
        "x-product-code": context.product_code,
        "x-tenant-id": context.tenant_id,
        "x-organization-id": context.organization_id,
        "x-actor-id": context.actor_id,
        "x-purpose": context.purpose,
        "x-region": context.region,
        "x-environment": context.environment,
    }
    if context.idempotency_key or idempotency_key:
        headers["x-idempotency-key"] = context.idempotency_key or idempotency_key or ""
    if extra:
        headers.update({str(key): str(value) for key, value in extra.items()})
    return {key: value for key, value in headers.items() if value}


class NovaTechHttpClient:
    def __init__(
        self,
        provider_registry: ProviderRegistry,
        *,
        retry_policies: Mapping[str, RetryPolicy] | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._registry = provider_registry
        self._retry_policies = dict(retry_policies or {})
        self._client = client or httpx.AsyncClient(timeout=httpx.Timeout(30.0))

    async def request(
        self,
        *,
        provider_id: str,
        product_code: str,
        method: str,
        path: str,
        context: IntegrationContext,
        query: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        idempotency_key: str | None = None,
    ) -> IntegrationResponse:
        provider = self._registry.resolve(product_code, provider_id)
        if not provider.enabled:
            raise IntegrationConfigurationError("provider is disabled")
        timeout = provider.timeout_seconds or 30
        retry_policy = self._retry_policies.get(provider.retry_policy)
        request_headers = _build_headers(context, headers, idempotency_key)
        url = f"{provider.base_url.rstrip('/')}/{path.lstrip('/')}"

        async def execute() -> httpx.Response:
            started_at = perf_counter()
            try:
                return await self._client.request(
                    method.upper(),
                    url,
                    params=dict(query or {}),
                    json=dict(body or {}) if body is not None else None,
                    headers=request_headers,
                    timeout=timeout,
                )
            except httpx.TimeoutException as error:
                raise IntegrationTimeoutError(str(error)) from error
            finally:
                _ = started_at

        if retry_policy is not None:
            response = await retry_transient(execute, retry_policy)
        else:
            response = await execute()

        duration_ms = 0.0
        payload: Any
        try:
            payload = response.json()
        except Exception:
            payload = await response.aread()

        if response.status_code >= 400:
            raise IntegrationProviderError(
                f"provider {provider.provider_id} returned {response.status_code}",
                code="INTEGRATION_PROVIDER_ERROR",
            )
        return IntegrationResponse(
            status_code=response.status_code,
            body=payload,
            headers={key: value for key, value in response.headers.items()},
            provider_id=provider.provider_id,
            duration_ms=duration_ms,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

