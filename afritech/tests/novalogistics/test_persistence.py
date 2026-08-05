from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import sqlite3

import pytest

from afritech.novalogistics import (
    AggregateAlreadyExistsError,
    AggregateNotFoundError,
    AggregateQuery,
    Customer,
    Identifier,
    OptimisticConcurrencyError,
    Page,
    Quote,
    QuoteStatus,
    Shipment,
    ShipmentStatus,
    TenantScopeError,
)
from afritech.novalogistics.codec import decode_aggregate, encode_aggregate
from afritech.novalogistics.persistence import (
    DuplicateBusinessKeyError,
    MigrationError,
    RepositoryError,
    SerializationError,
    UnsupportedSchemaVersionError,
)
from afritech.novalogistics.sqlite import (
    MIGRATIONS,
    Migration,
    MigrationRunner,
    SQLiteCustomerRepository,
    SQLiteOutbox,
    SQLiteQuoteRepository,
    SQLiteShipmentRepository,
    connect,
)


NOW = datetime(2026, 8, 6, 1, 2, 3, tzinfo=timezone.utc)
TENANT_A = Identifier("tenant-a")
TENANT_B = Identifier("tenant-b")


@pytest.fixture
def connection():
    value = connect()
    yield value
    value.close()


def customer(identifier: str, tenant: Identifier = TENANT_A, name: str = "Acme") -> Customer:
    return Customer(Identifier(identifier), tenant, name)


def shipment(identifier: str = "shipment-1", tenant: Identifier = TENANT_A) -> Shipment:
    return Shipment(Identifier(identifier), tenant, ShipmentStatus.DRAFT)


def test_reference_repository_insert_retrieve_exists_and_missing(connection):
    repository = SQLiteCustomerRepository(connection, clock=lambda: NOW)
    value = customer("customer-1")
    repository.add(value, business_key="ACME-1")
    assert repository.get(TENANT_A, value.id) == value
    assert repository.exists(TENANT_A, value.id) is True
    with pytest.raises(AggregateNotFoundError):
        repository.get(TENANT_A, Identifier("missing"))


def test_duplicate_identifier_and_tenant_scoped_business_keys(connection):
    repository = SQLiteCustomerRepository(connection, clock=lambda: NOW)
    repository.add(customer("one"), business_key="key")
    with pytest.raises(AggregateAlreadyExistsError):
        repository.add(customer("one"))
    with pytest.raises(DuplicateBusinessKeyError):
        repository.add(customer("two"), business_key="key")
    repository.add(customer("one", TENANT_B), business_key="key")
    assert repository.count(TENANT_A) == 1
    assert repository.count(TENANT_B) == 1


def test_pagination_filter_sort_count_business_lookup_and_archive(connection):
    repository = SQLiteCustomerRepository(connection, clock=lambda: NOW)
    for identifier in ("c", "a", "b"):
        repository.add(customer(identifier), business_key=f"key-{identifier}")
    page = repository.list(TENANT_A, AggregateQuery(page=Page(limit=2, offset=1)))
    assert [str(item.id) for item in page] == ["b", "c"]
    assert repository.find_by_business_key(TENANT_A, "key-b").id == Identifier("b")
    repository.archive(TENANT_A, Identifier("b"))
    assert repository.count(TENANT_A) == 2


def test_tenant_reads_lists_and_counts_are_isolated(connection):
    repository = SQLiteCustomerRepository(connection, clock=lambda: NOW)
    repository.add(customer("shared", TENANT_A))
    repository.add(customer("shared", TENANT_B))
    assert repository.get(TENANT_A, Identifier("shared")).tenant_id == TENANT_A
    assert {value.tenant_id for value in repository.list(TENANT_B)} == {TENANT_B}
    assert repository.count(TENANT_A) == repository.count(TENANT_B) == 1


