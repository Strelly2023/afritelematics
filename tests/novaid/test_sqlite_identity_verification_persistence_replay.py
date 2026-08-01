from __future__ import annotations

import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from afritech.novaid.persistence.document_repository import (
    DocumentPersistenceConflictError,
    DocumentPersistenceIntegrityError,
)
from afritech.novaid.persistence.identity_verification_codec import (
    encode_identity_verification_record_json,
)
from afritech.novaid.persistence.sqlite_document_repository import (
    SQLiteIdentityDocumentRepository,
)
from afritech.novaid.persistence.sqlite_identity_verification_persistence_coordinator import (
    SQLiteIdentityVerificationPersistenceCoordinator,
)
from tests.novaid.test_identity_verification_evidence_factory import (
    evidence_and_verification,
)
from tests.novaid.test_sqlite_identity_verification_persistence_coordinator import (
    document_for_verification,
)


@pytest.fixture
def connection() -> sqlite3.Connection:
    database = sqlite3.connect(":memory:")

    try:
        yield database
    finally:
        database.close()


@pytest.fixture
def coordinator(
    connection: sqlite3.Connection,
) -> SQLiteIdentityVerificationPersistenceCoordinator:
    return SQLiteIdentityVerificationPersistenceCoordinator(
        connection
    )


def persist_document(
    connection: sqlite3.Connection,
    verification,
) -> None:
    SQLiteIdentityDocumentRepository(
        connection
    ).add_document(
        document_for_verification(verification)
    )


def row_counts(
    connection: sqlite3.Connection,
) -> tuple[int, int]:
    verification_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM novaid_identity_verifications
        """
    ).fetchone()[0]

    evidence_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM novaid_identity_verification_evidence_refs
        """
    ).fetchone()[0]

    return verification_count, evidence_count


def test_identical_replay_is_idempotent(
    connection: sqlite3.Connection,
    coordinator: SQLiteIdentityVerificationPersistenceCoordinator,
) -> None:
    evidence, verification = evidence_and_verification()
    persist_document(connection, verification)

    first = coordinator.persist(
        verification=verification,
        evidence=evidence,
    )
    second = coordinator.persist(
        verification=verification,
        evidence=evidence,
    )

    assert second == first
    assert row_counts(connection) == (1, 4)


def test_changed_verification_replay_is_rejected(
    connection: sqlite3.Connection,
    coordinator: SQLiteIdentityVerificationPersistenceCoordinator,
) -> None:
    evidence, verification = evidence_and_verification()
    persist_document(connection, verification)

    coordinator.persist(
        verification=verification,
        evidence=evidence,
    )

    changed = replace(
        verification,
        combined_score=0.91,
    )

    with pytest.raises(
        DocumentPersistenceConflictError,
        match=(
            "IDENTITY_VERIFICATION_REPLAY_"
            "PAYLOAD_MISMATCH"
        ),
    ):
        coordinator.persist(
            verification=changed,
            evidence=evidence,
        )

    assert row_counts(connection) == (1, 4)


def test_changed_evidence_metadata_replay_is_rejected(
    connection: sqlite3.Connection,
    coordinator: SQLiteIdentityVerificationPersistenceCoordinator,
) -> None:
    evidence, verification = evidence_and_verification()
    persist_document(connection, verification)

    coordinator.persist(
        verification=verification,
        evidence=evidence,
        metadata={"region": "AU"},
    )

    with pytest.raises(
        DocumentPersistenceConflictError,
        match=(
            "IDENTITY_VERIFICATION_EVIDENCE_"
            "REPLAY_MISMATCH"
        ),
    ):
        coordinator.persist(
            verification=verification,
            evidence=evidence,
            metadata={"region": "NZ"},
        )

    assert row_counts(connection) == (1, 4)


def test_bundle_can_be_loaded_deterministically(
    connection: sqlite3.Connection,
    coordinator: SQLiteIdentityVerificationPersistenceCoordinator,
) -> None:
    evidence, verification = evidence_and_verification()
    persist_document(connection, verification)

    persisted = coordinator.persist(
        verification=verification,
        evidence=evidence,
    )

    loaded = coordinator.load_persisted_bundle(
        tenant_id=verification.tenant_id,
        verification_id=verification.verification_id,
    )

    assert loaded == persisted
    assert loaded is not persisted

    assert tuple(
        item.evidence_type.value
        for item in loaded.evidence_references
    ) == tuple(
        sorted(
            item.evidence_type.value
            for item in loaded.evidence_references
        )
    )


