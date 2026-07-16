"""Health snapshots for API platform registry."""

from __future__ import annotations

from typing import Any

from .endpoint_registry import EndpointRegistry


class ApiHealthService:
    def __init__(self, registry: EndpointRegistry) -> None:
        self.registry = registry

    def snapshot(self) -> dict[str, Any]:
        return {"status": "ready" if self.registry.list_all() else "empty", "registry": self.registry.health_snapshot()}
