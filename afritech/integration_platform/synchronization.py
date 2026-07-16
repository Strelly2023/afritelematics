"""Synchronization state for background imports and exports."""

from __future__ import annotations

from dataclasses import dataclass, field

from .contracts import SynchronizationDefinition


@dataclass(frozen=True, slots=True)
class SynchronizationState:
    sync_id: str
    status: str
    last_cursor: str | None = None
    last_attempted_cursor: str | None = None
    last_success_at: str | None = None
    failure_count: int = 0
    records_processed: int = 0
    records_rejected: int = 0


@dataclass(slots=True)
class SynchronizationCoordinator:
    definitions: dict[str, SynchronizationDefinition] = field(default_factory=dict)
    states: dict[str, SynchronizationState] = field(default_factory=dict)

    def register(self, definition: SynchronizationDefinition) -> SynchronizationDefinition:
        self.definitions[definition.sync_id] = definition
        self.states.setdefault(definition.sync_id, SynchronizationState(sync_id=definition.sync_id, status="PENDING"))
        return definition

    def mark(self, sync_id: str, *, status: str, cursor: str | None = None, processed: int = 0, rejected: int = 0) -> SynchronizationState:
        state = self.states[sync_id]
        self.states[sync_id] = SynchronizationState(
            sync_id=sync_id,
            status=status,
            last_cursor=cursor or state.last_cursor,
            last_attempted_cursor=cursor or state.last_attempted_cursor,
            last_success_at=state.last_success_at,
            failure_count=state.failure_count + (1 if status == "FAILED" else 0),
            records_processed=state.records_processed + processed,
            records_rejected=state.records_rejected + rejected,
        )
        return self.states[sync_id]

