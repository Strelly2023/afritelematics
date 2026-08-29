"""Settings-driven persistence selection for NovaRide.

This module selects persistence capability without opening PostgreSQL
connections or starting runtime-lifetime transactions.

Memory mode returns the canonical in-memory runtime.

PostgreSQL mode returns a long-lived PostgresRuntimeSessionFactory. Each
business operation must create its own tenant-scoped PostgresRuntimeSession.

Production activation and live infrastructure connectivity are deliberately
outside this module.
"""

from __future__ import annotations

from dataclasses import dataclass

from afritech.novaride_runtime.config import (
    NovaRideRuntimeSettings,
    PersistenceAdapter,
)
from afritech.novaride_runtime.persistence.postgres.runtime_session import (
    PostgresRuntimeSessionFactory,
    PostgresRuntimeSessionConfig,
)
from afritech.novaride_runtime.services import (
    NovaRideRuntime,
    create_runtime,
)


@dataclass(frozen=True, slots=True)
class MemoryRuntimeSelection:
    runtime: NovaRideRuntime


@dataclass(frozen=True, slots=True)
class PostgresRuntimeSelection:
    session_factory: PostgresRuntimeSessionFactory


RuntimePersistenceSelection = (
    MemoryRuntimeSelection
    | PostgresRuntimeSelection
)


def select_runtime_persistence(
    settings: NovaRideRuntimeSettings,
) -> RuntimePersistenceSelection:
    """Select runtime persistence from validated settings.

    Selection itself does not establish database connectivity.
    """

    settings.validate()

    if (
        settings.persistence_adapter
        is PersistenceAdapter.MEMORY
    ):
        return MemoryRuntimeSelection(
            runtime=create_runtime()
        )

    if (
        settings.persistence_adapter
        is PersistenceAdapter.POSTGRESQL
    ):
        if (
            not settings.postgres_dsn
            or not settings.postgres_dsn.strip()
        ):
            raise RuntimeError(
                "postgres_dsn_required"
            )

        config = PostgresRuntimeSessionConfig(
            dsn=settings.postgres_dsn,
        )

        return PostgresRuntimeSelection(
            session_factory=(
                PostgresRuntimeSessionFactory(
                    config
                )
            )
        )

    raise RuntimeError(
        "unsupported_persistence_adapter"
    )


__all__ = [
    "MemoryRuntimeSelection",
    "PostgresRuntimeSelection",
    "RuntimePersistenceSelection",
    "select_runtime_persistence",
]