def test_missing_bundle_returns_none(
    coordinator: SQLiteIdentityVerificationPersistenceCoordinator,
) -> None:
    assert coordinator.load_persisted_bundle(
        tenant_id="tenant-missing",
        verification_id="verification-missing",
    ) is None


def test_bundle_loading_is_tenant_scoped(
    connection: sqlite3.Connection,
    coordinator: SQLiteIdentityVerificationPersistenceCoordinator,
) -> None:
    evidence, verification = evidence_and_verification()
    persist_document(connection, verification)

    coordinator.persist(
        verification=verification,
        evidence=evidence,
    )

    assert coordinator.load_persisted_bundle(
        tenant_id="different-tenant",
        verification_id=verification.verification_id,
    ) is None


def test_incomplete_evidence_set_fails_closed(
    connection: sqlite3.Connection,
    coordinator: SQLiteIdentityVerificationPersistenceCoordinator,
) -> None:
    evidence, verification = evidence_and_verification()
    persist_document(connection, verification)

    coordinator.persist(
        verification=verification,
        evidence=evidence,
    )

    connection.execute(
        """
        DELETE FROM novaid_identity_verification_evidence_refs
        WHERE tenant_id = ?
          AND verification_id = ?
          AND evidence_type = 'LIVENESS_ASSESSMENT'
        """,
        (
            verification.tenant_id,
            verification.verification_id,
        ),
    )
    connection.commit()

    with pytest.raises(
        DocumentPersistenceIntegrityError,
        match=(
            "IDENTITY_VERIFICATION_EVIDENCE_"
            "SET_INCOMPLETE"
        ),
    ):
        coordinator.load_persisted_bundle(
            tenant_id=verification.tenant_id,
            verification_id=verification.verification_id,
        )


def test_corrupt_verification_payload_fails_closed(
    connection: sqlite3.Connection,
    coordinator: SQLiteIdentityVerificationPersistenceCoordinator,
) -> None:
    evidence, verification = evidence_and_verification()
    persist_document(connection, verification)

    coordinator.persist(
        verification=verification,
        evidence=evidence,
    )

    connection.execute(
        """
        UPDATE novaid_identity_verifications
        SET verification_payload_json = ?
        WHERE tenant_id = ?
          AND verification_id = ?
        """,
        (
            "{",
            verification.tenant_id,
            verification.verification_id,
        ),
    )
    connection.commit()

    with pytest.raises(
        DocumentPersistenceIntegrityError,
        match="STORED_VERIFICATION_PAYLOAD_INVALID",
    ):
        coordinator.load_persisted_bundle(
            tenant_id=verification.tenant_id,
            verification_id=verification.verification_id,
        )


def test_changed_stored_evidence_identifier_fails_closed(
    connection: sqlite3.Connection,
    coordinator: SQLiteIdentityVerificationPersistenceCoordinator,
) -> None:
    evidence, verification = evidence_and_verification()
    persist_document(connection, verification)

    coordinator.persist(
        verification=verification,
        evidence=evidence,
    )

    connection.execute(
        """
        UPDATE novaid_identity_verification_evidence_refs
        SET evidence_id = ?
        WHERE tenant_id = ?
          AND verification_id = ?
          AND evidence_type = 'OCR_EXTRACTION'
        """,
        (
            "changed-ocr-evidence-id",
            verification.tenant_id,
            verification.verification_id,
        ),
    )
    connection.commit()

    with pytest.raises(
        DocumentPersistenceIntegrityError,
        match=(
            "STORED_EVIDENCE_REFERENCE_"
            "IDENTIFIER_MISMATCH"
        ),
    ):
        coordinator.load_persisted_bundle(
            tenant_id=verification.tenant_id,
            verification_id=verification.verification_id,
        )


