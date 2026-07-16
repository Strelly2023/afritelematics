from __future__ import annotations

import asyncio

import httpx

from afritech.platform_runtime.adapters.object_storage import S3ObjectStorageAdapter
from afritech.platform_runtime.models import InfrastructureKind, InfrastructureRequirement


class _FakeClient:
    def __init__(self, *args, **kwargs):
        self.storage: dict[str, bytes] = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def request(self, method, url, content=None, headers=None):
        key = str(httpx.URL(url))
        if method == "PUT":
            self.storage[key] = content or b""
            return httpx.Response(200, request=httpx.Request("PUT", url), content=b"ok")
        if method == "GET":
            body = self.storage.get(key, b"")
            return httpx.Response(200 if key in self.storage else 404, request=httpx.Request("GET", url), content=body)
        if method == "DELETE":
            self.storage.pop(key, None)
            return httpx.Response(204, request=httpx.Request("DELETE", url), content=b"")
        return httpx.Response(500, request=httpx.Request(method, url), content=b"error")


def test_object_storage_adapter_uses_s3_style_paths(monkeypatch) -> None:
    fake = _FakeClient()
    monkeypatch.setattr("afritech.platform_runtime.adapters.object_storage.httpx.AsyncClient", lambda *args, **kwargs: fake)
    adapter = S3ObjectStorageAdapter("https://object.example", "runtime-bucket")
    requirement = InfrastructureRequirement(
        id="req-1",
        product_code="novafleet",
        kind=InfrastructureKind.OBJECT_STORAGE_PREFIX,
        name="novafleet",
        required=True,
        configuration={},
        desired_state="ready",
        ownership="novafleet",
        region="AU",
    )
    plan = asyncio.run(adapter.plan(requirement))
    applied = asyncio.run(adapter.apply(plan))
    verified = asyncio.run(adapter.verify(requirement))
    rolled_back = asyncio.run(adapter.rollback(applied))

    assert plan.product_code == "novafleet"
    assert applied.success is True
    assert verified.success is True
    assert rolled_back.success is True
