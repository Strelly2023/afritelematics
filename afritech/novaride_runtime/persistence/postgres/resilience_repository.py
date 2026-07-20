"""PostgreSQL resilience repositories.

These adapters define the production SQL boundary. They require an injected
connection implementing execute/fetch methods, so tests can verify SQL shape
without pretending a live PostgreSQL service exists.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Protocol

from afritech.novaride_runtime.models import (
    ConflictRecord,
    FailoverEvent,
    OfflineOperation,
    ProviderHealthRecord,
    ProviderRouteDecision,
    ResilienceEvidence,
    SyncSession,
)


class AsyncConnection(Protocol):
    async def execute(self, query: str, *args: Any) -> Any: ...
    async def fetchrow(self, query: str, *args: Any) -> Any: ...
    async def fetch(self, query: str, *args: Any) -> list[Any]: ...


@dataclass(slots=True)
class PostgresOfflineOperationRepository:
    connection: AsyncConnection

    async def save(self, operation: OfflineOperation) -> None:
        await self.connection.execute(
            """
            INSERT INTO novaride_offline_operations (
                id, tenant_id, organization_id, region_code, actor_id,
                operation_type, encrypted_payload, payload_hash, idempotency_key,
                authority_required, conflict_policy, status, attempt_count,
                next_attempt_at, last_error_code, priority, created_at, updated_at
            )
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18)
            ON CONFLICT (tenant_id, idempotency_key) DO UPDATE SET
                status = EXCLUDED.status,
                attempt_count = EXCLUDED.attempt_count,
                next_attempt_at = EXCLUDED.next_attempt_at,
                last_error_code = EXCLUDED.last_error_code,
                updated_at = EXCLUDED.updated_at
            """,
            operation.id,
            operation.tenant_id,
            operation.organization_id,
            operation.region_code,
            operation.actor_id,
            operation.operation_type,
            operation.encrypted_payload,
            operation.payload_hash,
            operation.idempotency_key,
            operation.authority_required,
            operation.conflict_policy,
            operation.status,
            operation.attempt_count,
            operation.next_attempt_at,
            operation.last_error_code,
            operation.priority,
            operation.created_at,
            operation.updated_at,
        )

    async def get_by_idempotency_key(
        self, tenant_id: str, idempotency_key: str
    ) -> dict[str, Any] | None:
        row = await self.connection.fetchrow(
            """
            SELECT * FROM novaride_offline_operations
            WHERE tenant_id = $1 AND idempotency_key = $2
            """,
            tenant_id,
            idempotency_key,
        )
        return dict(row) if row else None

    async def claim_pending(self, *, region_code: str, limit: int) -> list[dict[str, Any]]:
        rows = await self.connection.fetch(
            """
            UPDATE novaride_offline_operations
            SET status = 'UPLOADING', updated_at = now()
            WHERE id IN (
                SELECT id FROM novaride_offline_operations
                WHERE region_code = $1
                  AND status LIKE 'QUEUED%'
                  AND (next_attempt_at IS NULL OR next_attempt_at <= now())
                ORDER BY
                    CASE priority
                        WHEN 'EMERGENCY' THEN 0
                        WHEN 'HIGH' THEN 1
                        ELSE 2
                    END,
                    created_at
                LIMIT $2
                FOR UPDATE SKIP LOCKED
            )
            RETURNING *
            """,
            region_code,
            limit,
        )
        return [dict(row) for row in rows]

    async def mark_synced(self, operation_id: str) -> None:
        await self.connection.execute(
            """
            UPDATE novaride_offline_operations
            SET status = 'SYNCED', updated_at = now()
            WHERE id = $1
            """,
            operation_id,
        )

    async def mark_failed(
        self, operation_id: str, *, error_code: str, next_attempt_at: datetime
    ) -> None:
        await self.connection.execute(
            """
            UPDATE novaride_offline_operations
            SET status = 'QUEUED_RETRY',
                attempt_count = attempt_count + 1,
                last_error_code = $2,
                next_attempt_at = $3,
                updated_at = now()
            WHERE id = $1
            """,
            operation_id,
            error_code,
            next_attempt_at,
        )


def offline_operation_record(operation: OfflineOperation) -> dict[str, Any]:
    return asdict(operation)


__all__ = ["PostgresOfflineOperationRepository", "offline_operation_record"]


@dataclass(slots=True)
class PostgresResilienceEvidenceRepository:
    connection: AsyncConnection

    async def save(self, evidence: ResilienceEvidence) -> None:
        await self.connection.execute(
            """
            INSERT INTO novaride_resilience_evidence (
                id, tenant_id, organization_id, region_code, capability,
                degraded_mode, decision, fallback_used, evidence, correlation_id,
                evidence_hash, created_at
            )
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
            ON CONFLICT (id) DO NOTHING
            """,
            evidence.id,
            evidence.tenant_id,
            evidence.organization_id,
            evidence.region_code,
            evidence.capability,
            evidence.degraded_mode.value,
            evidence.decision,
            evidence.fallback_used,
            evidence.evidence,
            None,
            evidence.evidence_hash,
            evidence.created_at,
        )

    async def list(self, *, tenant_id: str, region_code: str | None = None) -> list[dict[str, Any]]:
        if region_code:
            rows = await self.connection.fetch(
                "SELECT * FROM novaride_resilience_evidence WHERE tenant_id = $1 AND region_code = $2 ORDER BY created_at DESC",
                tenant_id,
                region_code,
            )
        else:
            rows = await self.connection.fetch(
                "SELECT * FROM novaride_resilience_evidence WHERE tenant_id = $1 ORDER BY created_at DESC",
                tenant_id,
            )
        return [dict(row) for row in rows]


@dataclass(slots=True)
class PostgresProviderHealthRepository:
    connection: AsyncConnection

    async def save(self, record: ProviderHealthRecord) -> None:
        await self.connection.execute(
            """
            INSERT INTO novaride_provider_health (
                id, tenant_id, organization_id, region_code, provider, capability,
                state, latency_ms, error_rate, timeout_rate, success_rate,
                consecutive_failures, consecutive_successes, last_successful_probe_at,
                last_state_transition_at, created_at, updated_at
            )
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17)
            ON CONFLICT (id) DO UPDATE SET
                state = EXCLUDED.state,
                latency_ms = EXCLUDED.latency_ms,
                error_rate = EXCLUDED.error_rate,
                timeout_rate = EXCLUDED.timeout_rate,
                success_rate = EXCLUDED.success_rate,
                consecutive_failures = EXCLUDED.consecutive_failures,
                consecutive_successes = EXCLUDED.consecutive_successes,
                last_successful_probe_at = EXCLUDED.last_successful_probe_at,
                last_state_transition_at = EXCLUDED.last_state_transition_at,
                updated_at = EXCLUDED.updated_at
            """,
            record.id,
            record.tenant_id,
            record.organization_id,
            record.region_code,
            record.provider,
            record.capability,
            record.state.value,
            record.latency_ms,
            record.error_rate,
            record.timeout_rate,
            record.success_rate,
            record.consecutive_failures,
            record.consecutive_successes,
            record.last_successful_probe_at,
            record.last_state_transition_at,
            record.created_at,
            record.updated_at,
        )

    async def latest(
        self, *, tenant_id: str, region_code: str, provider: str, capability: str
    ) -> dict[str, Any] | None:
        row = await self.connection.fetchrow(
            """
            SELECT * FROM novaride_provider_health
            WHERE tenant_id = $1 AND region_code = $2 AND provider = $3 AND capability = $4
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            tenant_id,
            region_code,
            provider,
            capability,
        )
        return dict(row) if row else None


