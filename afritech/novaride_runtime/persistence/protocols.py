"""Repository protocols."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, TypeVar

from afritech.novaride_runtime.events.envelope import MobilityEvent
from afritech.novaride_runtime.models import (
    Aggregate,
    ConflictRecord,
    FailoverEvent,
    OfflineOperation,
    ProviderHealthRecord,
    ProviderRouteDecision,
    ResilienceEvidence,
    SyncSession,
)

T = TypeVar("T", bound=Aggregate)


class Repository(Protocol[T]):
    def save(self, aggregate: T) -> T: ...
    def get(self, aggregate_id: str) -> T | None: ...
    def list(self, *, tenant_id: str | None = None) -> list[T]: ...


class EventRepository(Protocol):
    def append(self, event: MobilityEvent) -> MobilityEvent: ...
    def all(self) -> list[MobilityEvent]: ...
    def by_aggregate(self, aggregate_id: str) -> list[MobilityEvent]: ...
    def by_correlation(self, correlation_id: str) -> list[MobilityEvent]: ...


class OfflineOperationRepository(Protocol):
    def save(self, operation: OfflineOperation) -> OfflineOperation: ...
    def get(self, operation_id: str) -> OfflineOperation | None: ...
    def get_by_idempotency_key(
        self, tenant_id: str, idempotency_key: str
    ) -> OfflineOperation | None: ...
    def claim_pending(
        self, *, region_code: str, limit: int, now: datetime | None = None
    ) -> list[OfflineOperation]: ...
    def mark_synced(self, operation_id: str) -> None: ...
    def mark_failed(
        self, operation_id: str, *, error_code: str, next_attempt_at: datetime
    ) -> None: ...


class ResilienceEvidenceRepository(Protocol):
    def save(self, evidence: ResilienceEvidence) -> ResilienceEvidence: ...
    def list(self, *, tenant_id: str | None = None) -> list[ResilienceEvidence]: ...


class ProviderHealthRepository(Protocol):
    def save(self, record: ProviderHealthRecord) -> ProviderHealthRecord: ...
    def latest(
        self, *, provider: str, capability: str, tenant_id: str | None = None
    ) -> ProviderHealthRecord | None: ...


class ProviderRouteDecisionRepository(Protocol):
    def save(self, decision: ProviderRouteDecision) -> ProviderRouteDecision: ...


class SyncSessionRepository(Protocol):
    def save(self, session: SyncSession) -> SyncSession: ...
    def get(self, sync_id: str) -> SyncSession | None: ...


class ConflictRecordRepository(Protocol):
    def save(self, conflict: ConflictRecord) -> ConflictRecord: ...
    def get(self, conflict_id: str) -> ConflictRecord | None: ...


class FailoverEventRepository(Protocol):
    def save(self, event: FailoverEvent) -> FailoverEvent: ...
