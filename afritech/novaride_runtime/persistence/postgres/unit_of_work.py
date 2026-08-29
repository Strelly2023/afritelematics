"""PostgreSQL unit-of-work for the NovaRide synchronous runtime.

The unit of work owns one PostgreSQL connection and one transaction boundary.

Tenant-scoped operations set ``app.tenant_id`` using PostgreSQL ``set_config``
with transaction-local scope so canonical NovaRide RLS policies can enforce
tenant isolation.

This module does not select PostgreSQL for production. Runtime composition and
settings-driven activation are handled in later NR-003 sections.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import TracebackType
from afritech.novaride_runtime.persistence.postgres.base_repository import (
    validate_identifier,
)
from afritech.novaride_runtime.persistence.postgres.connection import (
    PostgresConnectionConfig,
    PostgresConnectionFactory,
    PostgresConnectionProtocol,
)


@dataclass(frozen=True, slots=True)
class PostgresUnitOfWorkConfig:
    dsn: str
    schema: str = "public"
    rls_required: bool = True
    application_name: str = "novaride-runtime"


class PostgresUnitOfWork:
    def __init__(
        self,
        config: PostgresUnitOfWorkConfig,
        *,
        connection_factory: (
            PostgresConnectionFactory | None
        ) = None,
    ) -> None:
        self.config = config
        self.connection_factory = (
            connection_factory
            or PostgresConnectionFactory()
        )
        self.connection: (
            PostgresConnectionProtocol | None
        ) = None
        self._tenant_id: str | None = None

    def require_configured(self) -> None:
        if not self.config.dsn:
            raise RuntimeError(
                "postgres_dsn_required"
            )

        validate_identifier(
            self.config.schema,
            field="schema",
        )

    def connect(
        self,
    ) -> PostgresConnectionProtocol:
        self.require_configured()

        if self.connection is not None:
            return self.connection

        self.connection = (
            self.connection_factory.connect(
                PostgresConnectionConfig(
                    dsn=self.config.dsn,
                    application_name=(
                        self.config.application_name
                    ),
                )
            )
        )

        try:
            self.activate_transaction_configuration()
        except BaseException:
            try:
                self.connection.rollback()
            finally:
                self.close()
            raise

        return self.connection

    def activate_transaction_configuration(
        self,
    ) -> None:
        connection = self.require_connection()

        schema = validate_identifier(
            self.config.schema,
            field="schema",
        )

        connection.execute(
            "SELECT set_config("
            "'search_path', %s, true"
            ")",
            (
                f'"{schema}"',
            ),
        )

        if self.config.rls_required:
            connection.execute(
                "SELECT set_config("
                "'row_security', %s, true"
                ")",
                (
                    "on",
                ),
            )

    def require_connection(
        self,
    ) -> PostgresConnectionProtocol:
        if self.connection is None:
            raise RuntimeError(
                "postgres_connection_not_open"
            )

        return self.connection

    def set_tenant_context(
        self,
        tenant_id: str,
    ) -> None:
        if not tenant_id:
            raise RuntimeError(
                "tenant_id_required"
            )

        connection = self.require_connection()

        connection.execute(
            "SELECT set_config("
            "'app.tenant_id', %s, true"
            ")",
            (
                tenant_id,
            ),
        )

        self._tenant_id = tenant_id

    def clear_tenant_context(
        self,
    ) -> None:
        self._tenant_id = None

    @property
    def tenant_id(
        self,
    ) -> str | None:
        return self._tenant_id

    def commit(self) -> None:
        connection = self.require_connection()
        connection.commit()
        self.clear_tenant_context()

    def rollback(self) -> None:
        connection = self.require_connection()
        connection.rollback()
        self.clear_tenant_context()

    def close(self) -> None:
        if self.connection is None:
            return

        try:
            self.connection.close()
        finally:
            self.connection = None
            self.clear_tenant_context()

    def __enter__(
        self,
    ) -> "PostgresUnitOfWork":
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        try:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        finally:
            self.close()

        return False


__all__ = [
    "PostgresUnitOfWork",
    "PostgresUnitOfWorkConfig",
]