@dataclass(slots=True)
class PostgresProviderRouteDecisionRepository:
    connection: AsyncConnection

    async def save(self, decision: ProviderRouteDecision) -> None:
        await self.connection.execute(
            """
            INSERT INTO novaride_provider_route_decisions (
                id, tenant_id, organization_id, region_code, capability,
                selected_provider, attempted_providers, degraded_mode, reason,
                evidence_hash, created_at, updated_at
            )
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
            ON CONFLICT (id) DO NOTHING
            """,
            decision.id,
            decision.tenant_id,
            decision.organization_id,
            decision.region_code,
            decision.capability,
            decision.selected_provider,
            list(decision.attempted_providers),
            decision.degraded_mode.value,
            decision.reason,
            decision.evidence_hash,
            decision.created_at,
            decision.updated_at,
        )

    async def list(self, *, tenant_id: str, region_code: str) -> list[dict[str, Any]]:
        rows = await self.connection.fetch(
            """
            SELECT * FROM novaride_provider_route_decisions
            WHERE tenant_id = $1 AND region_code = $2
            ORDER BY created_at DESC
            """,
            tenant_id,
            region_code,
        )
        return [dict(row) for row in rows]


@dataclass(slots=True)
class PostgresSyncSessionRepository:
    connection: AsyncConnection

    async def save(self, session: SyncSession) -> None:
        await self.connection.execute(
            """
            INSERT INTO novaride_sync_sessions (
                id, tenant_id, organization_id, region_code, device_id,
                last_server_cursor, server_cursor, status, operation_count,
                created_at, updated_at
            )
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
            ON CONFLICT (id) DO UPDATE SET
                server_cursor = EXCLUDED.server_cursor,
                status = EXCLUDED.status,
                operation_count = EXCLUDED.operation_count,
                updated_at = EXCLUDED.updated_at
            """,
            session.id,
            session.tenant_id,
            session.organization_id,
            session.region_code,
            session.device_id,
            session.last_server_cursor,
            session.server_cursor,
            session.status,
            session.operation_count,
            session.created_at,
            session.updated_at,
        )

    async def get(self, *, tenant_id: str, sync_id: str) -> dict[str, Any] | None:
        row = await self.connection.fetchrow(
            "SELECT * FROM novaride_sync_sessions WHERE tenant_id = $1 AND id = $2",
            tenant_id,
            sync_id,
        )
        return dict(row) if row else None


