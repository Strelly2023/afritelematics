"""Transaction-scoped PostgreSQL persistence session for NovaRide.

This module bridges the long-lived NovaRide runtime configuration boundary
to short-lived PostgreSQL transaction scopes.

A session:

* owns one PostgresUnitOfWork;
* opens one PostgreSQL connection/transaction;
* applies tenant context transaction-locally;
* constructs the certified RuntimeRepositories bundle on that connection;
* exposes PostgreSQL support repositories for the same connection;
* exposes the atomic Event/Outbox transaction boundary;
* commits on successful context-manager exit;
* rolls back on failed context-manager exit;
* always closes the UnitOfWork.

This module deliberately does not:

* activate PostgreSQL in create_runtime();
* modify settings-driven adapter selection;
* create a global PostgreSQL connection;
* create a global tenant context;
* keep a UnitOfWork for runtime lifetime;
* activate Kafka, Redis, or production infrastructure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .connection import (
    PostgresConnectionFactory,
)
from .event_transaction import (
    PostgresEventTransaction,
)
from .runtime_repositories import (
    PostgresRuntimeRepositoryBundle,
    create_postgres_runtime_repository_bundle,
)
from .unit_of_work import (
    PostgresUnitOfWork,
    PostgresUnitOfWorkConfig,
)


@dataclass(frozen=True, slots=True)
class PostgresRuntimeSessionConfig:
    """Configuration for transaction-scoped runtime persistence."""

    dsn: str
    schema: str = "public"
    rls_required: bool = True
    application_name: str = "novaride-runtime"

    def __post_init__(self) -> None:
        if not self.dsn or not self.dsn.strip():
            raise ValueError("postgres_dsn_required")

    def unit_of_work_config(self) -> PostgresUnitOfWorkConfig:
        return PostgresUnitOfWorkConfig(
            dsn=self.dsn,
            schema=self.schema,
            rls_required=self.rls_required,
            application_name=self.application_name,
        )


class PostgresRuntimeSession:
    """One tenant-scoped PostgreSQL transaction for NovaRide runtime work."""

    def __init__(
        self,
        config: PostgresRuntimeSessionConfig,
        *,
        tenant_id: str,
        connection_factory: PostgresConnectionFactory | None = None,
    ) -> None:
        if not tenant_id or not tenant_id.strip():
            raise ValueError("tenant_id_required")

        self.config = config
        self.tenant_id = tenant_id
        self.connection_factory = connection_factory

        self._unit_of_work: PostgresUnitOfWork | None = None
        self._bundle: PostgresRuntimeRepositoryBundle | None = None
        self._event_transaction: PostgresEventTransaction | None = None

    @property
    def unit_of_work(self) -> PostgresUnitOfWork:
        if self._unit_of_work is None:
            raise RuntimeError("postgres_runtime_session_not_open")
        return self._unit_of_work

    @property
    def bundle(self) -> PostgresRuntimeRepositoryBundle:
        if self._bundle is None:
            raise RuntimeError("postgres_runtime_session_not_open")
        return self._bundle

    @property
    def repositories(self) -> Any:
        return self.bundle.repositories

    @property
    def support(self) -> Any:
        return self.bundle.support

    @property
    def event_transaction(self) -> PostgresEventTransaction:
        if self._event_transaction is None:
            raise RuntimeError("postgres_runtime_session_not_open")
        return self._event_transaction

    def open(self) -> "PostgresRuntimeSession":
        if self._unit_of_work is not None:
            raise RuntimeError("postgres_runtime_session_already_open")

        uow = PostgresUnitOfWork(
            self.config.unit_of_work_config(),
            connection_factory=self.connection_factory,
        )

        try:
            uow.connect()
            uow.set_tenant_context(self.tenant_id)

            connection = uow.require_connection()

            bundle = create_postgres_runtime_repository_bundle(
                connection
            )

            event_transaction = PostgresEventTransaction(
                uow
            )

        except BaseException:
            try:
                uow.rollback()
            except BaseException:
                pass

            try:
                uow.close()
            except BaseException:
                pass

            raise

        self._unit_of_work = uow
        self._bundle = bundle
        self._event_transaction = event_transaction

        return self

    def commit(self) -> None:
        self.unit_of_work.commit()

    def rollback(self) -> None:
        self.unit_of_work.rollback()

    def close(self) -> None:
        uow = self._unit_of_work

        self._event_transaction = None
        self._bundle = None
        self._unit_of_work = None

        if uow is not None:
            uow.close()

    def __enter__(self) -> "PostgresRuntimeSession":
        return self.open()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: Any,
    ) -> bool:
        try:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        finally:
            self.close()

        return False


class PostgresRuntimeSessionFactory:
    """Long-lived factory that creates short-lived PostgreSQL sessions."""

    def __init__(
        self,
        config: PostgresRuntimeSessionConfig,
        *,
        connection_factory: PostgresConnectionFactory | None = None,
    ) -> None:
        self.config = config
        self.connection_factory = connection_factory

    def session(
        self,
        *,
        tenant_id: str,
    ) -> PostgresRuntimeSession:
        return PostgresRuntimeSession(
            self.config,
            tenant_id=tenant_id,
            connection_factory=self.connection_factory,
        )


__all__ = [
    "PostgresRuntimeSession",
    "PostgresRuntimeSessionConfig",
    "PostgresRuntimeSessionFactory",
]
