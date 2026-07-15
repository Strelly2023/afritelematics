"""In-memory repositories for focused runtime tests."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from afritech.novaride_runtime.common.errors import DuplicateCommand
from afritech.novaride_runtime.common.idempotency import IdempotencyRecord
from afritech.novaride_runtime.events.envelope import MobilityEvent
from afritech.novaride_runtime.models import Aggregate

T = TypeVar("T", bound=Aggregate)


@dataclass(slots=True)
class MemoryRepository(Generic[T]):
    records: dict[str, T] = field(default_factory=dict)

    def save(self, aggregate: T) -> T:
        self.records[aggregate.id] = deepcopy(aggregate)
        return deepcopy(aggregate)

    def get(self, aggregate_id: str) -> T | None:
        item = self.records.get(aggregate_id)
        return deepcopy(item) if item is not None else None

    def list(self, *, tenant_id: str | None = None) -> list[T]:
        values = self.records.values()
        if tenant_id is not None:
            values = [item for item in values if item.tenant_id == tenant_id]
        return deepcopy(list(values))


@dataclass(slots=True)
class MemoryEventRepository:
    events: list[MobilityEvent] = field(default_factory=list)
    event_ids: set[str] = field(default_factory=set)

    def append(self, event: MobilityEvent) -> MobilityEvent:
        if event.event_id in self.event_ids:
            return event
        self.events.append(event)
        self.event_ids.add(event.event_id)
        return event

    def all(self) -> list[MobilityEvent]:
        return list(self.events)

    def by_aggregate(self, aggregate_id: str) -> list[MobilityEvent]:
        return [event for event in self.events if event.aggregate_id == aggregate_id]

    def by_correlation(self, correlation_id: str) -> list[MobilityEvent]:
        return [event for event in self.events if event.correlation_id == correlation_id]


@dataclass(slots=True)
class MemoryIdempotencyRepository:
    records: dict[tuple[str, str], IdempotencyRecord] = field(default_factory=dict)

    def get(self, tenant_id: str, key: str) -> IdempotencyRecord | None:
        return self.records.get((tenant_id, key))

    def put(self, record: IdempotencyRecord) -> None:
        existing = self.records.get((record.tenant_id, record.key))
        if existing and existing.command_hash != record.command_hash:
            raise DuplicateCommand("idempotency_key_reused_with_different_payload")
        self.records[(record.tenant_id, record.key)] = record


@dataclass(slots=True)
class RuntimeRepositories:
    riders: MemoryRepository = field(default_factory=MemoryRepository)
    drivers: MemoryRepository = field(default_factory=MemoryRepository)
    eligibility: MemoryRepository = field(default_factory=MemoryRepository)
    availability: MemoryRepository = field(default_factory=MemoryRepository)
    shifts: MemoryRepository = field(default_factory=MemoryRepository)
    offers: MemoryRepository = field(default_factory=MemoryRepository)
    bookings: MemoryRepository = field(default_factory=MemoryRepository)
    fare_quotes: MemoryRepository = field(default_factory=MemoryRepository)
    trips: MemoryRepository = field(default_factory=MemoryRepository)
    emergencies: MemoryRepository = field(default_factory=MemoryRepository)
    incidents: MemoryRepository = field(default_factory=MemoryRepository)
    fleets: MemoryRepository = field(default_factory=MemoryRepository)
    fleet_vehicles: MemoryRepository = field(default_factory=MemoryRepository)
    fleet_compliance: MemoryRepository = field(default_factory=MemoryRepository)
    deliveries: MemoryRepository = field(default_factory=MemoryRepository)
    corporate_accounts: MemoryRepository = field(default_factory=MemoryRepository)
    corporate_bookings: MemoryRepository = field(default_factory=MemoryRepository)
    transit_journeys: MemoryRepository = field(default_factory=MemoryRepository)
    operator_commands: MemoryRepository = field(default_factory=MemoryRepository)
    events: MemoryEventRepository = field(default_factory=MemoryEventRepository)
    idempotency: MemoryIdempotencyRepository = field(default_factory=MemoryIdempotencyRepository)
