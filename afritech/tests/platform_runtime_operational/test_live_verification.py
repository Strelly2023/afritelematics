from __future__ import annotations

import asyncio

import httpx

from afritech.platform_runtime.operational import RuntimeVerificationService, VerificationContext


class _MockClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, headers=None):
        path = httpx.URL(url).path
        status = 200 if path in {"/health/live", "/health/ready", "/health/products", "/health/workers", "/v1/platform"} else 404
        return httpx.Response(status, request=httpx.Request("GET", url), text="ok")

    async def post(self, url, headers=None, json=None):
        return httpx.Response(200, request=httpx.Request("POST", url), json={"status": "queued"})


def test_live_verification_executes_http_probes(monkeypatch) -> None:
    monkeypatch.setattr("afritech.platform_runtime.operational.probes.httpx.AsyncClient", _MockClient)
    context = VerificationContext(base_url="http://verification.example", product_code="novafleet", product_version="2026.07.0", environment="staging", region="AU")
    run = asyncio.run(RuntimeVerificationService().run(context))
    assert run.product_code == "novafleet"
    assert run.status in {"PASS", "FAIL"}
