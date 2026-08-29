"""Per-operation PostgreSQL runtime composition for NovaRide.

The bridge creates a short-lived NovaRideRuntime inside one already-certified
PostgresRuntimeSession.

Lifecycle:

    session factory
        -> tenant-scoped session
        -> open UnitOfWork
        -> apply RLS tenant context
        -> create PostgreSQL RuntimeRepositories bundle
        -> create transaction-bound PostgresEventFabric
        -> inject dependencies into NovaRideRuntime
        -> execute one operation
        -> outer session commits or rolls back
        -> close connection

The runtime returned inside the callback must not escape the operation scope.

This module deliberately does not:

* keep a PostgreSQL runtime globally;
* keep a PostgreSQL connection globally;
* keep a UnitOfWork globally;
* pin tenant state globally;
* alter runtime settings;
* activate Kafka;
* perform production activation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TypeVar

from afritech.novaride_runtime.persistence.postgres.event_fabric import (
    PostgresEventFabric,
)
from afritech.novaride_runtime.persistence.postgres.runtime_session import (
    PostgresRuntimeSession,
    PostgresRuntimeSessionFactory,
)
from afritech.novaride_runtime.services import (
    NovaRideRuntime,
    create_runtime_with_dependencies,
)


T = TypeVar("T")


@dataclass(slots=True)
class PostgresOperationRuntime:
    """Runtime dependencies valid only for one open persistence session."""

    runtime: NovaRideRuntime
    session: PostgresRuntimeSession


class PostgresRuntimeBridge:
    """Create and execute one tenant-scoped PostgreSQL runtime operation."""

    def __init__(
        self,
        session_factory: PostgresRuntimeSessionFactory,
    ) -> None:
        self.session_factory = session_factory

    def build_runtime(
        self,
        session: PostgresRuntimeSession,
    ) -> NovaRideRuntime:
        """Build runtime dependencies from an already-open session."""

        events = PostgresEventFabric(
            repositories=session.repositories,
            support=session.support,
        )

        return create_runtime_with_dependencies(
            session.repositories,
            events=events,
        )

    def execute(
        self,
        *,
        tenant_id: str,
        operation: Callable[[NovaRideRuntime], T],
    ) -> T:
        """Execute one runtime operation in one PostgreSQL transaction."""

        with self.session_factory.session(
            tenant_id=tenant_id,
        ) as session:
            runtime = self.build_runtime(
                session
            )

            return operation(
                runtime
            )


__all__ = [
    "PostgresOperationRuntime",
    "PostgresRuntimeBridge",
]