def test_lifecycle_save_enforces_expected_version_and_emits_outbox(connection):
    repository = SQLiteShipmentRepository(connection, clock=lambda: NOW)
    original = shipment()
    repository.add(original)
    booked = original.transition(ShipmentStatus.BOOKED, at=NOW)
    repository.save(booked, expected_version=0, metadata={"source": "test"}, correlation_id="corr", request_id="req")
    assert repository.get(TENANT_A, original.id) == booked
    event = SQLiteOutbox(connection).pending(TENANT_A)[0]
    assert event.aggregate_version == 1
    assert event.metadata == {"source": "test"}
    assert (event.correlation_id, event.request_id) == ("corr", "req")


def test_stale_write_fails_without_partial_state_or_outbox(connection):
    repository = SQLiteShipmentRepository(connection, clock=lambda: NOW)
    original = shipment()
    repository.add(original)
    first = original.transition(ShipmentStatus.BOOKED, at=NOW)
    repository.save(first, expected_version=0)
    stale = original.transition(ShipmentStatus.CANCELLED, at=NOW)
    with pytest.raises(OptimisticConcurrencyError):
        repository.save(stale, expected_version=0)
    assert repository.get(TENANT_A, original.id) == first
    assert len(SQLiteOutbox(connection).pending(TENANT_A)) == 1


def test_cross_tenant_update_fails_safely(connection):
    repository = SQLiteShipmentRepository(connection, clock=lambda: NOW)
    repository.add(shipment())
    impostor = shipment(tenant=TENANT_B).transition(ShipmentStatus.BOOKED, at=NOW)
    with pytest.raises(TenantScopeError):
        repository.save(impostor, expected_version=0)


def test_two_connection_writers_cannot_both_succeed(tmp_path):
    path = str(tmp_path / "concurrency.sqlite3")
    first_connection, second_connection = connect(path), connect(path)
    try:
        first = SQLiteShipmentRepository(first_connection, clock=lambda: NOW)
        second = SQLiteShipmentRepository(second_connection, clock=lambda: NOW)
        first.add(shipment())
        writer_one = first.get(TENANT_A, Identifier("shipment-1")).transition(ShipmentStatus.BOOKED, at=NOW)
        writer_two = second.get(TENANT_A, Identifier("shipment-1")).transition(ShipmentStatus.CANCELLED, at=NOW)
        first.save(writer_one, expected_version=0)
        with pytest.raises(OptimisticConcurrencyError):
            second.save(writer_two, expected_version=0)
    finally:
        first_connection.close()
        second_connection.close()


def test_invalid_metadata_rolls_back_aggregate_and_event(connection):
    repository = SQLiteShipmentRepository(connection, clock=lambda: NOW)
    changed = shipment().transition(ShipmentStatus.BOOKED, at=NOW)
    with pytest.raises(SerializationError):
        repository.add(changed, metadata={"bad": object()})
    assert repository.exists(TENANT_A, changed.id) is False
    assert SQLiteOutbox(connection).pending(TENANT_A) == ()


def test_outbox_order_tenant_scope_publish_idempotency_and_retry(connection):
    repository = SQLiteQuoteRepository(connection, clock=lambda: NOW)
    draft = Quote(Identifier("quote"), TENANT_A, QuoteStatus.DRAFT)
    offered = draft.transition(QuoteStatus.OFFERED, at=NOW)
    accepted = offered.transition(QuoteStatus.ACCEPTED, at=NOW)
    repository.add(accepted)
    repository_b = SQLiteQuoteRepository(connection, clock=lambda: NOW)
    repository_b.add(Quote(Identifier("other"), TENANT_B, QuoteStatus.DRAFT).transition(QuoteStatus.OFFERED, at=NOW))
    outbox = SQLiteOutbox(connection, clock=lambda: NOW)
    pending = outbox.pending(TENANT_A)
    assert [item.aggregate_version for item in pending] == [1, 2]
    assert all(item.tenant_id == TENANT_A for item in pending)
    outbox.mark_failed(TENANT_A, pending[0].event_id, "x" * 1500)
    assert outbox.pending(TENANT_A)[0].delivery_attempts == 1
    outbox.mark_published(TENANT_A, pending[0].event_id)
    outbox.mark_published(TENANT_A, pending[0].event_id)
    assert len(outbox.pending(TENANT_A)) == 1


