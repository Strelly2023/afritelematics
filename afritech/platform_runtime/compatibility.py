"""Compatibility validation for executable NovaTech product packages."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping

from .errors import ProductContractViolation
from .models import InfrastructureRequirement, RouteRegistration, WorkerDefinition


class CompatibilityClass(StrEnum):
    ADDITIVE = "ADDITIVE"
    COMPATIBLE = "COMPATIBLE"
    CONTROLLED = "CONTROLLED"
    BREAKING = "BREAKING"
    FORBIDDEN = "FORBIDDEN"


@dataclass(frozen=True, slots=True)
class CompatibilityFinding:
    kind: CompatibilityClass
    code: str
    message: str
    detail: Mapping[str, Any]


class CompatibilityValidator:
    protected_prefixes = (
        "/v1/platform",
        "/v1/identity",
        "/v1/governance",
        "/v1/audit",
        "/v1/evidence",
        "/v1/internal",
        "/health",
        "/metrics",
        "/docs",
        "/openapi.json",
    )

    def validate(self, registration: Any, backend: Any) -> tuple[CompatibilityFinding, ...]:
        findings: list[CompatibilityFinding] = []
        if getattr(backend, "product_code", "").lower() != registration.product_code.lower():
            raise ProductContractViolation("product_code_mismatch")
        if getattr(backend, "version", "") != registration.version:
            raise ProductContractViolation("version_mismatch")
        declared_commands = set(registration.registered_commands)
        backend_commands = set(getattr(backend, "command_handlers")().keys())
        removed_commands = declared_commands - backend_commands
        if removed_commands:
            findings.append(
                CompatibilityFinding(
                    CompatibilityClass.BREAKING,
                    "removed_commands",
                    "registered commands are missing from backend",
                    {"commands": sorted(removed_commands)},
                )
            )
        declared_queries = set(registration.registered_queries)
        backend_queries = set(getattr(backend, "query_handlers")().keys())
        removed_queries = declared_queries - backend_queries
        if removed_queries:
            findings.append(
                CompatibilityFinding(
                    CompatibilityClass.BREAKING,
                    "removed_queries",
                    "registered queries are missing from backend",
                    {"queries": sorted(removed_queries)},
                )
            )
        for route in getattr(backend, "routers")():
            for route_info in getattr(route, "routes", []):
                path = getattr(route_info, "path", "")
                if any(path.startswith(prefix) for prefix in self.protected_prefixes):
                    raise ProductContractViolation("protected_route_prefix")
        return tuple(findings)

    def route_compatible(self, registration: Any, routes: tuple[RouteRegistration, ...]) -> None:
        for route in routes:
            if any(route.path.startswith(prefix) for prefix in self.protected_prefixes):
                raise ProductContractViolation("protected_route_prefix")
            if not route.path.startswith(registration.api_prefix):
                raise ProductContractViolation("route_prefix_mismatch")

    def worker_compatible(self, workers: tuple[WorkerDefinition, ...]) -> None:
        for worker in workers:
            if not worker.queue.startswith(worker.product_code):
                raise ProductContractViolation("worker_queue_namespace_mismatch")

    def infrastructure_compatible(self, requirements: tuple[InfrastructureRequirement, ...], registration: Any) -> None:
        for requirement in requirements:
            if requirement.product_code.lower() != registration.product_code.lower():
                raise ProductContractViolation("infrastructure_product_mismatch")


__all__ = [
    "CompatibilityClass",
    "CompatibilityFinding",
    "CompatibilityValidator",
]
