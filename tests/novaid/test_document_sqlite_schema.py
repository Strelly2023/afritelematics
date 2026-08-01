from __future__ import annotations

import sqlite3

import pytest

from afritech.novaid.persistence.document_sqlite_schema import (
    DOCUMENT_SQLITE_SCHEMA,
    EXPECTED_DOCUMENT_TABLES,
    FORBIDDEN_DOCUMENT_SCHEMA_TERMS,
    initialize_document_sqlite_schema,
    list_document_tables,
)


@pytest.fixture
def connection() -> sqlite3.Connection:
    database = sqlite3.connect(":memory:")

    try:
        initialize_document_sqlite_schema(database)
        yield database
    finally:
        database.close()


def table_columns(
    connection: sqlite3.Connection,
    table_name: str,
) -> tuple[str, ...]:
    rows = connection.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return tuple(
        row[1]
        for row in rows
    )


def index_names(
    connection: sqlite3.Connection,
    table_name: str,
) -> tuple[str, ...]:
    rows = connection.execute(
        f"PRAGMA index_list({table_name})"
    ).fetchall()

    return tuple(
        row[1]
        for row in rows
    )


def test_schema_creates_all_document_tables(
    connection: sqlite3.Connection,
) -> None:
    tables = set(
        list_document_tables(connection)
    )

    assert EXPECTED_DOCUMENT_TABLES.issubset(tables)


@pytest.mark.parametrize(
    "table_name",
    tuple(sorted(EXPECTED_DOCUMENT_TABLES)),
)
def test_all_tables_are_tenant_scoped(
    connection: sqlite3.Connection,
    table_name: str,
) -> None:
    assert "tenant_id" in table_columns(
        connection,
        table_name,
    )


def test_documents_use_composite_tenant_primary_key(
    connection: sqlite3.Connection,
) -> None:
    rows = connection.execute(
        "PRAGMA table_info(novaid_identity_documents)"
    ).fetchall()

    primary_key_columns = tuple(
        row[1]
        for row in rows
        if row[5] > 0
    )

    assert primary_key_columns == (
        "tenant_id",
        "document_id",
    )


def test_verifications_use_composite_tenant_primary_key(
    connection: sqlite3.Connection,
) -> None:
    rows = connection.execute(
        "PRAGMA table_info(novaid_identity_verifications)"
    ).fetchall()

    primary_key_columns = tuple(
        row[1]
        for row in rows
        if row[5] > 0
    )

    assert primary_key_columns == (
        "tenant_id",
        "verification_id",
    )


def test_foreign_keys_are_enabled(
    connection: sqlite3.Connection,
) -> None:
    enabled = connection.execute(
        "PRAGMA foreign_keys"
    ).fetchone()

    assert enabled == (1,)


def test_cross_tenant_capture_reference_fails_closed(
    connection: sqlite3.Connection,
) -> None:
    connection.execute(
        """
        INSERT INTO novaid_identity_documents (
            tenant_id,
            document_id,
            identity_id,
            document_type,
            issuing_country,
            verification_status,
            created_at,
            updated_at,
            version,
            document_payload_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "tenant-a",
            "document-1",
            "identity-1",
            "PASSPORT",
            "AU",
            "CAPTURED",
            "2026-08-01T00:00:00+00:00",
            "2026-08-01T00:00:00+00:00",
            1,
            "{}",
        ),
    )

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO novaid_document_captures (
                tenant_id,
                capture_id,
                document_id,
                capture_reference,
                capture_side,
                media_type,
                checksum,
                captured_at,
                capture_order
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "tenant-b",
                "capture-1",
                "document-1",
                "secure://capture-1",
                "FRONT",
                "IMAGE_JPEG",
                "sha256:test",
                "2026-08-01T00:00:00+00:00",
                0,
            ),
        )


def test_document_version_must_be_positive(
    connection: sqlite3.Connection,
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO novaid_identity_documents (
                tenant_id,
                document_id,
                identity_id,
                document_type,
                issuing_country,
                verification_status,
                created_at,
                updated_at,
                version
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "tenant-a",
                "document-1",
                "identity-1",
                "PASSPORT",
                "AU",
                "CAPTURED",
                "2026-08-01T00:00:00+00:00",
                "2026-08-01T00:00:00+00:00",
                0,
            ),
        )


def test_verification_score_is_bounded(
    connection: sqlite3.Connection,
) -> None:
    connection.execute(
        """
        INSERT INTO novaid_identity_documents (
            tenant_id,
            document_id,
            identity_id,
            document_type,
            issuing_country,
            verification_status,
            created_at,
            updated_at,
            version,
            document_payload_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "tenant-a",
            "document-1",
            "identity-1",
            "PASSPORT",
            "AU",
            "IN_PROGRESS",
            "2026-08-01T00:00:00+00:00",
            "2026-08-01T00:00:00+00:00",
            1,
            "{}",
        ),
    )

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO novaid_identity_verifications (
                tenant_id,
                verification_id,
                identity_id,
                document_id,
                workflow_id,
                correlation_id,
                request_id,
                actor_identity_id,
                document_type,
                purpose,
                decision,
                assurance_level,
                combined_score,
                policy_version,
                document_version,
                verified_at,
                reason_codes_json
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                "tenant-a",
                "verification-1",
                "identity-1",
                "document-1",
                "workflow-1",
                "correlation-1",
                "request-1",
                "actor-1",
                "PASSPORT",
                "EKYC",
                "VERIFIED",
                "NID_AL2",
                1.1,
                "policy-v1",
                1,
                "2026-08-01T00:00:00+00:00",
                '["ALL_CONTROLS_SATISFIED"]',
            ),
        )


