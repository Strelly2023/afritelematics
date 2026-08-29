"""Synchronous PostgreSQL repositories for NovaRide resilience runtime state.

This module serves the synchronous ``RuntimeRepositories`` contract used by
``ResilienceService``.

It deliberately does not replace the existing asynchronous resilience
repositories in ``resilience_repository.py``. Those adapters retain authority
for worker-oriented concerns such as SKIP LOCKED claiming, retry processing,
and resilience outbox publication.

The canonical resilience migration predates several common Aggregate metadata
fields. Where the SQL schema does not carry ``aggregate_version`` or
``schema_version``, reconstruction uses the canonical domain defaults:
aggregate_version=1 and schema_version="2026.2".

``OfflineOperation.replayable`` is likewise reconstructed as its canonical
domain default ``True`` because no canonical SQL column currently exists.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping

from psycopg.types.json import Jsonb

from afritech.novaride_runtime.models import (
    ConflictRecord,
    DegradedMode,
    FailoverEvent,
    FailoverState,
    OfflineOperation,
    ProviderHealthRecord,
    ProviderRouteDecision,
    ProviderState,
    ResilienceEvidence,
    SyncSession,
)
from afritech.novaride_runtime.persistence.postgres.base_repository import (
    PostgresAggregateRepository,
    SyncPostgresConnection,
    _row_to_mapping,
)


CANONICAL_AGGREGATE_VERSION = 1
CANONICAL_SCHEMA_VERSION = "2026.2"


def _offline_to_record(
    value: OfflineOperation,
) -> Mapping[str, Any]:
    return {
        "id": value.id,
        "tenant_id": value.tenant_id,
        "organization_id": value.organization_id,
        "region_code": value.region_code,
        "actor_id": value.actor_id,
        "operation_type": value.operation_type,
        "encrypted_payload": Jsonb(value.encrypted_payload),
        "payload_hash": value.payload_hash,
        "idempotency_key": value.idempotency_key,
        "authority_required": value.authority_required,
        "conflict_policy": value.conflict_policy,
        "status": value.status,
        "attempt_count": value.attempt_count,
        "next_attempt_at": value.next_attempt_at,
        "last_error_code": value.last_error_code,
        "priority": value.priority,
        "created_at": value.created_at,
        "updated_at": value.updated_at,
    }


def _offline_from_record(
    row: Mapping[str, Any],
) -> OfflineOperation:
    return OfflineOperation(
        id=str(row["id"]),
        tenant_id=str(row["tenant_id"]),
        organization_id=str(row["organization_id"]),
        region_code=str(row["region_code"]),
        aggregate_version=CANONICAL_AGGREGATE_VERSION,
        schema_version=CANONICAL_SCHEMA_VERSION,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        actor_id=str(row["actor_id"]),
        operation_type=str(row["operation_type"]),
        encrypted_payload=dict(
            row.get("encrypted_payload") or {}
        ),
        payload_hash=str(row["payload_hash"]),
        idempotency_key=str(row["idempotency_key"]),
        authority_required=bool(
            row["authority_required"]
        ),
        status=str(row["status"]),
        conflict_policy=str(row["conflict_policy"]),
        replayable=True,
        attempt_count=int(
            row.get("attempt_count", 0)
        ),
        next_attempt_at=row.get("next_attempt_at"),
        last_error_code=row.get("last_error_code"),
        priority=str(
            row.get("priority", "NORMAL")
        ),
    )


def _evidence_to_record(
    value: ResilienceEvidence,
) -> Mapping[str, Any]:
    return {
        "id": value.id,
        "tenant_id": value.tenant_id,
        "organization_id": value.organization_id,
        "region_code": value.region_code,
        "capability": value.capability,
        "degraded_mode": value.degraded_mode.value,
        "decision": value.decision,
        "fallback_used": value.fallback_used,
        "evidence": Jsonb(value.evidence),
        "correlation_id": None,
        "evidence_hash": value.evidence_hash,
        "created_at": value.created_at,
    }


def _evidence_from_record(
    row: Mapping[str, Any],
) -> ResilienceEvidence:
    created_at = row["created_at"]

    return ResilienceEvidence(
        id=str(row["id"]),
        tenant_id=str(row["tenant_id"]),
        organization_id=str(row["organization_id"]),
        region_code=str(row["region_code"]),
        aggregate_version=CANONICAL_AGGREGATE_VERSION,
        schema_version=CANONICAL_SCHEMA_VERSION,
        created_at=created_at,
        updated_at=created_at,
        capability=str(row["capability"]),
        degraded_mode=DegradedMode(
            str(row["degraded_mode"])
        ),
        decision=str(row["decision"]),
        fallback_used=(
            None
            if row.get("fallback_used") is None
            else str(row["fallback_used"])
        ),
        evidence=dict(
            row.get("evidence") or {}
        ),
        evidence_hash=str(row["evidence_hash"]),
    )


def _provider_health_to_record(
    value: ProviderHealthRecord,
) -> Mapping[str, Any]:
    return {
        "id": value.id,
        "tenant_id": value.tenant_id,
        "organization_id": value.organization_id,
        "region_code": value.region_code,
        "provider": value.provider,
        "capability": value.capability,
        "state": value.state.value,
        "latency_ms": value.latency_ms,
        "error_rate": value.error_rate,
        "timeout_rate": value.timeout_rate,
        "success_rate": value.success_rate,
        "consecutive_failures":
            value.consecutive_failures,
        "consecutive_successes":
            value.consecutive_successes,
        "last_successful_probe_at":
            value.last_successful_probe_at,
        "last_state_transition_at":
            value.last_state_transition_at,
        "created_at": value.created_at,
        "updated_at": value.updated_at,
    }


def _provider_health_from_record(
    row: Mapping[str, Any],
) -> ProviderHealthRecord:
    return ProviderHealthRecord(
        id=str(row["id"]),
        tenant_id=str(row["tenant_id"]),
        organization_id=str(row["organization_id"]),
        region_code=str(row["region_code"]),
        aggregate_version=CANONICAL_AGGREGATE_VERSION,
        schema_version=CANONICAL_SCHEMA_VERSION,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        provider=str(row["provider"]),
        capability=str(row["capability"]),
        state=ProviderState(
            str(row["state"])
        ),
        latency_ms=int(
            row.get("latency_ms", 0)
        ),
        error_rate=Decimal(
            str(row.get("error_rate", 0))
        ),
        timeout_rate=Decimal(
            str(row.get("timeout_rate", 0))
        ),
        success_rate=Decimal(
            str(row.get("success_rate", 1))
        ),
        consecutive_failures=int(
            row.get(
                "consecutive_failures",
                0,
            )
        ),
        consecutive_successes=int(
            row.get(
                "consecutive_successes",
                0,
            )
        ),
        last_successful_probe_at=row.get(
            "last_successful_probe_at"
        ),
        last_state_transition_at=row.get(
            "last_state_transition_at"
        ),
    )


def _provider_route_to_record(
    value: ProviderRouteDecision,
) -> Mapping[str, Any]:
    return {
        "id": value.id,
        "tenant_id": value.tenant_id,
        "organization_id": value.organization_id,
        "region_code": value.region_code,
        "capability": value.capability,
        "selected_provider": value.selected_provider,
        "attempted_providers": Jsonb(
            list(value.attempted_providers)
        ),
        "degraded_mode": value.degraded_mode.value,
        "reason": value.reason,
        "evidence_hash": value.evidence_hash,
        "created_at": value.created_at,
        "updated_at": value.updated_at,
    }


def _provider_route_from_record(
    row: Mapping[str, Any],
) -> ProviderRouteDecision:
    return ProviderRouteDecision(
        id=str(row["id"]),
        tenant_id=str(row["tenant_id"]),
        organization_id=str(row["organization_id"]),
        region_code=str(row["region_code"]),
        aggregate_version=CANONICAL_AGGREGATE_VERSION,
        schema_version=CANONICAL_SCHEMA_VERSION,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        capability=str(row["capability"]),
        selected_provider=(
            None
            if row.get("selected_provider") is None
            else str(row["selected_provider"])
        ),
        attempted_providers=tuple(
            str(item)
            for item in (
                row.get("attempted_providers")
                or ()
            )
        ),
        degraded_mode=DegradedMode(
            str(row["degraded_mode"])
        ),
        reason=str(row["reason"]),
        evidence_hash=str(row["evidence_hash"]),
    )


def _sync_session_to_record(
    value: SyncSession,
) -> Mapping[str, Any]:
    return {
        "id": value.id,
        "tenant_id": value.tenant_id,
        "organization_id": value.organization_id,
        "region_code": value.region_code,
        "device_id": value.device_id,
        "last_server_cursor":
            value.last_server_cursor,
        "server_cursor": value.server_cursor,
        "status": value.status,
        "operation_count": value.operation_count,
        "created_at": value.created_at,
        "updated_at": value.updated_at,
    }


def _sync_session_from_record(
    row: Mapping[str, Any],
) -> SyncSession:
    return SyncSession(
        id=str(row["id"]),
        tenant_id=str(row["tenant_id"]),
        organization_id=str(row["organization_id"]),
        region_code=str(row["region_code"]),
        aggregate_version=CANONICAL_AGGREGATE_VERSION,
        schema_version=CANONICAL_SCHEMA_VERSION,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        device_id=str(row["device_id"]),
        last_server_cursor=(
            None
            if row.get("last_server_cursor") is None
            else str(row["last_server_cursor"])
        ),
        server_cursor=str(row["server_cursor"]),
        status=str(row["status"]),
        operation_count=int(
            row.get("operation_count", 0)
        ),
    )


def _conflict_to_record(
    value: ConflictRecord,
) -> Mapping[str, Any]:
    return {
        "id": value.id,
        "tenant_id": value.tenant_id,
        "organization_id": value.organization_id,
        "region_code": value.region_code,
        "sync_session_id": value.sync_session_id,
        "operation_id": value.operation_id,
        "domain": value.domain,
        "local_version": value.local_version,
        "server_version": value.server_version,
        "policy_selected": value.policy_selected,
        "winner": value.winner,
        "reason": value.reason,
        "correlation_id": value.correlation_id,
        "created_at": value.created_at,
        "updated_at": value.updated_at,
    }


def _conflict_from_record(
    row: Mapping[str, Any],
) -> ConflictRecord:
    return ConflictRecord(
        id=str(row["id"]),
        tenant_id=str(row["tenant_id"]),
        organization_id=str(row["organization_id"]),
        region_code=str(row["region_code"]),
        aggregate_version=CANONICAL_AGGREGATE_VERSION,
        schema_version=CANONICAL_SCHEMA_VERSION,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        sync_session_id=str(
            row["sync_session_id"]
        ),
        operation_id=str(row["operation_id"]),
        domain=str(row["domain"]),
        local_version=int(row["local_version"]),
        server_version=int(row["server_version"]),
        policy_selected=str(
            row["policy_selected"]
        ),
        winner=str(row["winner"]),
        reason=str(row["reason"]),
        correlation_id=(
            None
            if row.get("correlation_id") is None
            else str(row["correlation_id"])
        ),
    )


def _failover_to_record(
    value: FailoverEvent,
) -> Mapping[str, Any]:
    return {
        "id": value.id,
        "tenant_id": value.tenant_id,
        "organization_id": value.organization_id,
        "region_code": value.region_code,
        "previous_state": value.previous_state.value,
        "target_state": value.target_state.value,
        "reason": value.reason,
        "automatic": value.automatic,
        "approval_reference":
            value.approval_reference,
        "evidence_hash": value.evidence_hash,
        "created_at": value.created_at,
        "updated_at": value.updated_at,
    }


def _failover_from_record(
    row: Mapping[str, Any],
) -> FailoverEvent:
    return FailoverEvent(
        id=str(row["id"]),
        tenant_id=str(row["tenant_id"]),
        organization_id=str(row["organization_id"]),
        region_code=str(row["region_code"]),
        aggregate_version=CANONICAL_AGGREGATE_VERSION,
        schema_version=CANONICAL_SCHEMA_VERSION,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        previous_state=FailoverState(
            str(row["previous_state"])
        ),
        target_state=FailoverState(
            str(row["target_state"])
        ),
        reason=str(row["reason"]),
        automatic=bool(row["automatic"]),
        approval_reference=(
            None
            if row.get("approval_reference") is None
            else str(row["approval_reference"])
        ),
        evidence_hash=str(row["evidence_hash"]),
    )


class PostgresRuntimeOfflineOperationRepository(
    PostgresAggregateRepository[OfflineOperation]
):
    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="novaride_offline_operations",
            id_column="id",
            to_record=_offline_to_record,
            from_record=_offline_from_record,
        )

    def get_by_idempotency_key(
        self,
        tenant_id: str,
        idempotency_key: str,
    ) -> OfflineOperation | None:
        cursor = self.connection.execute(
            "SELECT * FROM novaride_offline_operations "
            "WHERE tenant_id = %s "
            "AND idempotency_key = %s "
            "ORDER BY updated_at DESC "
            "LIMIT 1",
            (
                tenant_id,
                idempotency_key,
            ),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return _offline_from_record(
            _row_to_mapping(cursor, row)
        )


class PostgresRuntimeResilienceEvidenceRepository(
    PostgresAggregateRepository[ResilienceEvidence]
):
    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="novaride_resilience_evidence",
            id_column="id",
            to_record=_evidence_to_record,
            from_record=_evidence_from_record,
        )


class PostgresRuntimeProviderHealthRepository(
    PostgresAggregateRepository[ProviderHealthRecord]
):
    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="novaride_provider_health",
            id_column="id",
            to_record=_provider_health_to_record,
            from_record=_provider_health_from_record,
        )

    def latest(
        self,
        *,
        provider: str,
        capability: str,
        tenant_id: str | None = None,
    ) -> ProviderHealthRecord | None:
        conditions = [
            "provider = %s",
            "capability = %s",
        ]

        params: list[Any] = [
            provider,
            capability,
        ]

        if tenant_id is not None:
            conditions.append(
                "tenant_id = %s"
            )

            params.append(
                tenant_id
            )

        query = (
            "SELECT * FROM novaride_provider_health "
            "WHERE "
            + " AND ".join(conditions)
            + " ORDER BY updated_at DESC LIMIT 1"
        )

        cursor = self.connection.execute(
            query,
            tuple(params),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return _provider_health_from_record(
            _row_to_mapping(cursor, row)
        )


class PostgresRuntimeProviderRouteRepository(
    PostgresAggregateRepository[ProviderRouteDecision]
):
    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="novaride_provider_route_decisions",
            id_column="id",
            to_record=_provider_route_to_record,
            from_record=_provider_route_from_record,
        )


class PostgresRuntimeSyncSessionRepository(
    PostgresAggregateRepository[SyncSession]
):
    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="novaride_sync_sessions",
            id_column="id",
            to_record=_sync_session_to_record,
            from_record=_sync_session_from_record,
        )


class PostgresRuntimeConflictRecordRepository(
    PostgresAggregateRepository[ConflictRecord]
):
    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="novaride_sync_conflicts",
            id_column="id",
            to_record=_conflict_to_record,
            from_record=_conflict_from_record,
        )


class PostgresRuntimeFailoverEventRepository(
    PostgresAggregateRepository[FailoverEvent]
):
    def __init__(
        self,
        connection: SyncPostgresConnection,
    ) -> None:
        super().__init__(
            connection=connection,
            table="novaride_failover_events",
            id_column="id",
            to_record=_failover_to_record,
            from_record=_failover_from_record,
        )


__all__ = [
    "PostgresRuntimeOfflineOperationRepository",
    "PostgresRuntimeResilienceEvidenceRepository",
    "PostgresRuntimeProviderHealthRepository",
    "PostgresRuntimeProviderRouteRepository",
    "PostgresRuntimeSyncSessionRepository",
    "PostgresRuntimeConflictRecordRepository",
    "PostgresRuntimeFailoverEventRepository",
]
