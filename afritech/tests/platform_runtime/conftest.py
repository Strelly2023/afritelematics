from __future__ import annotations

from collections.abc import Awaitable, Mapping
from types import ModuleType
from typing import Any

from fastapi import APIRouter

from afritech.platform_runtime import (
    EventConsumerDefinition,
    InfrastructureKind,
    InfrastructureRequirement,
    ProductHealthCheck,
    ProductMigration,
    WorkerDefinition,
)


async def _command_handler(payload: Mapping[str, Any], context: Any) -> dict[str, Any]:
    return {"payload": dict(payload), "tenant_id": context.tenant_id, "product_code": context.product_code}


async def _query_handler(parameters: Mapping[str, Any], context: Any) -> dict[str, Any]:
    return {"parameters": dict(parameters), "tenant_id": context.tenant_id, "product_code": context.product_code}


async def _worker_handler(context: Any) -> None:
    return None


class FakeProductBackend:
    product_code = "novafleet"
    version = "2026.07.0"

    def command_handlers(self) -> Mapping[str, Any]:
        return {"RegisterFleetVehicle": _command_handler}

    def query_handlers(self) -> Mapping[str, Any]:
        return {"GetFleetVehicle": _query_handler}

    def routers(self) -> tuple[APIRouter, ...]:
        router = APIRouter(prefix="/v1/novafleet", tags=["novafleet"])

        @router.get("/ping")
        def ping() -> dict[str, str]:
            return {"status": "ok"}

        return (router,)

    def workers(self) -> tuple[WorkerDefinition, ...]:
        return (
            WorkerDefinition(
                name="fleet-worker",
                product_code=self.product_code,
                handler=_worker_handler,
                queue="novafleet.jobs",
                dead_letter_queue="novafleet.dlq",
            ),
        )

    def consumers(self) -> tuple[EventConsumerDefinition, ...]:
        return (
            EventConsumerDefinition(
                name="fleet-consumer",
                product_code=self.product_code,
                topic="novatech.fleet.events",
                group="novafleet",
            ),
        )

    def health_checks(self) -> tuple[ProductHealthCheck, ...]:
        return (ProductHealthCheck(check_id="fleet-health", name="fleet health"),)

    def infrastructure_requirements(self) -> tuple[InfrastructureRequirement, ...]:
        return (
            InfrastructureRequirement(
                id="novafleet-postgres",
                product_code=self.product_code,
                kind=InfrastructureKind.POSTGRES_SCHEMA,
                name="novafleet",
                required=True,
                configuration={"schema": "novafleet"},
                desired_state="present",
                ownership="product",
                region="AU",
            ),
        )

    def migrations(self) -> tuple[ProductMigration, ...]:
        return (
            ProductMigration(
                migration_id="novafleet-0001",
                version=self.version,
                checksum="sha256:" + "1" * 64,
                approved=True,
                destructive=False,
            ),
        )

    async def startup(self, context: Any) -> None:
        return None

    async def shutdown(self) -> None:
        return None

    def configuration_schema(self) -> dict[str, Any]:
        return {
            "schema_name": "novafleet-config",
            "schema_version": 1,
            "fields": [
                {"name": "maintenance_reminder_days", "type": "integer", "default": 30, "required": False},
            ],
        }


def build_fake_module(name: str = "afritech.products.novafleet") -> ModuleType:
    module = ModuleType(name)

    def get_product_backend() -> FakeProductBackend:
        return FakeProductBackend()

    module.get_product_backend = get_product_backend  # type: ignore[attr-defined]
    module.__file__ = f"/virtual/{name.replace('.', '/')}.py"
    return module