def test_orphaned_evidence_set_fails_closed(
    connection: sqlite3.Connection,
    coordinator: SQLiteIdentityVerificationPersistenceCoordinator,
) -> None:
    connection.execute("PRAGMA foreign_keys = OFF")

    connection.execute(
        """
        INSERT INTO novaid_identity_verification_evidence_refs (
            tenant_id,
            verification_id,
            evidence_type,
            evidence_id,
            evidence_version,
            collected_at,
            metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "tenant-orphan",
            "verification-orphan",
            "OCR_EXTRACTION",
            "evidence-orphan",
            1,
            "2026-08-01T10:00:00+00:00",
            "{}",
        ),
    )
    connection.commit()
    connection.execute("PRAGMA foreign_keys = ON")

    with pytest.raises(
        DocumentPersistenceIntegrityError,
        match="ORPHANED_IDENTITY_VERIFICATION_EVIDENCE_SET",
    ):
        coordinator.load_persisted_bundle(
            tenant_id="tenant-orphan",
            verification_id="verification-orphan",
        )


def test_retry_succeeds_after_rolled_back_attempt(
    connection: sqlite3.Connection,
    coordinator: SQLiteIdentityVerificationPersistenceCoordinator,
) -> None:
    evidence, verification = evidence_and_verification()
    persist_document(connection, verification)

    connection.execute(
        """
        CREATE TRIGGER fail_replay_recovery_probe
        BEFORE INSERT ON
            novaid_identity_verification_evidence_refs
        BEGIN
            SELECT RAISE(
                ABORT,
                'FORCED_RECOVERY_FAILURE'
            );
        END
        """
    )
    connection.commit()

    with pytest.raises(
        DocumentPersistenceIntegrityError,
        match=(
            "IDENTITY_VERIFICATION_"
            "ATOMIC_PERSISTENCE_FAILED"
        ),
    ):
        coordinator.persist(
            verification=verification,
            evidence=evidence,
        )

    assert row_counts(connection) == (0, 0)

    connection.execute(
        """
        DROP TRIGGER fail_replay_recovery_probe
        """
    )
    connection.commit()

    bundle = coordinator.persist(
        verification=verification,
        evidence=evidence,
    )

    assert bundle.verification == verification
    assert row_counts(connection) == (1, 4)


def test_identical_replay_across_connections(
    tmp_path: Path,
) -> None:
    database_path = (
        tmp_path / "verification-replay.sqlite3"
    )

    first_connection = sqlite3.connect(database_path)
    second_connection = sqlite3.connect(database_path)

    try:
        first = (
            SQLiteIdentityVerificationPersistenceCoordinator(
                first_connection
            )
        )
        second = (
            SQLiteIdentityVerificationPersistenceCoordinator(
                second_connection
            )
        )

        evidence, verification = evidence_and_verification()

        SQLiteIdentityDocumentRepository(
            first_connection
        ).add_document(
            document_for_verification(verification)
        )

        first_bundle = first.persist(
            verification=verification,
            evidence=evidence,
        )
        second_bundle = second.persist(
            verification=verification,
            evidence=evidence,
        )

        assert second_bundle == first_bundle

        assert first_connection.execute(
            """
            SELECT COUNT(*)
            FROM novaid_identity_verifications
            """
        ).fetchone() == (1,)

        assert second_connection.execute(
            """
            SELECT COUNT(*)
            FROM novaid_identity_verification_evidence_refs
            """
        ).fetchone() == (4,)
    finally:
        first_connection.close()
        second_connection.close()


@pytest.mark.parametrize(
    ("tenant_id", "verification_id", "error_code"),
    (
        (
            "",
            "verification-1",
            "TENANT_ID_REQUIRED",
        ),
        (
            "tenant-1",
            "",
            "IDENTITY_VERIFICATION_ID_REQUIRED",
        ),
    ),
)
def test_blank_load_identifiers_are_rejected(
    coordinator: SQLiteIdentityVerificationPersistenceCoordinator,
    tenant_id: str,
    verification_id: str,
    error_code: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=error_code,
    ):
        coordinator.load_persisted_bundle(
            tenant_id=tenant_id,
            verification_id=verification_id,
        )
