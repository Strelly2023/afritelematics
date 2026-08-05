"""Persistence-neutral NovaLogistics repository contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Generic, Protocol, TypeVar

from .domain import Entity, Identifier, LifecycleAggregate


Persisted = TypeVar("Persisted", bound=Entity | LifecycleAggregate)


class RepositoryError(RuntimeError):
    """Base public persistence error."""


class AggregateNotFoundError(RepositoryError):
    pass


class AggregateAlreadyExistsError(RepositoryError):
    pass


class OptimisticConcurrencyError(RepositoryError):
    pass


class DuplicateBusinessKeyError(RepositoryError):
    pass


class TenantScopeError(RepositoryError):
    pass


class SerializationError(RepositoryError):
    pass


class UnsupportedSchemaVersionError(SerializationError):
    pass


class MigrationError(RepositoryError):
    pass


class OutboxError(RepositoryError):
    pass


@dataclass(frozen=True)
class Page:
    limit: int = 100
    offset: int = 0

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 500:
            raise RepositoryError("page limit must be between 1 and 500")
        if self.offset < 0:
            raise RepositoryError("page offset cannot be negative")


@dataclass(frozen=True)
class AggregateQuery:
    page: Page = Page()
    status: str | None = None
    business_key: str | None = None
    updated_from: datetime | None = None
    updated_to: datetime | None = None
    descending: bool = False


class AggregateRepository(Protocol, Generic[Persisted]):
    def add(self, aggregate: Persisted, *, business_key: str | None = None) -> None: ...
    def get(self, tenant_id: Identifier, aggregate_id: Identifier) -> Persisted: ...
    def exists(self, tenant_id: Identifier, aggregate_id: Identifier) -> bool: ...
    def list(self, tenant_id: Identifier, query: AggregateQuery = AggregateQuery()) -> tuple[Persisted, ...]: ...
    def count(self, tenant_id: Identifier, query: AggregateQuery = AggregateQuery()) -> int: ...
    def find_by_business_key(self, tenant_id: Identifier, business_key: str) -> Persisted: ...
    def save(self, aggregate: Persisted, *, expected_version: int) -> None: ...


class CustomerRepository(AggregateRepository["Entity"], Protocol): pass
class SupplierRepository(AggregateRepository["Entity"], Protocol): pass
class CarrierRepository(AggregateRepository["Entity"], Protocol): pass
class DriverRepository(AggregateRepository["Entity"], Protocol): pass
class VehicleRepository(AggregateRepository["Entity"], Protocol): pass
class WarehouseRepository(AggregateRepository["Entity"], Protocol): pass
class ShipmentRepository(AggregateRepository["LifecycleAggregate"], Protocol): pass
class LoadRepository(AggregateRepository["LifecycleAggregate"], Protocol): pass
class StopRepository(AggregateRepository["LifecycleAggregate"], Protocol): pass
class DeliveryRepository(AggregateRepository["LifecycleAggregate"], Protocol): pass
class OrderRepository(AggregateRepository["LifecycleAggregate"], Protocol): pass
class QuoteRepository(AggregateRepository["LifecycleAggregate"], Protocol): pass
class IncidentRepository(AggregateRepository["LifecycleAggregate"], Protocol): pass
class ClaimRepository(AggregateRepository["LifecycleAggregate"], Protocol): pass
