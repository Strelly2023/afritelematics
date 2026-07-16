"""Secret reference handling for integration providers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class SecretReference:
    secret_ref: str


@dataclass(frozen=True, slots=True)
class SecretValue:
    secret_ref: str
    value: str


@dataclass(frozen=True, slots=True)
class SecretAccessContext:
    product_code: str
    provider_id: str
    environment: str
    region: str
    tenant_id: str | None = None


class SecretResolver(Protocol):
    async def resolve(self, secret_ref: str, context: SecretAccessContext) -> str: ...

