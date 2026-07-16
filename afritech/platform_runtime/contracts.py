"""Runtime contracts for executable NovaTech product modules."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any, Protocol, runtime_checkable

from fastapi import APIRouter

from .models import (
    EventConsumerDefinition,
    ExecutionContext,
    InfrastructureRequirement,
    ProductHealthCheck,
    ProductMigration,
    ProductStartupContext,
    WorkerDefinition,
    WorkerExecutionContext,
)

CommandHandler = Callable[[Mapping[str, Any], ExecutionContext], Awaitable[Any] | Any]
QueryHandler = Callable[[Mapping[str, Any], ExecutionContext], Awaitable[Any] | Any]
WorkerHandler = Callable[[WorkerExecutionContext], Awaitable[None] | None]


@runtime_checkable
class NovaTechProductBackend(Protocol):
    product_code: str
    version: str

    def command_handlers(self) -> Mapping[str, CommandHandler]: ...

    def query_handlers(self) -> Mapping[str, QueryHandler]: ...

    def routers(self) -> Sequence[APIRouter]: ...

    def workers(self) -> Sequence[WorkerDefinition]: ...

    def consumers(self) -> Sequence[EventConsumerDefinition]: ...

    def health_checks(self) -> Sequence[ProductHealthCheck]: ...

    def infrastructure_requirements(self) -> Sequence[InfrastructureRequirement]: ...

    def migrations(self) -> Sequence[ProductMigration]: ...

    async def startup(self, context: ProductStartupContext) -> None: ...

    async def shutdown(self) -> None: ...


@runtime_checkable
class ProductBackendFactory(Protocol):
    def __call__(self) -> NovaTechProductBackend: ...


__all__ = [
    "CommandHandler",
    "NovaTechProductBackend",
    "ProductBackendFactory",
    "QueryHandler",
    "WorkerHandler",
]
