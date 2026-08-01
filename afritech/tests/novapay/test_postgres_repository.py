from __future__ import annotations

from dataclasses import dataclass

from afritech.novapay.repository import PostgresNovaPayRepository
from afritech.novapay.schema import TABLE_NAMES, create_postgres_table_sql


@dataclass
class _Result:
    row: dict[str, object] | None = None

    def fetchone(self) -> dict[str, object] | None:
        return self.row


class _Connection:
    def __init__(self) -> None:
        self.autocommit = False
        self.statements: list[tuple[str, tuple[object, ...] | None]] = []

    def execute(self, sql: str, params: tuple[object, ...] | None = None) -> _Result:
        self.statements.append((sql, params))
        if "RETURNING *" in sql:
            assert params is not None
            payload_json = params[5]
            return _Result(
                {
                    "record_id": params[0],
                    "organization_id": params[1],
                    "status": params[2],
                    "payload_json": payload_json,
                    "created_at": params[6],
                    "updated_at": params[7],
                }
            )
        return _Result()

    def close(self) -> None:  # pragma: no cover - compatibility hook
        return None


def test_postgres_ddl_has_no_duplicate_base_columns() -> None:
    base_columns = (
        "record_id",
        "organization_id",
        "status",
        "version",
        "idempotency_key",
        "payload_json",
        "created_at",
        "updated_at",
    )

    for table_name in TABLE_NAMES:
        definitions = [
            line.strip().split(maxsplit=1)[0].lower()
            for line in create_postgres_table_sql(table_name).splitlines()
            if line.strip() and not line.lstrip().upper().startswith(("CREATE ", ")"))
        ]
        for column in base_columns:
            assert definitions.count(column) == 1, (
                f"{table_name} defines base column {column!r} "
                f"{definitions.count(column)} times"
            )


def test_postgres_repository_uses_normalized_schema_and_columns(monkeypatch) -> None:
    connection = _Connection()
    monkeypatch.setattr(
        "afritech.novapay.repository.psycopg.connect",
        lambda dsn, row_factory=None: connection,
    )

    repo = PostgresNovaPayRepository("postgresql://example/db")
    record = repo.upsert(
        "novapay_wallets",
        record_id="wallet-1",
        organization_id="org-pay",
        status="active",
        payload={
            "wallet_id": "wallet-1",
            "owner_id": "customer-1",
            "owner_type": "consumer",
            "currency": "AUD",
            "balance": "10.00",
            "metadata": {"tier": "standard"},
        },
    )

    ddl = "\n".join(sql for sql, _ in connection.statements[: len(repo.table_names())])
    assert "version INTEGER NOT NULL DEFAULT 1" in ddl
    assert "idempotency_key TEXT UNIQUE" in ddl
    assert "balance NUMERIC(20,2) NOT NULL DEFAULT 0" in ddl

    upsert_sql, upsert_params = connection.statements[-1]
    assert "wallet_id" in upsert_sql
    assert "balance" in upsert_sql
    assert "metadata_json" in upsert_sql
    assert upsert_params is not None
    assert upsert_params[0] == "wallet-1"
    assert upsert_params[1] == "org-pay"
    assert upsert_params[2] == "active"
    assert record.payload["wallet_id"] == "wallet-1"
    assert record.payload["balance"] == "10.00"


def test_postgres_repository_supports_financial_outbox_rows(monkeypatch) -> None:
    connection = _Connection()
    monkeypatch.setattr(
        "afritech.novapay.repository.psycopg.connect",
        lambda dsn, row_factory=None: connection,
    )

    repo = PostgresNovaPayRepository("postgresql://example/db")
    event = repo.enqueue_outbox(
        outbox_event_id="outbox-1",
        organization_id="org-pay",
        event_type="TRANSFER_POSTED",
        resource_type="TRANSFER",
        resource_id="transfer-1",
        payload={"transaction_id": "txn-1", "amount": "10.00"},
        idempotency_key="idem-1",
        actor_id="actor-1",
        correlation_id="corr-1",
        causation_id="caus-1",
    )

    outbox_ddl = "\n".join(sql for sql, _ in connection.statements[: len(repo.table_names())])
    assert "novapay_financial_outbox" in outbox_ddl
    assert "outbox_event_id TEXT NOT NULL" in outbox_ddl
    assert "retry_count INTEGER NOT NULL DEFAULT 0" in outbox_ddl
    assert "dead_letter_reason TEXT" in outbox_ddl

    outbox_sql, outbox_params = connection.statements[-1]
    assert "novapay_financial_outbox" in outbox_sql
    assert "payload_json" in outbox_sql
    assert outbox_params is not None
    assert outbox_params[0] == "outbox-1"
    assert outbox_params[1] == "org-pay"
    assert outbox_params[2] == "pending"
    assert event.payload["event_type"] == "TRANSFER_POSTED"
    assert event.payload["resource_id"] == "transfer-1"
