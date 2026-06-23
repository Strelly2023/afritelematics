from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.core_platform_api import (
    build_core_platform_router,
    build_public_trust_explorer_router,
)
from afritech.tools import novatrust_verifier_cli


def test_novatrust_verifier_cli_downloads_and_verifies(monkeypatch, tmp_path, capsys) -> None:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_core_platform_router())
    app.include_router(build_public_trust_explorer_router())
    client = TestClient(app)
    token = JWT.create_token("operator-cli", role="OPERATOR", organization_id="org-cli")
    pilot = client.post(
        "/v1/core-platform/pilot/flow",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "intent_id": "cli-pilot",
            "amount": "4.00",
            "currency": "aud",
            "destination": "cli-merchant",
            "provider": "payid",
        },
    )
    trust_id = pilot.json()["result"]["trust"]["trust_id"]

    class _Response:
        def __init__(self, response):
            self.response = response

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return self.response.content

    requested_paths: list[str] = []

    def fake_urlopen(url, timeout: int = 20):
        assert timeout == 20
        full_url = url.full_url if hasattr(url, "full_url") else str(url)
        headers = dict(getattr(url, "header_items", lambda: [])())
        if full_url.endswith(f"/trust/explorer/{trust_id}"):
            assert headers.get("Accept") == "application/json"
        path = full_url.replace("http://testserver", "")
        requested_paths.append(path)
        return _Response(client.get(path, headers=headers))

    monkeypatch.setattr(novatrust_verifier_cli.request, "urlopen", fake_urlopen)

    exit_code = novatrust_verifier_cli.run(
        [
            "--base-url",
            "http://testserver",
            "--trust-id",
            trust_id,
            "--write-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    assert "NovaTrust verification: PASS" in capsys.readouterr().out
    assert f"/trust/explorer/{trust_id}" in requested_paths
    assert f"/v1/core-platform/trust/explorer/{trust_id}" not in requested_paths
    assert (tmp_path / "packet.json").exists()
    assert (tmp_path / "verification-result.json").exists()
