from __future__ import annotations

import asyncio
import httpx

from afritech.integration_platform import IntegrationContext, ProviderDefinition, ProviderRegistry, NovaTechHttpClient


def test_http_client_injects_shared_headers() -> None:
    async def run() -> None:
        captured = {}

        async def handler(request: httpx.Request) -> httpx.Response:
            captured["headers"] = dict(request.headers)
            captured["url"] = str(request.url)
            return httpx.Response(200, json={"ok": True})

        client = NovaTechHttpClient(
            ProviderRegistry(),
            client=httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://unused.example.com"),
        )
        client._registry.register(  # noqa: SLF001 - test setup
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
        response = await client.request(
            provider_id="maps-primary",
            product_code="novaride",
            method="GET",
            path="/route",
            context=IntegrationContext(
                request_id="req-1",
                correlation_id="corr-1",
                trace_id="trace-1",
                product_code="novaride",
                tenant_id="tenant-a",
                organization_id="org-a",
                actor_id="actor-a",
                environment="staging",
                region="AU",
                purpose="routing",
                roles=("DEVELOPER",),
                permissions=("novaride:ride:read",),
            ),
        )

        assert response.status_code == 200
        assert captured["headers"]["x-request-id"] == "req-1"
        assert captured["headers"]["x-tenant-id"] == "tenant-a"
        assert captured["url"].endswith("/route")

    asyncio.run(run())
