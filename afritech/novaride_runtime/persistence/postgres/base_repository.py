"""Synchronous PostgreSQL repository foundation for NovaRide aggregates.

NovaRide's canonical domain services currently use synchronous repository
contracts. This module deliberately preserves that contract.

Domain-specific repositories provide two mappings:

* ``to_record`` converts an aggregate into columns matching its migration table.
* ``from_record`` reconstructs the aggregate from a PostgreSQL row.

The base repository owns only safe SQL construction and the common
``save/get/list`` lifecycle. It does not invent a second persistence schema,
does not fake PostgreSQL, and does not convert the runtime to async.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Any, Callable, Generic, Mapping, Protocol, Sequence, TypeVar

T = TypeVar("T")


class PostgresStrictCreateOutcome(str, Enum):
    """Explicit outcome of one strict PostgreSQL create attempt."""

    CREATED = "CREATED"
    UNCHANGED = "UNCHANGED"


@dataclass(frozen=True, slots=True)
class PostgresStrictCreateResult(Generic[T]):
    """Aggregate plus the persistence outcome of strict creation."""

    aggregate: T
    outcome: PostgresStrictCreateOutcome


_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class PostgresCursor(Protocol):
    """Minimal synchronous cursor contract used by repository adapters."""

    def fetchone(self) -> Mapping[str, Any] | None: ...

    def fetchall(self) -> Sequence[Mapping[str, Any]]: ...


class SyncPostgresConnection(Protocol):
    """Minimal synchronous connection contract compatible with psycopg."""

    def execute(
        self,
        query: str,
        params: Sequence[Any] | None = None,
    ) -> PostgresCursor: ...


RecordEncoder = Callable[[T], Mapping[str, Any]]
RecordDecoder = Callable[[Mapping[str, Any]], T]


def validate_identifier(value: str, *, field: str) -> str:
    """Validate a SQL identifier before it is interpolated into a statement."""

    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"invalid_postgres_{field}:{value!r}")

    return value


def _row_to_mapping(cursor, row):
    """Normalize PostgreSQL rows into a mapping.

    Supports both mapping-style fake/test rows and positional psycopg rows.
    """
    if row is None:
        return None

    if isinstance(row, dict):
        return row

    try:
        return dict(row)
    except (TypeError, ValueError):
        pass

    description = getattr(cursor, "description", None)

    if not description:
        raise TypeError(
            "cannot map positional PostgreSQL row without cursor.description"
        )

    columns = []

    for item in description:
        name = getattr(item, "name", None)

        if name is None:
            name = item[0]

        columns.append(name)

    if len(columns) != len(row):
        raise ValueError(
            "cursor column count does not match PostgreSQL row width"
        )

    return dict(zip(columns, row))


@dataclass(slots=True)
class PostgresAggregateRepository(Generic[T]):
    """Common synchronous CRUD behavior for a NovaRide PostgreSQL table.

    The table and column names are configuration supplied by trusted source
    code and are validated before interpolation. Runtime values remain query
    parameters.

    ``to_record`` must return keys that correspond exactly to columns in the
    target migration table. ``from_record`` owns domain reconstruction.
    """

    connection: SyncPostgresConnection
    table: str
    id_column: str
    to_record: RecordEncoder[T]
    from_record: RecordDecoder[T]
    tenant_column: str | None = "tenant_id"

    def __post_init__(self) -> None:
        self.table = validate_identifier(self.table, field="table")
        self.id_column = validate_identifier(self.id_column, field="id_column")

        if self.tenant_column is not None:
            self.tenant_column = validate_identifier(
                self.tenant_column,
                field="tenant_column",
            )

    def save(self, aggregate: T) -> T:
        """Insert or update an aggregate using its primary identifier."""

        record = dict(self.to_record(aggregate))

        if not record:
            raise ValueError("postgres_record_empty")

        if self.id_column not in record:
            raise ValueError(
                f"postgres_record_missing_id_column:{self.id_column}"
            )

        self._validate_record_columns(record)

        columns = tuple(record)
        values = tuple(record[column] for column in columns)

        column_sql = ", ".join(columns)
        placeholder_sql = ", ".join(["%s"] * len(columns))

        update_columns = tuple(
            column
            for column in columns
            if column != self.id_column
        )

        if update_columns:
            update_sql = ", ".join(
                f"{column} = EXCLUDED.{column}"
                for column in update_columns
            )
            conflict_sql = (
                f"ON CONFLICT ({self.id_column}) DO UPDATE SET {update_sql}"
            )
        else:
            conflict_sql = (
                f"ON CONFLICT ({self.id_column}) DO NOTHING"
            )

        query = (
            f"INSERT INTO {self.table} ({column_sql}) "
            f"VALUES ({placeholder_sql}) "
            f"{conflict_sql}"
        )

        self.connection.execute(query, values)
        return aggregate
    def create_strict(self, aggregate: T) -> T:
        """Create an aggregate without overwriting an existing identifier.

        An identical existing persistence record is an idempotent match.
        A conflicting record for the same primary identifier fails closed.

        This compatibility surface preserves the historical aggregate-only
        return contract. Call ``create_strict_with_outcome`` when the caller
        requires explicit CREATED versus UNCHANGED persistence evidence.
        """

        return self.create_strict_with_outcome(aggregate).aggregate

    def create_strict_with_outcome(
        self,
        aggregate: T,
    ) -> PostgresStrictCreateResult[T]:
        """Strictly create and report whether persistence changed."""

        record = dict(self.to_record(aggregate))

        if not record:
            raise ValueError("postgres_record_empty")

        if self.id_column not in record:
            raise ValueError(
                f"postgres_record_missing_id_column:{self.id_column}"
            )

        self._validate_record_columns(record)

        columns = tuple(record)
        values = tuple(record[column] for column in columns)

        column_sql = ", ".join(columns)
        placeholder_sql = ", ".join(["%s"] * len(columns))

        query = (
            f"INSERT INTO {self.table} ({column_sql}) "
            f"VALUES ({placeholder_sql}) "
            f"ON CONFLICT ({self.id_column}) DO NOTHING "
            f"RETURNING *"
        )

        cursor = self.connection.execute(query, values)
        row = cursor.fetchone()

        if row is not None:
            persisted = self.from_record(
                _row_to_mapping(cursor, row)
            )
            outcome = PostgresStrictCreateOutcome.CREATED
        else:
            aggregate_id = str(record[self.id_column])
            persisted = self.get(aggregate_id)

            if persisted is None:
                raise RuntimeError(
                    "postgres_strict_create_conflict_record_missing"
                )

            outcome = PostgresStrictCreateOutcome.UNCHANGED

        # Strict-create equivalence is evaluated after canonical
        # persistence reconstruction. Transport adapters used by
        # ``to_record`` (for example psycopg Jsonb wrappers) are
        # execution details and must not participate in aggregate
        # identity/equivalence.
        #
        # Genuine persistence differences remain fail-closed because
        # ``from_record`` reconstructs the authoritative aggregate and
        # aggregate equality must still match the requested value.
        if persisted != aggregate:
            raise ValueError(
                "postgres_strict_create_conflict"
            )

        return PostgresStrictCreateResult(
            aggregate=persisted,
            outcome=outcome,
        )


    def get(self, aggregate_id: str) -> T | None:
        """Return an aggregate by primary identifier."""

        query = (
            f"SELECT * FROM {self.table} "
            f"WHERE {self.id_column} = %s"
        )

        cursor = self.connection.execute(
            query,
            (aggregate_id,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return self.from_record(_row_to_mapping(cursor, row))

    def list(self, *, tenant_id: str | None = None) -> list[T]:
        """List aggregates, optionally scoped to a tenant."""

        if tenant_id is not None:
            if self.tenant_column is None:
                raise ValueError(
                    "postgres_repository_tenant_filter_unsupported"
                )

            query = (
                f"SELECT * FROM {self.table} "
                f"WHERE {self.tenant_column} = %s "
                f"ORDER BY {self.id_column}"
            )
            params: tuple[Any, ...] = (tenant_id,)
        else:
            query = (
                f"SELECT * FROM {self.table} "
                f"ORDER BY {self.id_column}"
            )
            params = ()

        cursor = self.connection.execute(query, params)

        return [
            self.from_record(_row_to_mapping(cursor, row))
            for row in cursor.fetchall()
        ]

    def _validate_record_columns(
        self,
        record: Mapping[str, Any],
    ) -> None:
        for column in record:
            validate_identifier(
                column,
                field="record_column",
            )


__all__ = [
    "PostgresAggregateRepository",
    "PostgresCursor",
    "PostgresStrictCreateOutcome",
    "PostgresStrictCreateResult",
    "RecordDecoder",
    "RecordEncoder",
    "SyncPostgresConnection",
    "validate_identifier",
]
