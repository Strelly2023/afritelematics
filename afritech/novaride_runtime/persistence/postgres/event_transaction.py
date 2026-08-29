"""Atomic PostgreSQL event + outbox persistence boundary."""

from __future__ import annotations

from afritech.novaride_runtime.persistence.postgres.event_outbox_repository import (
    PostgresEventOutboxRepository,
)
from afritech.novaride_runtime.persistence.postgres.event_repository import (
    PostgresEventRepository,
)
from afritech.novaride_runtime.persistence.postgres.unit_of_work import (
    PostgresUnitOfWork,
)


class PostgresEventTransaction:
    """Persist an event and its publication intent atomically."""

    def __init__(
        self,
        unit_of_work: PostgresUnitOfWork,
    ) -> None:
        self.unit_of_work = unit_of_work

    def append(
        self,
        event,
    ):
        """Append event + outbox row using one transaction.

        The UnitOfWork owns commit and rollback. Both repositories receive
        the same connection, preventing event/outbox split-brain commits.
        """

        with self.unit_of_work as uow:
            uow.set_tenant_context(
                event.tenant_id
            )

            connection = (
                uow.require_connection()
            )

            events = PostgresEventRepository(
                connection
            )

            outbox = (
                PostgresEventOutboxRepository(
                    connection
                )
            )

            events.append(event)
            outbox.append(event)

        return event


__all__ = [
    "PostgresEventTransaction",
]