def test_duplicate_outbox_event_is_idempotent_only_when_payload_matches(connection):
    repository = SQLiteQuoteRepository(connection, clock=lambda: NOW)
    aggregate = Quote(Identifier("quote"), TENANT_A, QuoteStatus.DRAFT).transition(QuoteStatus.OFFERED, at=NOW)
    repository.add(aggregate, metadata={"source": "same"})
    connection.execute("BEGIN IMMEDIATE")
    repository._insert_events(aggregate, '{"source":"same"}', None, None)
    connection.commit()
    assert len(SQLiteOutbox(connection).pending(TENANT_A)) == 1


def test_codec_round_trip_malformed_unknown_version_and_type():
    value = shipment().transition(ShipmentStatus.BOOKED, at=NOW)
    assert decode_aggregate(encode_aggregate(value)) == value
    assert decode_aggregate(encode_aggregate(customer("c"))) == customer("c")
    with pytest.raises(SerializationError):
        decode_aggregate("not-json")
    with pytest.raises(UnsupportedSchemaVersionError):
        decode_aggregate('{"schema":"v999","type":"Customer"}')
    with pytest.raises(SerializationError):
        decode_aggregate('{"schema":"afritech.novalogistics.persistence.v1","type":"builtins.eval"}')


def test_page_and_query_validation(connection):
    with pytest.raises(RepositoryError):
        Page(limit=0)
    repository = SQLiteCustomerRepository(connection)
    with pytest.raises(RepositoryError):
        repository.list(TENANT_A, AggregateQuery(updated_from=datetime(2026, 1, 1)))


def test_migrations_fresh_repeat_history_tables_indexes_and_foreign_keys():
    connection = sqlite3.connect(":memory:", isolation_level=None)
    try:
        runner = MigrationRunner(connection, clock=lambda: NOW)
        assert runner.migrate() == tuple(migration.migration_id for migration in MIGRATIONS)
        assert runner.migrate() == ()
        assert runner.applied() == tuple(migration.migration_id for migration in MIGRATIONS)
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        indexes = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='index'")}
        assert {"novalogistics_aggregates", "novalogistics_outbox", "novalogistics_schema_migrations"} <= tables
        assert {"idx_nl_aggregate_tenant_type_status", "idx_nl_outbox_pending"} <= indexes
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        connection.close()


def test_failed_migration_rolls_back_its_schema_and_history():
    connection = sqlite3.connect(":memory:", isolation_level=None)
    migration = Migration("0001_failure", ("CREATE TABLE should_rollback(id TEXT)", "INVALID SQL"))
    try:
        with pytest.raises(MigrationError):
            MigrationRunner(connection, (migration,), clock=lambda: NOW).migrate()
        assert connection.execute("SELECT name FROM sqlite_master WHERE name='should_rollback'").fetchone() is None
        assert connection.execute("SELECT COUNT(*) FROM novalogistics_schema_migrations").fetchone()[0] == 0
    finally:
        connection.close()


def test_all_required_explicit_repository_adapters_are_exported():
    import afritech.novalogistics.sqlite as persistence

    required = "Customer Supplier Carrier Driver Vehicle Trailer Warehouse Dock Zone BinLocation Item SKU HandlingUnit Package Pallet Shipment ShipmentLeg Stop Load Consignment Delivery Route Order PurchaseOrder SalesOrder Quote Rate ServiceLevel TrackingEvent ProofOfDelivery Incident Claim".split()
    assert all(hasattr(persistence, f"SQLite{name}Repository") for name in required)
