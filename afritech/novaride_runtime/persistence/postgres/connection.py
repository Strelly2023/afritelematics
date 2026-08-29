"""NovaRide synchronous PostgreSQL connection foundation.

This module provides the connection lifecycle required by the synchronous
NovaRide PostgreSQL runtime repositories.

It deliberately does not activate PostgreSQL runtime composition. Repository
composition and production adapter selection remain separate NR-003 gates.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol


class PostgresConnectionProtocol(Protocol):
    def execute(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
    ) -> Any:
        ...

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...

    def close(self) -> None:
        ...


ConnectionFactory = Callable[
    [str],
    PostgresConnectionProtocol,
]


@dataclass(frozen=True, slots=True)
class PostgresConnectionConfig:
    dsn: str
    application_name: str = "novaride-runtime"


class PostgresConnectionFactory:
    """Create synchronous PostgreSQL connections.

    psycopg is imported lazily so unit tests and memory-only development
    workflows do not require a live PostgreSQL installation or connection.
    """

    def __init__(
        self,
        connector: ConnectionFactory | None = None,
    ) -> None:
        self._connector = connector

    def connect(
        self,
        config: PostgresConnectionConfig,
    ) -> PostgresConnectionProtocol:
        if not config.dsn:
            raise RuntimeError(
                "postgres_dsn_required"
            )

        connector = self._connector

        if connector is None:
            try:
                import psycopg
            except ImportError as exc:
                raise RuntimeError(
                    "psycopg_required_for_postgresql_runtime"
                ) from exc

            def connector(
                dsn: str,
            ) -> PostgresConnectionProtocol:
                return psycopg.connect(
                    dsn,
                    application_name=(
                        config.application_name
                    ),
                )

        connection = connector(
            config.dsn
        )

        if connection is None:
            raise RuntimeError(
                "postgres_connection_factory_returned_none"
            )

        return connection


__all__ = [
    "ConnectionFactory",
    "PostgresConnectionConfig",
    "PostgresConnectionFactory",
    "PostgresConnectionProtocol",
]
