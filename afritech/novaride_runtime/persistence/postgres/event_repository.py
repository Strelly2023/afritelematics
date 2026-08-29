"""Synchronous PostgreSQL persistence for NovaRide mobility events.

The runtime contract mirrors ``MemoryEventRepository``:

    append(event)
    all()
    by_aggregate(aggregate_id)
    by_correlation(correlation_id)

``mobility_events`` is authoritative for durable NovaRide mobility events.

The transactional broker outbox is deliberately not absorbed here.
``mobility_event_outbox`` remains a separate publication-durability concern
and must be certified separately before production activation.
"""

from __future__ import annotations

from psycopg.types.json import Jsonb

from typing import Any, Mapping

from afritech.novaride_runtime.persistence.postgres.connection import (
    PostgresConnectionProtocol,
)


def _mobility_event_type():
    # Lazy import avoids broadening import topology at module import time.
    from afritech.novaride_runtime.events.envelope import MobilityEvent

    return MobilityEvent


def _row_mapping(
    cursor: Any,
    row: Any,
) -> Mapping[str, Any]:
    """Normalize mapping and positional PostgreSQL result rows."""

    if isinstance(row, Mapping):
        return dict(row)

    description = cursor.description

    if description is None:
        raise RuntimeError(
            "event_query_missing_cursor_description"
        )

    return {
        column.name: value
        for column, value in zip(
            description,
            row,
            strict=True,
        )
    }


def _event_from_row(
    row: Mapping[str, Any],
):
    MobilityEvent = _mobility_event_type()

    values = {
        "event_id": str(row["event_id"]),
        "event_type": str(row["event_type"]),
        "aggregate_id": str(row["aggregate_id"]),
        "aggregate_type": str(row["aggregate_type"]),
        "aggregate_version": int(
            row["aggregate_version"]
        ),
        "occurred_at": row["occurred_at"],
        "tenant_id": str(row["tenant_id"]),
        "region": str(row["region_code"]),
        "actor_type": str(row["actor_type"]),
        "actor_id": str(row["actor_id"]),
        "correlation_id": str(
            row["correlation_id"]
        ),
        "causation_id": (
            None
            if row.get("causation_id") is None
            else str(row["causation_id"])
        ),
        "schema_version": str(
            row["schema_version"]
        ),
        "payload": dict(
            row.get("payload") or {}
        ),
        "integrity_hash": str(
            row["integrity_hash"]
        ),
    }

    return MobilityEvent(
        **values
    )


class PostgresEventRepository:
    """Synchronous mobility-event repository."""

    table = "mobility_events"

    def __init__(
        self,
        connection: PostgresConnectionProtocol,
    ) -> None:
        self.connection = connection

    def append(
        self,
        event,
    ):
        self.connection.execute(
            """
            INSERT INTO mobility_events (
                event_id,
                event_type,
                aggregate_id,
                aggregate_type,
                aggregate_version,
                occurred_at,
                tenant_id,
                region_code,
                actor_type,
                actor_id,
                correlation_id,
                causation_id,
                schema_version,
                payload,
                integrity_hash
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
            ON CONFLICT (event_id) DO NOTHING
            """,
            (
                event.event_id,
                event.event_type,
                event.aggregate_id,
                event.aggregate_type,
                event.aggregate_version,
                event.occurred_at,
                event.tenant_id,
                event.region,
                event.actor_type,
                event.actor_id,
                event.correlation_id,
                event.causation_id,
                event.schema_version,
                Jsonb(event.payload),
                event.integrity_hash,
            ),
        )

        return event

    def all(
        self,
    ) -> list[Any]:
        cursor = self.connection.execute(
            """
            SELECT *
            FROM mobility_events
            ORDER BY occurred_at ASC, event_id ASC
            """
        )

        return [
            _event_from_row(
                _row_mapping(cursor, row)
            )
            for row in cursor.fetchall()
        ]

    def by_aggregate(
        self,
        aggregate_id: str,
    ) -> list[Any]:
        cursor = self.connection.execute(
            """
            SELECT *
            FROM mobility_events
            WHERE aggregate_id = %s
            ORDER BY occurred_at ASC, event_id ASC
            """,
            (
                aggregate_id,
            ),
        )

        return [
            _event_from_row(
                _row_mapping(cursor, row)
            )
            for row in cursor.fetchall()
        ]

    def by_correlation(
        self,
        correlation_id: str,
    ) -> list[Any]:
        cursor = self.connection.execute(
            """
            SELECT *
            FROM mobility_events
            WHERE correlation_id = %s
            ORDER BY occurred_at ASC, event_id ASC
            """,
            (
                correlation_id,
            ),
        )

        return [
            _event_from_row(
                _row_mapping(cursor, row)
            )
            for row in cursor.fetchall()
        ]


__all__ = [
    "PostgresEventRepository",
]
