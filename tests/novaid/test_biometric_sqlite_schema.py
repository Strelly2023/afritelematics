from __future__ import annotations

from afritech.novaid.persistence.sqlite import (
    NovaIDUnitOfWork,
)


BIOMETRIC_TABLES = (
    "novaid_biometric_consents",
    "novaid_biometric_enrollments",
    "novaid_face_verifications",
    "novaid_face_authentications",
    "novaid_liveness_assessments",
)


FORBIDDEN_COLUMNS = {
    "raw_image",
    "raw_video",
    "video",
    "frames",
    "embedding",
    "embeddings",
    "feature_vector",
    "feature_vectors",
    "template",
    "biometric_template",
    "provider_secret",
    "api_key",
    "private_key",
}


def table_columns(
    store: NovaIDUnitOfWork,
    table: str,
) -> set[str]:
    rows = store.connection.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    return {
        str(row["name"]).lower()
        for row in rows
    }


def test_sqlite_creates_all_biometric_tables() -> None:
    store = NovaIDUnitOfWork()

    with store:
        actual = {
            str(row["name"])
            for row in store.connection.execute(
                "SELECT name "
                "FROM sqlite_master "
                "WHERE type='table'"
            ).fetchall()
        }

    assert set(BIOMETRIC_TABLES) <= actual


def test_biometric_tables_are_tenant_scoped() -> None:
    store = NovaIDUnitOfWork()

    with store:
        for table in BIOMETRIC_TABLES:
            columns = table_columns(
                store,
                table,
            )

            assert "tenant_id" in columns
            assert "identity_id" in columns


def test_biometric_schema_excludes_raw_material() -> None:
    store = NovaIDUnitOfWork()

    with store:
        for table in BIOMETRIC_TABLES:
            columns = table_columns(
                store,
                table,
            )

            assert not (
                columns & FORBIDDEN_COLUMNS
            ), (
                table,
                columns & FORBIDDEN_COLUMNS,
            )


def test_enrollment_stores_reference_not_template() -> None:
    store = NovaIDUnitOfWork()

    with store:
        columns = table_columns(
            store,
            "novaid_biometric_enrollments",
        )

    assert "template_reference" in columns
    assert "template" not in columns
    assert "biometric_template" not in columns


def test_biometric_indexes_are_created() -> None:
    store = NovaIDUnitOfWork()

    expected_indexes = {
        "ix_novaid_biometric_consent_identity",
        "ix_novaid_biometric_enrollment_identity",
        "ix_novaid_biometric_enrollment_consent",
        "ix_novaid_face_verification_identity",
        "ix_novaid_face_verification_enrollment",
        "ix_novaid_face_authentication_identity",
        "ix_novaid_face_authentication_verification",
        "ix_novaid_liveness_identity",
        "ix_novaid_liveness_decision",
    }

    with store:
        actual_indexes = {
            str(row["name"])
            for row in store.connection.execute(
                "SELECT name "
                "FROM sqlite_master "
                "WHERE type='index'"
            ).fetchall()
        }

    assert expected_indexes <= actual_indexes


def test_foreign_keys_are_enabled_for_biometric_tables() -> None:
    store = NovaIDUnitOfWork()

    with store:
        enrollment_foreign_keys = (
            store.connection.execute(
                "PRAGMA foreign_key_list("
                "novaid_biometric_enrollments"
                ")"
            ).fetchall()
        )

        verification_foreign_keys = (
            store.connection.execute(
                "PRAGMA foreign_key_list("
                "novaid_face_verifications"
                ")"
            ).fetchall()
        )

    enrollment_targets = {
        str(row["table"])
        for row in enrollment_foreign_keys
    }
    verification_targets = {
        str(row["table"])
        for row in verification_foreign_keys
    }

    assert "novaid_tenants" in enrollment_targets
    assert "novaid_identities" in enrollment_targets
    assert (
        "novaid_biometric_consents"
        in enrollment_targets
    )

    assert "novaid_tenants" in verification_targets
    assert "novaid_identities" in verification_targets
    assert (
        "novaid_biometric_enrollments"
        in verification_targets
    )
    assert (
        "novaid_biometric_consents"
        in verification_targets
    )