@dataclass(slots=True)
class PostgresSyncConflictRepository:
    connection: AsyncConnection

    async def save(self, conflict: ConflictRecord) -> None:
        await self.connection.execute(
            """
            INSERT INTO novaride_sync_conflicts (
                id, tenant_id, organization_id, region_code, sync_session_id,
                operation_id, domain, local_version, server_version,
                policy_selected, winner, reason, correlation_id, created_at, updated_at
            )
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
            ON CONFLICT (id) DO UPDATE SET
                policy_selected = EXCLUDED.policy_selected,
                winner = EXCLUDED.winner,
                reason = EXCLUDED.reason,
                updated_at = EXCLUDED.updated_at
            """,
            conflict.id,
            conflict.tenant_id,
            conflict.organization_id,
            conflict.region_code,
            conflict.sync_session_id,
            conflict.operation_id,
            conflict.domain,
            conflict.local_version,
            conflict.server_version,
            conflict.policy_selected,
            conflict.winner,
            conflict.reason,
            conflict.correlation_id,
            conflict.created_at,
            conflict.updated_at,
        )

    async def list_unresolved(self, *, tenant_id: str, region_code: str) -> list[dict[str, Any]]:
        rows = await self.connection.fetch(
            """
            SELECT * FROM novaride_sync_conflicts
            WHERE tenant_id = $1 AND region_code = $2 AND reason NOT LIKE 'resolved_by_%'
            ORDER BY created_at
            """,
            tenant_id,
            region_code,
        )
        return [dict(row) for row in rows]


@dataclass(slots=True)
class PostgresFailoverEventRepository:
    connection: AsyncConnection

    async def save(self, event: FailoverEvent) -> None:
        await self.connection.execute(
            """
            INSERT INTO novaride_failover_events (
                id, tenant_id, organization_id, region_code, previous_state,
                target_state, reason, automatic, approval_reference, evidence_hash,
                created_at, updated_at
            )
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
            ON CONFLICT (id) DO NOTHING
            """,
            event.id,
            event.tenant_id,
            event.organization_id,
            event.region_code,
            event.previous_state.value,
            event.target_state.value,
            event.reason,
            event.automatic,
            event.approval_reference,
            event.evidence_hash,
            event.created_at,
            event.updated_at,
        )


@dataclass(slots=True)
class PostgresResilienceOutboxRepository:
    connection: AsyncConnection

    async def claim_batch(self, *, worker_id: str, limit: int) -> list[dict[str, Any]]:
        rows = await self.connection.fetch(
            """
            UPDATE novaride_resilience_outbox
            SET state = 'CLAIMED', worker_id = $1, claimed_at = now()
            WHERE outbox_id IN (
                SELECT outbox_id FROM novaride_resilience_outbox
                WHERE state IN ('PENDING','FAILED') AND next_attempt_at <= now()
                ORDER BY created_at
                LIMIT $2
                FOR UPDATE SKIP LOCKED
            )
            RETURNING *
            """,
            worker_id,
            limit,
        )
        return [dict(row) for row in rows]

    async def mark_published(self, outbox_id: str, *, broker_ack: str) -> None:
        await self.connection.execute(
            "UPDATE novaride_resilience_outbox SET state = 'PUBLISHED', published_at = now(), broker_ack = $2 WHERE outbox_id = $1",
            outbox_id,
            broker_ack,
        )

    async def mark_failed(self, outbox_id: str, *, error: str, exhausted: bool) -> None:
        state = "DEAD_LETTERED" if exhausted else "FAILED"
        await self.connection.execute(
            """
            UPDATE novaride_resilience_outbox
            SET state = $2, attempts = attempts + 1, last_error = $3, next_attempt_at = now() + interval '30 seconds'
            WHERE outbox_id = $1
            """,
            outbox_id,
            state,
            error,
        )


__all__ = [
    "PostgresOfflineOperationRepository",
    "PostgresResilienceEvidenceRepository",
    "PostgresProviderHealthRepository",
    "PostgresProviderRouteDecisionRepository",
    "PostgresSyncSessionRepository",
    "PostgresSyncConflictRepository",
    "PostgresFailoverEventRepository",
    "PostgresResilienceOutboxRepository",
    "offline_operation_record",
]
