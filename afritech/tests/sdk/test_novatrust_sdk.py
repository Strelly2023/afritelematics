from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.core_platform_api import (
    build_core_platform_router,
    build_public_trust_explorer_router,
)
from afritech.sdk.novatrust import NovaTrustClient


def test_novatrust_python_sdk_uses_public_contract(monkeypatch) -> None:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_core_platform_router())
    app.include_router(build_public_trust_explorer_router())

    client = TestClient(app)

    token = JWT.create_token(
        "operator-sdk",
        role="OPERATOR",
        organization_id="org-sdk"
    )

    pilot = client.post(
        "/v1/core-platform/pilot/flow",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "intent_id": "sdk-pilot",
            "amount": "5.00",
            "currency": "aud",
            "destination": "sdk-merchant",
            "provider": "payid",
        },
    )

    trust_id = pilot.json()["result"]["trust"]["trust_id"]
    requested_paths: list[str] = []

    class _Response:
        def __init__(self, response):
            self.response = response

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return self.response.content

    def fake_urlopen(url, timeout: int = 20):
        assert timeout == 20

        full_url = url.full_url if hasattr(url, "full_url") else str(url)
        path = full_url.replace("http://testserver", "")
        requested_paths.append(path)

        return _Response(
            client.get(path, headers={"Accept": "application/json"})
        )

    monkeypatch.setattr(
        "afritech.sdk.novatrust.request.urlopen",
        fake_urlopen
    )

    result = NovaTrustClient("http://testserver").verify(trust_id)

    assert result.verified is True
    assert result.control_count >= 1
    assert f"/trust/explorer/{trust_id}" in requested_paths
    assert f"/v1/core-platform/trust/explorer/{trust_id}" not in requested_paths


def test_novatrust_js_sdk_exposes_public_contract() -> None:
    source = Path("docs/sdk/novatrust-js/index.js").read_text(
        encoding="utf-8"
    )

    assert "export class NovaTrustClient" in source
    assert "/trust/explorer/" in source
    assert 'Accept: "application/json"' in source
    assert "/v1/core-platform" not in source