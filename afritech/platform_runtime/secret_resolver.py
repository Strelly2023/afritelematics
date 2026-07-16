"""Secret resolution contracts for NovaTech product runtimes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

from .errors import ProductSecretAccessDenied


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class SecretAccessContext:
    product_code: str
    tenant_id: str
    region: str
    actor_id: str
    purpose: str
    correlation_id: str = ""


@dataclass
class InMemorySecretResolver:
    secrets: dict[str, str] = field(default_factory=dict)

    async def resolve(self, secret_ref: str, context: SecretAccessContext) -> str:
        if not secret_ref.startswith(f"vault://{context.product_code}/") and f"/{context.product_code}/" not in secret_ref:
            raise ProductSecretAccessDenied("secret_namespace_mismatch")
        if secret_ref not in self.secrets:
            raise ProductSecretAccessDenied("secret_not_found")
        return self.secrets[secret_ref]


class SecretResolver(Protocol):
    async def resolve(self, secret_ref: str, context: SecretAccessContext) -> str: ...


__all__ = ["InMemorySecretResolver", "SecretAccessContext", "SecretResolver"]
