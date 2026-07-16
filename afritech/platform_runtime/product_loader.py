"""Dynamic product module loader for NovaTech runtimes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import importlib
import inspect
from pathlib import Path
from types import ModuleType
from typing import Any

from .compatibility import CompatibilityValidator
from .contracts import NovaTechProductBackend
from .errors import ProductContractViolation, ProductLoadRejected
from .models import LoadedProduct, ProductRuntimeState
from .registry import BackendProductRegistration, CommandRegistry, QueryRegistry
from .route_registry import RouteRegistry
from .worker_registry import WorkerRegistry


APPROVED_PREFIXES = (
    "afritech.products.",
    "afritech.novaride_runtime.",
    "afritech.core_platform.",
    "afritech.novacodepro.",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _module_checksum(module: ModuleType) -> str:
    source = getattr(module, "__file__", "") or module.__name__
    return "sha256:" + hashlib.sha256(source.encode("utf-8")).hexdigest()


def _build_command_name(handler: Any) -> str:
    return getattr(handler, "__name__", handler.__class__.__name__)


class ProductModuleLoader:
    def __init__(
        self,
        compatibility_validator: CompatibilityValidator | None = None,
        route_registry: RouteRegistry | None = None,
        command_registry: CommandRegistry | None = None,
        query_registry: QueryRegistry | None = None,
        worker_registry: WorkerRegistry | None = None,
    ) -> None:
        self._compatibility = compatibility_validator or CompatibilityValidator()
        self._route_registry = route_registry or RouteRegistry()
        self._command_registry = command_registry or CommandRegistry()
        self._query_registry = query_registry or QueryRegistry()
        self._worker_registry = worker_registry or WorkerRegistry()

    def load(self, registration: BackendProductRegistration) -> LoadedProduct:
        if registration.status not in {
            "APPROVED",
            "PROVISIONING",
            "DEPLOYED",
            "VERIFYING",
            "ACTIVE",
        }:
            raise ProductLoadRejected(f"product_not_loadable:{registration.status}")
        if not registration.module_name.startswith(APPROVED_PREFIXES):
            raise ProductContractViolation("module_prefix_not_allowed")
        module = importlib.import_module(registration.module_name)
        factory = getattr(module, "get_product_backend", None)
        if factory is None or not callable(factory):
            raise ProductContractViolation("missing_get_product_backend")
        backend = factory()
        if not isinstance(backend, NovaTechProductBackend):
            raise ProductContractViolation("backend_does_not_implement_contract")
        if backend.product_code.lower() != registration.product_code.lower():
            raise ProductContractViolation("product_code_mismatch")
        if str(backend.version) != str(registration.version):
            raise ProductContractViolation("version_mismatch")
        self._compatibility.validate(registration, backend)
        routers = tuple(backend.routers())
        self._route_registry.validate_product_routes(registration.product_code, routers)
        commands = dict(backend.command_handlers())
        queries = dict(backend.query_handlers())
        for command_name, handler in commands.items():
            self._command_registry.register(registration.product_code, type(f"{registration.product_code}:{command_name}", (), {}), handler)
        for query_name, handler in queries.items():
            self._query_registry.register(registration.product_code, type(f"{registration.product_code}:{query_name}", (), {}), handler)
        workers = tuple(backend.workers())
        for worker in workers:
            self._worker_registry.register(worker)
        consumers = tuple(backend.consumers())
        health_checks = tuple(backend.health_checks())
        backend_routes = tuple(routers)
        return LoadedProduct(
            product_code=registration.product_code,
            version=registration.version,
            registration=registration,
            backend=backend,
            commands=commands,
            queries=queries,
            routers=backend_routes,
            workers=workers,
            consumers=consumers,
            health_checks=health_checks,
            loaded_at=_now(),
            module_checksum=_module_checksum(module),
            state=ProductRuntimeState.LOADED,
        )


__all__ = ["APPROVED_PREFIXES", "ProductModuleLoader"]
