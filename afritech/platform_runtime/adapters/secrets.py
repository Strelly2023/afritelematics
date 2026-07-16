"""Secret manager adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

from ..errors import ProductSecretAccessDenied


@dataclass(frozen=True, slots=True)
class SecretReference:
    name: str
    secret_ref: str


@dataclass
class SecretManagerAdapter:
    provider: str
    endpoint: str = ""
    token: str = ""
    name: str = "secrets"
    kind: str = "secrets"

    async def resolve(self, secret_ref: str, *, product_code: str, tenant_id: str, region: str, actor_id: str, purpose: str) -> str:
        parsed = urlparse(secret_ref)
        if not secret_ref or not parsed.scheme:
            raise ProductSecretAccessDenied("invalid_secret_ref")
        if product_code not in secret_ref and parsed.scheme not in {"env", "file"}:
            raise ProductSecretAccessDenied("secret_namespace_mismatch")
        if parsed.scheme == "env":
            import os

            key = parsed.path.lstrip("/")
            if key in os.environ:
                return os.environ[key]
            raise ProductSecretAccessDenied("secret_not_found")
        if parsed.scheme == "file":
            path = parsed.path
            return open(path, "r", encoding="utf-8").read().strip()
        if parsed.scheme == "vault":
            if not self.endpoint:
                raise ProductSecretAccessDenied("secret_provider_unavailable")
            async with httpx.AsyncClient(timeout=20, headers={"X-Vault-Token": self.token} if self.token else {}) as client:
                resp = await client.get(f"{self.endpoint.rstrip('/')}/v1/{parsed.path.lstrip('/')}")
                if resp.status_code >= 400:
                    raise ProductSecretAccessDenied("secret_not_found")
                payload = resp.json()
                return payload.get("data", {}).get("data", {}).get("value", "")
        raise ProductSecretAccessDenied("secret_provider_unavailable")

