"""In-memory repositories for focused runtime tests."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Generic, TypeVar

from afritech.novaride_runtime.common.clocks import utc_now
from afritech.novaride_runtime.common.errors import DuplicateCommand
from afritech.novaride_runtime.common.idempotency import IdempotencyRecord
from afritech.novaride_runtime.events.envelope import MobilityEvent
from afritech.novaride_runtime.models import Aggregate, OfflineOperation, ProviderHealthRecord

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
class MemoryOfflineOperationRepository(MemoryRepository[OfflineOperation]):
    def get_by_idempotency_key(self, tenant_id: str, idempotency_key: str) -> OfflineOperation | None:
        for item in self.records.values():
            if item.tenant_id == tenant_id and item.idempotency_key == idempotency_key:
                return deepcopy(item)
        return None

    def claim_pending(self, *, region_code: str, limit: int, now: datetime | None = None) -> list[OfflineOperation]:
        current_time = now or utc_now()
        pending: list[OfflineOperation] = []
        for item in self.records.values():
            if len(pending) >= limit:
                break
            if item.region_code != region_code or not item.status.startswith("QUEUED"):
                continue
            if item.next_attempt_at is not None and item.next_attempt_at > current_time:
                continue
            claimed = deepcopy(item)
            claimed.status = "UPLOADING"
            claimed.touch()
            self.records[item.id] = deepcopy(claimed)
            pending.append(deepcopy(claimed))
        return pending

    def mark_synced(self, operation_id: str) -> None:
        item = self.records[operation_id]
        item.status = "SYNCED"
        item.touch()
        self.records[operation_id] = deepcopy(item)

    def mark_failed(self, operation_id: str, *, error_code: str, next_attempt_at: datetime) -> None:
        item = self.records[operation_id]
        item.status = "QUEUED_RETRY"
        item.attempt_count += 1
        item.last_error_code = error_code
        item.next_attempt_at = next_attempt_at
        item.touch()
        self.records[operation_id] = deepcopy(item)


@dataclass(slots=True)
class MemoryProviderHealthRepository(MemoryRepository[ProviderHealthRecord]):
    def latest(self, *, provider: str, capability: str, tenant_id: str | None = None) -> ProviderHealthRecord | None:
        matches = [
            item
            for item in self.records.values()
            if item.provider == provider
            and item.capability == capability
            and (tenant_id is None or item.tenant_id == tenant_id)
        ]
        if not matches:
            return None
        return deepcopy(sorted(matches, key=lambda item: item.updated_at)[-1])


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
    offline_operations: MemoryOfflineOperationRepository = field(default_factory=MemoryOfflineOperationRepository)
    resilience_evidence: MemoryRepository = field(default_factory=MemoryRepository)
    provider_health: MemoryProviderHealthRepository = field(default_factory=MemoryProviderHealthRepository)
    provider_routes: MemoryRepository = field(default_factory=MemoryRepository)
    sync_sessions: MemoryRepository = field(default_factory=MemoryRepository)
    conflict_records: MemoryRepository = field(default_factory=MemoryRepository)
    failover_events: MemoryRepository = field(default_factory=MemoryRepository)
    events: MemoryEventRepository = field(default_factory=MemoryEventRepository)
    idempotency: MemoryIdempotencyRepository = field(default_factory=MemoryIdempotencyRepository)
