from __future__ import annotations

from dataclasses import dataclass

from afritech.novapay.repository import PostgresNovaPayRepository


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
