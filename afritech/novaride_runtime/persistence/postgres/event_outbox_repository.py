"""Synchronous PostgreSQL persistence for NovaRide mobility-event outbox.

This repository owns only ``mobility_event_outbox``.

It deliberately does not own transaction commit/rollback. A shared
``PostgresUnitOfWork`` owns the transaction so ``mobility_events`` and
``mobility_event_outbox`` can commit atomically.

``novaride_resilience_outbox`` remains a separate persistence authority.
"""

from __future__ import annotations

from typing import Any

from psycopg.types.json import Jsonb

from afritech.novaride_runtime.persistence.postgres.connection import (
    PostgresConnectionProtocol,
)


class PostgresEventOutboxRepository:
    table = "mobility_event_outbox"

    def __init__(
        self,
        connection: PostgresConnectionProtocol,
    ) -> None:
        self.connection = connection

    def append(
        self,
        event,
    ):
        """Persist publication intent exactly once per event."""

        self.connection.execute(
            """
            INSERT INTO mobility_event_outbox (
                outbox_id,
                event_id,
                tenant_id,
                region_code,
                state,
                payload
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                'PENDING',
                %s
            )
            ON CONFLICT (event_id) DO NOTHING
            """,
            (
                f"outbox_{event.event_id}",
                event.event_id,
                event.tenant_id,
                event.region,
                Jsonb({
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "aggregate_id": event.aggregate_id,
                    "aggregate_type": event.aggregate_type,
                    "aggregate_version": (
                        event.aggregate_version
                    ),
                    "occurred_at": (
                        event.occurred_at.isoformat()
                        if hasattr(
                            event.occurred_at,
                            "isoformat",
                        )
                        else str(event.occurred_at)
                    ),
                    "tenant_id": event.tenant_id,
                    "region_code": event.region,
                    "actor_type": event.actor_type,
                    "actor_id": event.actor_id,
                    "correlation_id": (
                        event.correlation_id
                    ),
                    "causation_id": (
                        event.causation_id
                    ),
                    "schema_version": (
                        event.schema_version
                    ),
                    "payload": event.payload,
                    "integrity_hash": (
                        event.integrity_hash
                    ),
                }),
            ),
        )

        return event

    def claim_batch(
        self,
        *,
        worker_id: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        cursor = self.connection.execute(
            """
            WITH candidates AS (
                SELECT outbox_id
                FROM mobility_event_outbox
                WHERE state IN ('PENDING', 'FAILED')
                  AND next_attempt_at <= now()
                ORDER BY created_at ASC, outbox_id ASC
                FOR UPDATE SKIP LOCKED
                LIMIT %s
            )
            UPDATE mobility_event_outbox AS outbox
            SET
                state = 'CLAIMED',
                worker_id = %s,
                claimed_at = now(),
                attempts = attempts + 1
            FROM candidates
            WHERE outbox.outbox_id = candidates.outbox_id
            RETURNING outbox.*
            """,
            (
                limit,
                worker_id,
            ),
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    def mark_published(
        self,
        event_id: str,
        *,
        broker_ack: str,
    ) -> None:
        self.connection.execute(
            """
            UPDATE mobility_event_outbox
            SET
                state = 'PUBLISHED',
                published_at = now(),
                broker_ack = %s,
                last_error = NULL
            WHERE event_id = %s
              AND state <> 'PUBLISHED'
            """,
            (
                broker_ack,
                event_id,
            ),
        )

    def mark_failed(
        self,
        event_id: str,
        *,
        error: str,
    ) -> None:
        self.connection.execute(
            """
            UPDATE mobility_event_outbox
            SET
                state = 'FAILED',
                worker_id = NULL,
                claimed_at = NULL,
                last_error = %s,
                next_attempt_at = now()
            WHERE event_id = %s
              AND state <> 'PUBLISHED'
            """,
            (
                error,
                event_id,
            ),
        )


__all__ = [
    "PostgresEventOutboxRepository",
]
