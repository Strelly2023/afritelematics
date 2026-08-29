"""Synchronous PostgreSQL runtime idempotency persistence.

This adapter mirrors ``MemoryIdempotencyRepository`` and binds only to
``idempotency_records``.

``novaride_runtime_idempotency`` belongs to the replay/control-plane
persistence authority and is intentionally not absorbed here.
"""

from __future__ import annotations

from psycopg.types.json import Jsonb

from typing import Any, Mapping

from afritech.novaride_runtime.common.idempotency import (
    IdempotencyRecord,
)
from afritech.novaride_runtime.persistence.postgres.connection import (
    PostgresConnectionProtocol,
)


def _duplicate_command_type():
    from afritech.novaride_runtime.common.errors import DuplicateCommand

    return DuplicateCommand


def _record_from_row(
    row: Mapping[str, Any],
) -> IdempotencyRecord:
    return IdempotencyRecord(
        tenant_id=str(
            row["tenant_id"]
        ),
        key=str(
            row["idempotency_key"]
        ),
        command_hash=str(
            row["command_hash"]
        ),
        result=dict(
            row.get("result") or {}
        ),
    )


class PostgresIdempotencyRepository:
    """Synchronous runtime idempotency repository."""

    table = "idempotency_records"

    def __init__(
        self,
        connection: PostgresConnectionProtocol,
    ) -> None:
        self.connection = connection

    def get(
        self,
        tenant_id: str,
        key: str,
    ) -> IdempotencyRecord | None:
        cursor = self.connection.execute(
            """
            SELECT
                tenant_id,
                idempotency_key,
                command_hash,
                result
            FROM idempotency_records
            WHERE tenant_id = %s
              AND idempotency_key = %s
            """,
            (
                tenant_id,
                key,
            ),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        if isinstance(row, Mapping):
            row_mapping = dict(row)
        else:
            description = cursor.description

            if description is None:
                raise RuntimeError(
                    "idempotency_query_missing_cursor_description"
                )

            row_mapping = {
                column.name: value
                for column, value in zip(
                    description,
                    row,
                    strict=True,
                )
            }

        return _record_from_row(
            row_mapping
        )

    def put(
        self,
        record: IdempotencyRecord,
    ) -> None:
        existing = self.get(
            record.tenant_id,
            record.key,
        )

        if (
            existing is not None
            and existing.command_hash
            != record.command_hash
        ):
            DuplicateCommand = (
                _duplicate_command_type()
            )

            raise DuplicateCommand(
                "idempotency_key_reused_with_different_payload"
            )

        if existing is not None:
            return

        self.connection.execute(
            """
            INSERT INTO idempotency_records (
                tenant_id,
                idempotency_key,
                command_hash,
                result
            )
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (
                tenant_id,
                idempotency_key
            )
            DO NOTHING
            """,
            (
                record.tenant_id,
                record.key,
                record.command_hash,
                Jsonb(record.result),
            ),
        )


__all__ = [
    "PostgresIdempotencyRepository",
]
