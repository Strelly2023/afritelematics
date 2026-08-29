"""Tenant-scoped PostgreSQL authoritative event source for replay.

This adapter deliberately owns no database connection and no global
tenant context.

Every replay lookup:

* receives the authoritative tenant_id from the persisted replay plan;
* opens one short-lived PostgresRuntimeSession;
* lets that session apply transaction-local RLS tenant authority;
* reads from the certified runtime repository bundle;
* exits the session deterministically.

The long-lived object is only PostgresRuntimeSessionFactory.
"""

from __future__ import annotations

from typing import Any

from afritech.novaride_runtime.persistence.postgres.runtime_session import (
    PostgresRuntimeSessionFactory,
)


class TenantScopedPostgresReplayEventSource:
    """Read authoritative mobility events inside tenant-scoped sessions."""

    def __init__(
        self,
        session_factory: PostgresRuntimeSessionFactory,
    ) -> None:
        self.session_factory = session_factory

    def by_correlation_for_tenant(
        self,
        *,
        tenant_id: str,
        correlation_id: str,
    ) -> list[Any]:
        if not tenant_id or not tenant_id.strip():
            raise RuntimeError(
                "replay_event_source_tenant_id_required"
            )

        with self.session_factory.session(
            tenant_id=tenant_id,
        ) as session:
            return list(
                session.repositories.events.by_correlation(
                    correlation_id
                )
            )

    def by_aggregate_for_tenant(
        self,
        *,
        tenant_id: str,
        aggregate_id: str,
    ) -> list[Any]:
        if not tenant_id or not tenant_id.strip():
            raise RuntimeError(
                "replay_event_source_tenant_id_required"
            )

        with self.session_factory.session(
            tenant_id=tenant_id,
        ) as session:
            return list(
                session.repositories.events.by_aggregate(
                    aggregate_id
                )
            )


__all__ = [
    "TenantScopedPostgresReplayEventSource",
]
