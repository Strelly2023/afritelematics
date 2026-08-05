"""SQLite persistence, migrations, optimistic concurrency, and outbox."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import sqlite3
from typing import Any, Callable, Generic, Mapping, TypeVar

from . import domain
from .codec import decode_aggregate, decode_event, encode_aggregate, encode_event
from .domain import DomainEvent, Entity, Identifier, LifecycleAggregate
from .persistence import (
    AggregateAlreadyExistsError,
    AggregateNotFoundError,
    AggregateQuery,
    DuplicateBusinessKeyError,
    MigrationError,
    OptimisticConcurrencyError,
    OutboxError,
    RepositoryError,
    SerializationError,
    TenantScopeError,
)


T = TypeVar("T", bound=Entity | LifecycleAggregate)
Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Migration:
    migration_id: str
    statements: tuple[str, ...]


MIGRATIONS = (
    Migration(
        "0001_novalogistics_aggregate_outbox",
        (
            """CREATE TABLE IF NOT EXISTS novalogistics_aggregates (
                tenant_id TEXT NOT NULL,
                aggregate_type TEXT NOT NULL,
                aggregate_id TEXT NOT NULL,
                aggregate_version INTEGER NOT NULL CHECK (aggregate_version >= 0),
                lifecycle_status TEXT,
                business_key TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                archived_at TEXT,
                PRIMARY KEY (tenant_id, aggregate_type, aggregate_id),
                UNIQUE (tenant_id, aggregate_type, business_key)
            )""",
            """CREATE TABLE IF NOT EXISTS novalogistics_outbox (
                event_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                aggregate_type TEXT NOT NULL,
                aggregate_id TEXT NOT NULL,
                aggregate_version INTEGER NOT NULL CHECK (aggregate_version >= 0),
                event_order INTEGER NOT NULL CHECK (event_order >= 1),
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                correlation_id TEXT,
                request_id TEXT,
                published_at TEXT,
                delivery_attempts INTEGER NOT NULL DEFAULT 0 CHECK (delivery_attempts >= 0),
                last_error TEXT,
                UNIQUE (tenant_id, aggregate_type, aggregate_id, aggregate_version, event_order),
                FOREIGN KEY (tenant_id, aggregate_type, aggregate_id)
                    REFERENCES novalogistics_aggregates(tenant_id, aggregate_type, aggregate_id)
                    ON DELETE CASCADE
            )""",
            "CREATE INDEX IF NOT EXISTS idx_nl_aggregate_tenant_type_status ON novalogistics_aggregates(tenant_id, aggregate_type, lifecycle_status, updated_at, aggregate_id)",
            "CREATE INDEX IF NOT EXISTS idx_nl_aggregate_tenant_business ON novalogistics_aggregates(tenant_id, aggregate_type, business_key)",
            "CREATE INDEX IF NOT EXISTS idx_nl_outbox_pending ON novalogistics_outbox(tenant_id, published_at, occurred_at, aggregate_version, event_order, event_id)",
        ),
    ),
)


class MigrationRunner:
    def __init__(self, connection: sqlite3.Connection, migrations: tuple[Migration, ...] = MIGRATIONS, *, clock: Clock = utc_now) -> None:
        self.connection = connection
        self.migrations = migrations
        self.clock = clock

    def migrate(self) -> tuple[str, ...]:
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS novalogistics_schema_migrations (migration_id TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        applied: list[str] = []
        try:
            known = {row[0] for row in self.connection.execute("SELECT migration_id FROM novalogistics_schema_migrations")}
            for migration in sorted(self.migrations, key=lambda item: item.migration_id):
                if migration.migration_id in known:
                    continue
                self.connection.execute("BEGIN IMMEDIATE")
                try:
                    for statement in migration.statements:
                        self.connection.execute(statement)
                    self.connection.execute(
                        "INSERT INTO novalogistics_schema_migrations(migration_id, applied_at) VALUES (?, ?)",
                        (migration.migration_id, self.clock().astimezone(timezone.utc).isoformat()),
                    )
                    self.connection.commit()
                    applied.append(migration.migration_id)
                except Exception:
                    self.connection.rollback()
                    raise
        except Exception as exc:
            raise MigrationError("NovaLogistics migration failed") from exc
        return tuple(applied)

    def applied(self) -> tuple[str, ...]:
        return tuple(row[0] for row in self.connection.execute(
            "SELECT migration_id FROM novalogistics_schema_migrations ORDER BY migration_id"
        ))


def connect(path: str = ":memory:") -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=30, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    MigrationRunner(connection).migrate()
    return connection


@dataclass(frozen=True)
class OutboxRecord:
    event_id: str
    tenant_id: Identifier
    aggregate_type: str
    aggregate_id: Identifier
    aggregate_version: int
    event_order: int
    event: DomainEvent
    metadata: Mapping[str, Any]
    correlation_id: str | None
    request_id: str | None
    published_at: datetime | None
    delivery_attempts: int
    last_error: str | None


class SQLiteOutbox:
    def __init__(self, connection: sqlite3.Connection, *, clock: Clock = utc_now) -> None:
        self.connection = connection
        self.clock = clock

    def pending(self, tenant_id: Identifier, *, limit: int = 100) -> tuple[OutboxRecord, ...]:
        if not 1 <= limit <= 500:
            raise OutboxError("outbox limit must be between 1 and 500")
        rows = self.connection.execute(
            """SELECT * FROM novalogistics_outbox
               WHERE tenant_id = ? AND published_at IS NULL
               ORDER BY occurred_at, aggregate_version, event_order, event_id LIMIT ?""",
            (str(tenant_id), limit),
        ).fetchall()
        return tuple(self._row(row) for row in rows)

    def mark_published(self, tenant_id: Identifier, event_id: str, *, at: datetime | None = None) -> None:
        timestamp = (at or self.clock()).astimezone(timezone.utc).isoformat()
        cursor = self.connection.execute(
            """UPDATE novalogistics_outbox
               SET published_at = COALESCE(published_at, ?)
               WHERE tenant_id = ? AND event_id = ?""",
            (timestamp, str(tenant_id), event_id),
        )
        if cursor.rowcount == 0:
            raise AggregateNotFoundError("outbox event not found")

    def mark_failed(self, tenant_id: Identifier, event_id: str, error: str) -> None:
        cursor = self.connection.execute(
            """UPDATE novalogistics_outbox SET delivery_attempts = delivery_attempts + 1,
               last_error = ? WHERE tenant_id = ? AND event_id = ?""",
            (error[:1000], str(tenant_id), event_id),
        )
        if cursor.rowcount == 0:
            raise AggregateNotFoundError("outbox event not found")

    @staticmethod
    def _row(row: sqlite3.Row) -> OutboxRecord:
        return OutboxRecord(
            event_id=row["event_id"], tenant_id=Identifier(row["tenant_id"]),
            aggregate_type=row["aggregate_type"], aggregate_id=Identifier(row["aggregate_id"]),
            aggregate_version=row["aggregate_version"], event_order=row["event_order"],
            event=decode_event(row["payload_json"]), metadata=json.loads(row["metadata_json"]),
            correlation_id=row["correlation_id"], request_id=row["request_id"],
            published_at=datetime.fromisoformat(row["published_at"]) if row["published_at"] else None,
            delivery_attempts=row["delivery_attempts"], last_error=row["last_error"],
        )


class SQLiteAggregateRepository(Generic[T]):
    def __init__(self, connection: sqlite3.Connection, aggregate_type: type[T], *, clock: Clock = utc_now) -> None:
        self.connection = connection
        self.aggregate_type = aggregate_type
        self.clock = clock

    @property
    def type_name(self) -> str:
        return self.aggregate_type.__name__

    def add(
        self,
        aggregate: T,
        *,
        business_key: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        correlation_id: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self._assert_type(aggregate)
        payload = encode_aggregate(aggregate)
        metadata_json = self._metadata(metadata)
        now = self.clock().astimezone(timezone.utc).isoformat()
        version = getattr(aggregate, "version", 0)
        status = getattr(getattr(aggregate, "status", None), "value", None)
        try:
            self.connection.execute("BEGIN IMMEDIATE")
            self.connection.execute(
                """INSERT INTO novalogistics_aggregates
                   (tenant_id, aggregate_type, aggregate_id, aggregate_version, lifecycle_status,
                    business_key, payload_json, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (str(aggregate.tenant_id), self.type_name, str(aggregate.id), version, status,
                 business_key.strip() if business_key else None, payload, now, now),
            )
            self._insert_events(aggregate, metadata_json, correlation_id, request_id)
            self.connection.commit()
        except sqlite3.IntegrityError as exc:
            self.connection.rollback()
            if business_key and "business_key" in str(exc):
                raise DuplicateBusinessKeyError(business_key) from exc
            raise AggregateAlreadyExistsError(str(aggregate.id)) from exc
        except Exception as exc:
            self.connection.rollback()
            if isinstance(exc, RepositoryError):
                raise
            raise RepositoryError("aggregate insert failed") from exc

    def get(self, tenant_id: Identifier, aggregate_id: Identifier) -> T:
        row = self.connection.execute(
            "SELECT payload_json FROM novalogistics_aggregates WHERE tenant_id=? AND aggregate_type=? AND aggregate_id=? AND archived_at IS NULL",
            (str(tenant_id), self.type_name, str(aggregate_id)),
        ).fetchone()
        if row is None:
            raise AggregateNotFoundError(str(aggregate_id))
        value = decode_aggregate(row["payload_json"])
        self._assert_type(value)
        return value

    def exists(self, tenant_id: Identifier, aggregate_id: Identifier) -> bool:
        return self.connection.execute(
            "SELECT 1 FROM novalogistics_aggregates WHERE tenant_id=? AND aggregate_type=? AND aggregate_id=? AND archived_at IS NULL",
            (str(tenant_id), self.type_name, str(aggregate_id)),
        ).fetchone() is not None

    def list(self, tenant_id: Identifier, query: AggregateQuery = AggregateQuery()) -> tuple[T, ...]:
        where, params = self._where(tenant_id, query)
        direction = "DESC" if query.descending else "ASC"
        rows = self.connection.execute(
            f"SELECT payload_json FROM novalogistics_aggregates WHERE {where} ORDER BY updated_at {direction}, aggregate_id {direction} LIMIT ? OFFSET ?",
            (*params, query.page.limit, query.page.offset),
        ).fetchall()
        values = tuple(decode_aggregate(row["payload_json"]) for row in rows)
        for value in values:
            self._assert_type(value)
        return values  # type: ignore[return-value]

    def count(self, tenant_id: Identifier, query: AggregateQuery = AggregateQuery()) -> int:
        where, params = self._where(tenant_id, query)
        return int(self.connection.execute(
            f"SELECT COUNT(*) FROM novalogistics_aggregates WHERE {where}", params
        ).fetchone()[0])

    def find_by_business_key(self, tenant_id: Identifier, business_key: str) -> T:
        query = AggregateQuery(business_key=business_key)
        values = self.list(tenant_id, query)
        if not values:
            raise AggregateNotFoundError(business_key)
        return values[0]

    def save(
        self,
        aggregate: T,
        *,
        expected_version: int,
        metadata: Mapping[str, Any] | None = None,
        correlation_id: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self._assert_type(aggregate)
        if not isinstance(aggregate, LifecycleAggregate):
            raise OptimisticConcurrencyError("reference records are immutable")
        if aggregate.version <= expected_version:
            raise OptimisticConcurrencyError("aggregate version must advance")
        payload = encode_aggregate(aggregate)
        metadata_json = self._metadata(metadata)
        now = self.clock().astimezone(timezone.utc).isoformat()
        try:
            self.connection.execute("BEGIN IMMEDIATE")
            cursor = self.connection.execute(
                """UPDATE novalogistics_aggregates
                   SET aggregate_version=?, lifecycle_status=?, payload_json=?, updated_at=?
                   WHERE tenant_id=? AND aggregate_type=? AND aggregate_id=?
                     AND aggregate_version=? AND archived_at IS NULL""",
                (aggregate.version, aggregate.status.value, payload, now, str(aggregate.tenant_id),
                 self.type_name, str(aggregate.id), expected_version),
            )
            if cursor.rowcount != 1:
                self._raise_write_conflict(aggregate)
            self._insert_events(aggregate, metadata_json, correlation_id, request_id, after_version=expected_version)
            self.connection.commit()
        except Exception as exc:
            self.connection.rollback()
            if isinstance(exc, RepositoryError):
                raise
            raise RepositoryError("aggregate save failed") from exc

    def archive(self, tenant_id: Identifier, aggregate_id: Identifier) -> None:
        now = self.clock().astimezone(timezone.utc).isoformat()
        cursor = self.connection.execute(
            "UPDATE novalogistics_aggregates SET archived_at=?, updated_at=? WHERE tenant_id=? AND aggregate_type=? AND aggregate_id=? AND archived_at IS NULL",
            (now, now, str(tenant_id), self.type_name, str(aggregate_id)),
        )
        if cursor.rowcount == 0:
            raise AggregateNotFoundError(str(aggregate_id))

    def _where(self, tenant_id: Identifier, query: AggregateQuery) -> tuple[str, tuple[Any, ...]]:
        clauses = ["tenant_id=?", "aggregate_type=?", "archived_at IS NULL"]
        params: list[Any] = [str(tenant_id), self.type_name]
        for column, value in (("lifecycle_status", query.status), ("business_key", query.business_key)):
            if value is not None:
                clauses.append(f"{column}=?")
                params.append(value)
        for operator, value in ((">=", query.updated_from), ("<=", query.updated_to)):
            if value is not None:
                if value.tzinfo is None:
                    raise RepositoryError("query timestamps must be timezone-aware")
                clauses.append(f"updated_at {operator} ?")
                params.append(value.astimezone(timezone.utc).isoformat())
        return " AND ".join(clauses), tuple(params)

    def _insert_events(self, aggregate: T, metadata_json: str, correlation_id: str | None, request_id: str | None, *, after_version: int = -1) -> None:
        if not isinstance(aggregate, LifecycleAggregate):
            return
        first_version = aggregate.version - len(aggregate.events) + 1
        for order, event in enumerate(aggregate.events, start=1):
            event_version = first_version + order - 1
            if event_version <= after_version:
                continue
            payload = encode_event(event)
            identity = "|".join((str(event.tenant_id), self.type_name, str(event.aggregate_id), str(event_version), str(order), payload))
            event_id = sha256(identity.encode("utf-8")).hexdigest()
            values = (
                event_id, str(event.tenant_id), self.type_name, str(event.aggregate_id), event_version,
                order, event.event_type, payload, metadata_json, event.occurred_at.isoformat(),
                correlation_id, request_id,
            )
            try:
                self.connection.execute(
                    """INSERT INTO novalogistics_outbox
                   (event_id, tenant_id, aggregate_type, aggregate_id, aggregate_version, event_order,
                    event_type, payload_json, metadata_json, occurred_at, correlation_id, request_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    values,
                )
            except sqlite3.IntegrityError as exc:
                existing = self.connection.execute(
                    """SELECT tenant_id, aggregate_type, aggregate_id, aggregate_version, event_order,
                              event_type, payload_json, metadata_json, occurred_at, correlation_id, request_id
                       FROM novalogistics_outbox WHERE event_id=?""",
                    (event_id,),
                ).fetchone()
                if existing is None or tuple(existing) != values[1:]:
                    raise OutboxError("outbox event identity conflict") from exc

    def _raise_write_conflict(self, aggregate: LifecycleAggregate) -> None:
        row = self.connection.execute(
            "SELECT tenant_id, aggregate_version FROM novalogistics_aggregates WHERE aggregate_type=? AND aggregate_id=?",
            (self.type_name, str(aggregate.id)),
        ).fetchone()
        if row is None:
            raise AggregateNotFoundError(str(aggregate.id))
        if row["tenant_id"] != str(aggregate.tenant_id):
            raise TenantScopeError(str(aggregate.id))
        raise OptimisticConcurrencyError(
            f"stale aggregate version: persisted={row['aggregate_version']} requested={aggregate.version}"
        )

    def _assert_type(self, aggregate: Entity | LifecycleAggregate) -> None:
        if not isinstance(aggregate, self.aggregate_type):
            raise RepositoryError(f"expected {self.type_name}")

    @staticmethod
    def _metadata(metadata: Mapping[str, Any] | None) -> str:
        try:
            return json.dumps(dict(metadata or {}), sort_keys=True, separators=(",", ":"))
        except (TypeError, ValueError) as exc:
            raise SerializationError("event metadata is not JSON serializable") from exc


def _repository_type(name: str, aggregate_type: type[T]) -> type[SQLiteAggregateRepository[T]]:
    class ConcreteRepository(SQLiteAggregateRepository[T]):
        def __init__(self, connection: sqlite3.Connection, *, clock: Clock = utc_now) -> None:
            super().__init__(connection, aggregate_type, clock=clock)
    ConcreteRepository.__name__ = name
    ConcreteRepository.__qualname__ = name
    return ConcreteRepository


_PERSISTED_TYPES = (
    "Customer Supplier Carrier Driver Vehicle Trailer Warehouse Dock Zone BinLocation Item SKU "
    "HandlingUnit Package Pallet Shipment ShipmentLeg Stop Load Consignment Delivery Route Order "
    "PurchaseOrder SalesOrder Quote Rate ServiceLevel TrackingEvent ProofOfDelivery Incident Claim"
).split()

for _name in _PERSISTED_TYPES:
    globals()[f"SQLite{_name}Repository"] = _repository_type(
        f"SQLite{_name}Repository", getattr(domain, _name)
    )


__all__ = [
    "Migration", "MigrationRunner", "MIGRATIONS", "connect", "OutboxRecord", "SQLiteOutbox",
    "SQLiteAggregateRepository", *[f"SQLite{name}Repository" for name in _PERSISTED_TYPES],
]
