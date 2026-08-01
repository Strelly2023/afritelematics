from __future__ import annotations

import sqlite3
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from afritech.novaid.domain.biometric_models import (
    BiometricPurpose,
)
from afritech.novaid.domain.document_models import (
    DocumentVerificationStatus,
    IdentityDocument,
)
from afritech.novaid.persistence.document_repository import (
    DocumentPersistenceConflictError,
    DocumentPersistenceIntegrityError,
)
from afritech.novaid.persistence.identity_verification_evidence_factory import (
    IdentityVerificationEvidenceFactoryError,
)
from afritech.novaid.persistence.sqlite_document_repository import (
    SQLiteIdentityDocumentRepository,
)
from afritech.novaid.persistence.sqlite_identity_verification_persistence_coordinator import (
    IdentityVerificationPersistenceBundle,
    SQLiteIdentityVerificationPersistenceCoordinator,
)
from afritech.novaid.persistence.sqlite_identity_verification_repository import (
    SQLiteIdentityVerificationRepository,
)
from afritech.novaid.persistence.sqlite_identity_verification_evidence_repository import (
    SQLiteIdentityVerificationEvidenceRepository,
)
from tests.novaid.test_identity_verification_evidence_factory import (
    evidence_and_verification,
)


def document_for_verification(
    verification,
) -> IdentityDocument:
    now = datetime(
        2026,
        8,
        1,
        10,
        0,
        0,
        tzinfo=timezone.utc,
    )

    return IdentityDocument(
        document_id=verification.document_id,
        tenant_id=verification.tenant_id,
        identity_id=verification.identity_id,
        document_type=verification.document_type,
        issuing_country_code="AU",
        status=DocumentVerificationStatus.IN_PROGRESS,
        purpose=BiometricPurpose.EKYC,
        created_at=now,
        updated_at=now,
        version=verification.document_version,
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


def persist_bound_document(
    connection: sqlite3.Connection,
    verification,
) -> None:
    repository = SQLiteIdentityDocumentRepository(
        connection
    )
    repository.add_document(
        document_for_verification(verification)
    )


def test_atomic_persistence_round_trip(
    connection: sqlite3.Connection,
    coordinator: SQLiteIdentityVerificationPersistenceCoordinator,
) -> None:
    evidence, verification = evidence_and_verification()
    persist_bound_document(connection, verification)

    bundle = coordinator.persist(
        verification=verification,
        evidence=evidence,
    )

    assert isinstance(
        bundle,
        IdentityVerificationPersistenceBundle,
    )
    assert bundle.verification == verification
    assert len(bundle.evidence_references) == 4

    verification_repository = (
        SQLiteIdentityVerificationRepository(
            connection
        )
    )
    evidence_repository = (
        SQLiteIdentityVerificationEvidenceRepository(
            connection
        )
    )

    assert verification_repository.get_verification(
        tenant_id=verification.tenant_id,
        verification_id=verification.verification_id,
    ) == verification

    assert len(
        evidence_repository.list_verification_evidence(
            tenant_id=verification.tenant_id,
            verification_id=verification.verification_id,
        )
    ) == 4


def test_bundle_references_are_deterministic(
    connection: sqlite3.Connection,
    coordinator: SQLiteIdentityVerificationPersistenceCoordinator,
) -> None:
    evidence, verification = evidence_and_verification()
    persist_bound_document(connection, verification)

    bundle = coordinator.persist(
        verification=verification,
        evidence=evidence,
    )

    values = tuple(
        item.evidence_type.value
        for item in bundle.evidence_references
    )

    assert values == tuple(sorted(values))


def test_missing_document_is_rejected_before_transaction(
    coordinator: SQLiteIdentityVerificationPersistenceCoordinator,
) -> None:
    evidence, verification = evidence_and_verification()

    with pytest.raises(
        DocumentPersistenceIntegrityError,
        match="IDENTITY_VERIFICATION_DOCUMENT_NOT_FOUND",
    ):
        coordinator.persist(
            verification=verification,
            evidence=evidence,
        )


def test_evidence_mismatch_is_rejected_before_insert(
    connection: sqlite3.Connection,
    coordinator: SQLiteIdentityVerificationPersistenceCoordinator,
) -> None:
    evidence, verification = evidence_and_verification()
    persist_bound_document(connection, verification)

    evidence = replace(
        evidence,
        workflow_id="different-workflow",
    )

    with pytest.raises(
        IdentityVerificationEvidenceFactoryError,
        match=(
            "IDENTITY_VERIFICATION_EVIDENCE_"
            "WORKFLOW_MISMATCH"
        ),
    ):
        coordinator.persist(
            verification=verification,
            evidence=evidence,
        )

    assert connection.execute(
        """
        SELECT COUNT(*)
        FROM novaid_identity_verifications
        """
    ).fetchone() == (0,)


def test_duplicate_bundle_is_idempotent(
    connection: sqlite3.Connection,
    coordinator: SQLiteIdentityVerificationPersistenceCoordinator,
) -> None:
    evidence, verification = evidence_and_verification()
    persist_bound_document(connection, verification)

    first = coordinator.persist(
        verification=verification,
        evidence=evidence,
    )

    second = coordinator.persist(
        verification=verification,
        evidence=evidence,
    )

    assert second == first

    assert connection.execute(
        """
        SELECT COUNT(*)
        FROM novaid_identity_verifications
        """
    ).fetchone() == (1,)

    assert connection.execute(
        """
        SELECT COUNT(*)
        FROM novaid_identity_verification_evidence_refs
        """
    ).fetchone() == (4,)


def test_evidence_insert_failure_rolls_back_verification(
    connection: sqlite3.Connection,
    coordinator: SQLiteIdentityVerificationPersistenceCoordinator,
) -> None:
    evidence, verification = evidence_and_verification()
    persist_bound_document(connection, verification)

    connection.execute(
        """
        CREATE TRIGGER fail_selfie_evidence_insert
        BEFORE INSERT ON
            novaid_identity_verification_evidence_refs
        WHEN NEW.evidence_type = 'DOCUMENT_SELFIE_MATCH'
        BEGIN
            SELECT RAISE(
                ABORT,
                'FORCED_EVIDENCE_FAILURE'
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

    assert connection.execute(
        """
        SELECT COUNT(*)
        FROM novaid_identity_verifications
        """
    ).fetchone() == (0,)

    assert connection.execute(
        """
        SELECT COUNT(*)
        FROM novaid_identity_verification_evidence_refs
        """
    ).fetchone() == (0,)


def test_first_evidence_insert_failure_rolls_back_verification(
    connection: sqlite3.Connection,
    coordinator: SQLiteIdentityVerificationPersistenceCoordinator,
) -> None:
    evidence, verification = evidence_and_verification()
    persist_bound_document(connection, verification)

    connection.execute(
        """
        CREATE TRIGGER fail_all_evidence_inserts
        BEFORE INSERT ON
            novaid_identity_verification_evidence_refs
        BEGIN
            SELECT RAISE(
                ABORT,
                'FORCED_FIRST_EVIDENCE_FAILURE'
            );
        END
        """
    )
    connection.commit()

    with pytest.raises(
        DocumentPersistenceIntegrityError,
    ):
        coordinator.persist(
            verification=verification,
            evidence=evidence,
        )

    assert connection.execute(
        """
        SELECT COUNT(*)
        FROM novaid_identity_verifications
        """
    ).fetchone() == (0,)


def test_active_transaction_is_rejected(
    connection: sqlite3.Connection,
    coordinator: SQLiteIdentityVerificationPersistenceCoordinator,
) -> None:
    evidence, verification = evidence_and_verification()
    persist_bound_document(connection, verification)

    connection.execute("BEGIN")

    try:
        with pytest.raises(
            DocumentPersistenceIntegrityError,
            match="ACTIVE_SQLITE_TRANSACTION_NOT_SUPPORTED",
        ):
            coordinator.persist(
                verification=verification,
                evidence=evidence,
            )
    finally:
        connection.rollback()


def test_document_identity_binding_is_enforced(
    connection: sqlite3.Connection,
    coordinator: SQLiteIdentityVerificationPersistenceCoordinator,
) -> None:
    evidence, verification = evidence_and_verification()

    altered_document = replace(
        document_for_verification(verification),
        identity_id="different-identity",
    )

    SQLiteIdentityDocumentRepository(
        connection
    ).add_document(altered_document)

    with pytest.raises(
        DocumentPersistenceIntegrityError,
        match=(
            "IDENTITY_VERIFICATION_"
            "IDENTITY_BINDING_MISMATCH"
        ),
    ):
        coordinator.persist(
            verification=verification,
            evidence=evidence,
        )


def test_document_version_binding_is_enforced(
    connection: sqlite3.Connection,
    coordinator: SQLiteIdentityVerificationPersistenceCoordinator,
) -> None:
    evidence, verification = evidence_and_verification()

    altered_document = replace(
        document_for_verification(verification),
        version=verification.document_version + 1,
    )

    SQLiteIdentityDocumentRepository(
        connection
    ).add_document(altered_document)

    with pytest.raises(
        DocumentPersistenceIntegrityError,
        match=(
            "IDENTITY_VERIFICATION_"
            "DOCUMENT_VERSION_MISMATCH"
        ),
    ):
        coordinator.persist(
            verification=verification,
            evidence=evidence,
        )


def test_metadata_is_propagated_to_references(
    connection: sqlite3.Connection,
    coordinator: SQLiteIdentityVerificationPersistenceCoordinator,
) -> None:
    evidence, verification = evidence_and_verification()
    persist_bound_document(connection, verification)

    bundle = coordinator.persist(
        verification=verification,
        evidence=evidence,
        metadata={
            "region": "AU",
        },
    )

    assert all(
        reference.metadata["region"] == "AU"
        for reference in bundle.evidence_references
    )


def test_caller_connection_remains_open(
    connection: sqlite3.Connection,
) -> None:
    coordinator = (
        SQLiteIdentityVerificationPersistenceCoordinator(
            connection
        )
    )

    del coordinator

    assert connection.execute(
        "SELECT 1"
    ).fetchone() == (1,)


def test_invalid_connection_is_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="SQLITE_CONNECTION_REQUIRED",
    ):
        SQLiteIdentityVerificationPersistenceCoordinator(
            object()  # type: ignore[arg-type]
        )
