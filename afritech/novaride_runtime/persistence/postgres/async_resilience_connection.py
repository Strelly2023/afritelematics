"""Async psycopg adapter for NovaRide resilience repositories.

The resilience repositories intentionally expose a small async connection
contract modelled around execute/fetchrow/fetch and use PostgreSQL-style
numbered placeholders ($1, $2, ...).

psycopg 3 provides the required asynchronous PostgreSQL authority, but its
native API uses cursor fetch methods and ``%s`` placeholders. This adapter
bridges those contracts without changing repository SQL or introducing a
second PostgreSQL driver.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Protocol, Sequence

from psycopg.rows import dict_row


_NUMBERED_PLACEHOLDER = re.compile(r"\$(\d+)")


class PsycopgAsyncCursor(Protocol):
    async def execute(
        self,
        query: str,
        params: Sequence[Any] | None = None,
    ) -> Any: ...

    async def fetchone(self) -> Any: ...

    async def fetchall(self) -> list[Any]: ...


class PsycopgAsyncConnectionProtocol(Protocol):
    def cursor(
        self,
        *,
        row_factory: Any | None = None,
    ) -> Any: ...


AsyncConnector = Callable[..., Any]


def _translate_query(
    query: str,
    args: tuple[Any, ...],
) -> tuple[str, tuple[Any, ...]]:
    """Translate numbered PostgreSQL placeholders into psycopg parameters.

    Repository SQL uses ``$1``/``$2`` style placeholders. psycopg expects
    ``%s`` placeholders with positional parameters. Translation preserves
    repeated and reordered numbered parameters.
    """

    matches = list(_NUMBERED_PLACEHOLDER.finditer(query))

    if not matches:
        if args:
            raise ValueError(
                "resilience_sql_arguments_without_placeholders"
            )
        return query, ()

    indexes = [int(match.group(1)) for match in matches]

    if any(index <= 0 for index in indexes):
        raise ValueError(
            "resilience_sql_placeholder_index_must_be_positive"
        )

    highest = max(indexes)

    if highest > len(args):
        raise ValueError(
            "resilience_sql_placeholder_argument_missing"
        )

    # Reject unused supplied arguments. Repository calls should describe
    # their complete parameter contract through numbered placeholders.
    used = set(indexes)
    expected = set(range(1, len(args) + 1))

    if used != expected:
        raise ValueError(
            "resilience_sql_placeholder_argument_mismatch"
        )

    translated = _NUMBERED_PLACEHOLDER.sub("%s", query)
    translated_args = tuple(args[index - 1] for index in indexes)

    return translated, translated_args


@dataclass(slots=True)
class PsycopgAsyncResilienceConnection:
    """Adapt an open psycopg async connection to the resilience contract."""

    connection: PsycopgAsyncConnectionProtocol

    async def execute(
        self,
        query: str,
        *args: Any,
    ) -> Any:
        translated_query, translated_args = _translate_query(
            query,
            args,
        )

        async with self.connection.cursor(
            row_factory=dict_row,
        ) as cursor:
            return await cursor.execute(
                translated_query,
                translated_args or None,
            )

    async def fetchrow(
        self,
        query: str,
        *args: Any,
    ) -> Any:
        translated_query, translated_args = _translate_query(
            query,
            args,
        )

        async with self.connection.cursor(
            row_factory=dict_row,
        ) as cursor:
            await cursor.execute(
                translated_query,
                translated_args or None,
            )
            return await cursor.fetchone()

    async def fetch(
        self,
        query: str,
        *args: Any,
    ) -> list[Any]:
        translated_query, translated_args = _translate_query(
            query,
            args,
        )

        async with self.connection.cursor(
            row_factory=dict_row,
        ) as cursor:
            await cursor.execute(
                translated_query,
                translated_args or None,
            )
            rows = await cursor.fetchall()

        return list(rows)


@dataclass(frozen=True, slots=True)
class PsycopgAsyncResilienceConnectionConfig:
    """Configuration for the async resilience PostgreSQL connection."""

    dsn: str
    application_name: str = "novaride-resilience-runtime"


class PsycopgAsyncResilienceConnectionFactory:
    """Create psycopg-backed resilience connection adapters.

    Connection creation remains explicit. Constructing this factory does not
    open PostgreSQL and therefore does not activate runtime composition.
    """

    def __init__(
        self,
        connector: AsyncConnector | None = None,
    ) -> None:
        self._connector = connector

    async def connect(
        self,
        config: PsycopgAsyncResilienceConnectionConfig,
    ) -> PsycopgAsyncResilienceConnection:
        if not config.dsn:
            raise RuntimeError("postgres_dsn_required")

        connector = self._connector

        if connector is None:
            import psycopg

            connector = psycopg.AsyncConnection.connect

        connection = await connector(
            config.dsn,
            application_name=config.application_name,
            row_factory=dict_row,
        )

        if connection is None:
            raise RuntimeError(
                "postgres_async_connection_factory_returned_none"
            )

        return PsycopgAsyncResilienceConnection(connection)


__all__ = [
    "PsycopgAsyncConnectionProtocol",
    "PsycopgAsyncResilienceConnection",
    "PsycopgAsyncResilienceConnectionConfig",
    "PsycopgAsyncResilienceConnectionFactory",
]