def test_event_version_is_unique_per_aggregate(
    connection: sqlite3.Connection,
) -> None:
    values = (
        "tenant-a",
        "event-1",
        "DOCUMENT_CAPTURED",
        "IDENTITY_DOCUMENT",
        "document-1",
        1,
        "actor-1",
        "correlation-1",
        "request-1",
        "2026-08-01T00:00:00+00:00",
        "{}",
    )

    connection.execute(
        """
        INSERT INTO novaid_document_persistence_events (
            tenant_id,
            event_id,
            event_type,
            aggregate_type,
            aggregate_id,
            aggregate_version,
            actor_identity_id,
            correlation_id,
            request_id,
            occurred_at,
            payload_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        values,
    )

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO novaid_document_persistence_events (
                tenant_id,
                event_id,
                event_type,
                aggregate_type,
                aggregate_id,
                aggregate_version,
                actor_identity_id,
                correlation_id,
                request_id,
                occurred_at,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "tenant-a",
                "event-2",
                "DOCUMENT_CAPTURED",
                "IDENTITY_DOCUMENT",
                "document-1",
                1,
                "actor-1",
                "correlation-2",
                "request-2",
                "2026-08-01T00:00:01+00:00",
                "{}",
            ),
        )


def test_required_indexes_are_created(
    connection: sqlite3.Connection,
) -> None:
    document_indexes = set(
        index_names(
            connection,
            "novaid_identity_documents",
        )
    )
    verification_indexes = set(
        index_names(
            connection,
            "novaid_identity_verifications",
        )
    )

    assert (
        "idx_novaid_identity_documents_identity"
        in document_indexes
    )
    assert (
        "idx_novaid_identity_documents_status"
        in document_indexes
    )
    assert (
        "idx_novaid_identity_verification_document"
        in verification_indexes
    )
    assert (
        "idx_novaid_identity_verification_identity"
        in verification_indexes
    )


def test_schema_excludes_raw_document_and_biometric_material() -> None:
    normalized_schema = (
        DOCUMENT_SQLITE_SCHEMA.lower()
    )

    detected = sorted(
        term
        for term in FORBIDDEN_DOCUMENT_SCHEMA_TERMS
        if term in normalized_schema
    )

    assert detected == []


def test_schema_initialization_is_idempotent(
    connection: sqlite3.Connection,
) -> None:
    before = list_document_tables(connection)

    initialize_document_sqlite_schema(connection)

    after = list_document_tables(connection)

    assert before == after


def test_invalid_connection_is_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="SQLITE_CONNECTION_REQUIRED",
    ):
        initialize_document_sqlite_schema(
            object()  # type: ignore[arg-type]
        )


def test_documents_store_governed_codec_payload(
    connection: sqlite3.Connection,
) -> None:
    columns = table_columns(
        connection,
        "novaid_identity_documents",
    )

    assert "document_payload_json" in columns


def test_document_payload_column_is_required(
    connection: sqlite3.Connection,
) -> None:
    rows = connection.execute(
        "PRAGMA table_info(novaid_identity_documents)"
    ).fetchall()

    columns = {
        row[1]: row
        for row in rows
    }

    payload_column = columns["document_payload_json"]

    # PRAGMA table_info:
    # cid, name, type, notnull, default, pk
    assert payload_column[2].upper() == "TEXT"
    assert payload_column[3] == 1


def test_verifications_store_governed_codec_payload(
    connection: sqlite3.Connection,
) -> None:
    columns = table_columns(
        connection,
        "novaid_identity_verifications",
    )

    assert "verification_payload_json" in columns


def test_verification_payload_column_is_required(
    connection: sqlite3.Connection,
) -> None:
    rows = connection.execute(
        "PRAGMA table_info(novaid_identity_verifications)"
    ).fetchall()

    columns = {
        row[1]: row
        for row in rows
    }

    payload_column = columns[
        "verification_payload_json"
    ]

    assert payload_column[2].upper() == "TEXT"
    assert payload_column[3] == 1


def test_verification_event_context_columns_are_optional(
    connection: sqlite3.Connection,
) -> None:
    rows = connection.execute(
        "PRAGMA table_info(novaid_identity_verifications)"
    ).fetchall()

    columns = {
        row[1]: row
        for row in rows
    }

    assert columns["correlation_id"][3] == 0
    assert columns["request_id"][3] == 0
    assert columns["actor_identity_id"][3] == 0
