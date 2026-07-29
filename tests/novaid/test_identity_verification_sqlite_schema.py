from __future__ import annotations

from collections.abc import Iterable

from afritech.novaid.persistence.sqlite import (
    NovaIDUnitOfWork,
)


EVIDENCE_TABLE = (
    "novaid_identity_verification_evidence"
)
VERIFICATION_TABLE = (
    "novaid_identity_verifications"
)
EVENT_TABLE = (
    "novaid_identity_verification_events"
)

IDENTITY_VERIFICATION_TABLES = (
    EVIDENCE_TABLE,
    VERIFICATION_TABLE,
    EVENT_TABLE,
)

FORBIDDEN_COLUMN_FRAGMENTS = (
    "raw_image",
    "raw_selfie",
    "selfie_image",
    "document_image",
    "raw_video",
    "video_bytes",
    "frames",
    "embedding",
    "feature_vector",
    "biometric_template",
    "face_template",
    "document_bytes",
    "pdf_bytes",
    "raw_provider_response",
    "provider_secret",
    "api_key",
    "private_key",
    "access_token",
)


def table_names(
    store: NovaIDUnitOfWork,
) -> set[str]:
    return {
        str(row["name"])
        for row in store.connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table'"
        ).fetchall()
    }


def column_names(
    store: NovaIDUnitOfWork,
    table: str,
) -> set[str]:
    return {
        str(row["name"])
        for row in store.connection.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()
    }


def index_names(
    store: NovaIDUnitOfWork,
) -> set[str]:
    return {
        str(row["name"])
        for row in store.connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='index' "
            "AND name NOT LIKE 'sqlite_autoindex_%'"
        ).fetchall()
    }


def foreign_key_targets(
    store: NovaIDUnitOfWork,
    table: str,
) -> set[str]:
    return {
        str(row["table"])
        for row in store.connection.execute(
            f"PRAGMA foreign_key_list({table})"
        ).fetchall()
    }


def assert_columns_present(
    actual: set[str],
    required: Iterable[str],
) -> None:
    missing = set(required) - actual

    assert not missing, (
        f"Missing expected columns: {sorted(missing)}"
    )


def test_sqlite_creates_identity_verification_tables() -> None:
    store = NovaIDUnitOfWork()

    with store:
        actual = table_names(store)

    assert set(
        IDENTITY_VERIFICATION_TABLES
    ).issubset(actual)


def test_identity_verification_tables_are_tenant_scoped() -> None:
    store = NovaIDUnitOfWork()

    with store:
        for table in IDENTITY_VERIFICATION_TABLES:
            assert "tenant_id" in column_names(
                store,
                table,
            )


def test_evidence_schema_contains_governed_references() -> None:
    store = NovaIDUnitOfWork()

    with store:
        actual = column_names(
            store,
            EVIDENCE_TABLE,
        )

    assert_columns_present(
        actual,
        (
            "workflow_id",
            "tenant_id",
            "identity_id",
            "document_id",
            "document_version",
            "ocr_extraction_id",
            "authenticity_assessment_id",
            "selfie_match_id",
            "evidence_payload",
            "evidence_hash",
            "schema_version",
            "persisted_at",
        ),
    )


def test_verification_schema_supports_traceability() -> None:
    store = NovaIDUnitOfWork()

    with store:
        actual = column_names(
            store,
            VERIFICATION_TABLE,
        )

    assert_columns_present(
        actual,
        (
            "verification_id",
            "tenant_id",
            "identity_id",
            "workflow_id",
            "document_id",
            "document_version",
            "decision",
            "current_assurance_level",
            "resulting_assurance_level",
            "policy_version",
            "combined_score",
            "ocr_score",
            "authenticity_score",
            "selfie_match_score",
            "liveness_score",
            "reason_codes",
            "verification_payload",
            "verified_at",
            "version",
        ),
    )


def test_event_schema_supports_audit_and_replay() -> None:
    store = NovaIDUnitOfWork()

    with store:
        actual = column_names(
            store,
            EVENT_TABLE,
        )

    assert_columns_present(
        actual,
        (
            "event_id",
            "tenant_id",
            "identity_id",
            "verification_id",
            "workflow_id",
            "event_type",
            "decision",
            "correlation_id",
            "request_id",
            "policy_version",
            "event_payload",
            "occurred_at",
            "persisted_at",
            "schema_version",
        ),
    )


def test_schema_excludes_raw_identity_material() -> None:
    store = NovaIDUnitOfWork()

    with store:
        for table in IDENTITY_VERIFICATION_TABLES:
            columns = {
                column.lower()
                for column in column_names(
                    store,
                    table,
                )
            }

            for forbidden in FORBIDDEN_COLUMN_FRAGMENTS:
                assert forbidden not in columns, (
                    f"{table} contains forbidden "
                    f"raw-material column {forbidden}"
                )


def test_identity_verification_indexes_are_created() -> None:
    expected = {
        (
            "ix_novaid_identity_verification_"
            "evidence_identity"
        ),
        (
            "ix_novaid_identity_verification_"
            "evidence_document"
        ),
        (
            "ix_novaid_identity_verifications_"
            "identity"
        ),
        (
            "ix_novaid_identity_verifications_"
            "decision"
        ),
        (
            "ix_novaid_identity_verifications_"
            "document"
        ),
        (
            "ix_novaid_identity_verification_"
            "events_verification"
        ),
        (
            "ix_novaid_identity_verification_"
            "events_identity"
        ),
        (
            "ix_novaid_identity_verification_"
            "events_correlation"
        ),
    }

    store = NovaIDUnitOfWork()

    with store:
        actual = index_names(store)

    assert expected.issubset(actual)


def test_identity_verification_foreign_keys_are_enabled() -> None:
    store = NovaIDUnitOfWork()

    with store:
        enabled = store.connection.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]

        evidence_targets = foreign_key_targets(
            store,
            EVIDENCE_TABLE,
        )
        verification_targets = foreign_key_targets(
            store,
            VERIFICATION_TABLE,
        )
        event_targets = foreign_key_targets(
            store,
            EVENT_TABLE,
        )

    assert enabled == 1

    assert "novaid_tenants" in evidence_targets
    assert "novaid_identities" in evidence_targets

    assert "novaid_tenants" in verification_targets
    assert "novaid_identities" in verification_targets
    assert EVIDENCE_TABLE in verification_targets

    assert "novaid_tenants" in event_targets
    assert "novaid_identities" in event_targets
    assert VERIFICATION_TABLE in event_targets
    assert EVIDENCE_TABLE in event_targets


def test_score_constraints_fail_closed() -> None:
    store = NovaIDUnitOfWork()

    with store:
        sql = store.connection.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE type='table' AND name=?",
            (VERIFICATION_TABLE,),
        ).fetchone()["sql"]

    normalized = " ".join(
        str(sql).lower().split()
    )

    for score in (
        "combined_score",
        "ocr_score",
        "authenticity_score",
        "selfie_match_score",
        "liveness_score",
    ):
        assert f"{score} >= 0.0" in normalized
        assert f"{score} <= 1.0" in normalized


def test_version_constraints_are_present() -> None:
    store = NovaIDUnitOfWork()

    with store:
        verification_sql = store.connection.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE type='table' AND name=?",
            (VERIFICATION_TABLE,),
        ).fetchone()["sql"]

        evidence_sql = store.connection.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE type='table' AND name=?",
            (EVIDENCE_TABLE,),
        ).fetchone()["sql"]

    assert "version >= 1" in " ".join(
        str(verification_sql).lower().split()
    )
    assert "document_version >= 1" in " ".join(
        str(evidence_sql).lower().split()
    )
