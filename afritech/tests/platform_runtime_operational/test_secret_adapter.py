from __future__ import annotations

import asyncio

import pytest

from afritech.platform_runtime.adapters.secrets import SecretManagerAdapter


def test_secret_adapter_reads_env_and_file(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOVAFLEET_API_KEY", "secret-value")
    adapter = SecretManagerAdapter(provider="local")
    assert asyncio.run(adapter.resolve("env:///NOVAFLEET_API_KEY", product_code="novafleet", tenant_id="tenant-a", region="AU", actor_id="actor-a", purpose="test")) == "secret-value"

    secret_file = tmp_path / "secret.txt"
    secret_file.write_text("file-secret", encoding="utf-8")
    assert asyncio.run(adapter.resolve(f"file://{secret_file}", product_code="novafleet", tenant_id="tenant-a", region="AU", actor_id="actor-a", purpose="test")) == "file-secret"

    with pytest.raises(Exception, match="secret_namespace_mismatch"):
        asyncio.run(adapter.resolve("vault://novapay/providers/onafriq/api-key", product_code="novafleet", tenant_id="tenant-a", region="AU", actor_id="actor-a", purpose="test"))

