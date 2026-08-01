from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from afritech.novaid.domain.biometric_models import (
    BiometricPurpose,
)
from afritech.novaid.domain.document_models import (
    DocumentVerificationStatus,
    IdentityDocument,
    IdentityDocumentType,
)
from afritech.novaid.domain.identity_verification_models import (
    IdentityVerificationDecision,
    IdentityVerificationRecord,
)
from afritech.novaid.domain.models import AssuranceLevel
from afritech.novaid.persistence.document_repository import (
    DocumentPersistenceConflictError,
    DocumentPersistenceIntegrityError,
)
from afritech.novaid.persistence.identity_verification_evidence_repository import (
    IdentityVerificationEvidenceReference,
    IdentityVerificationEvidenceRepository,
    IdentityVerificationEvidenceType,
)
from afritech.novaid.persistence.sqlite_document_repository import (
    SQLiteIdentityDocumentRepository,
)
from afritech.novaid.persistence.sqlite_identity_verification_evidence_repository import (
    SQLiteIdentityVerificationEvidenceRepository,
)
from afritech.novaid.persistence.sqlite_identity_verification_repository import (
    SQLiteIdentityVerificationRepository,
)


def uid() -> str:
    return str(uuid4())


def timestamp(
    minute: int = 0,
) -> datetime:
    return datetime(
        2026,
        8,
        1,
        9,
        minute,
        0,
        tzinfo=timezone.utc,
    )


def document() -> IdentityDocument:
    return IdentityDocument(
        document_id=uid(),
        tenant_id=uid(),
        identity_id=uid(),
        document_type=IdentityDocumentType.PASSPORT,
        issuing_country_code="AU",
        status=DocumentVerificationStatus.IN_PROGRESS,
        purpose=BiometricPurpose.EKYC,
        created_at=timestamp(),
        updated_at=timestamp(),
        version=1,
    )


def verification(
    current_document: IdentityDocument,
) -> IdentityVerificationRecord:
    return IdentityVerificationRecord(
        verification_id=uid(),
        workflow_id=uid(),
        tenant_id=current_document.tenant_id,
        identity_id=current_document.identity_id,
        document_id=current_document.document_id,
        document_type=current_document.document_type,
        purpose=BiometricPurpose.EKYC,
        decision=IdentityVerificationDecision.VERIFIED,
        assurance_level=AssuranceLevel.NID_AL2,
        combined_score=0.96,
        ocr_score=0.97,
        authenticity_score=0.96,
        selfie_match_score=0.95,
        liveness_score=0.98,
        ocr_extraction_id=uid(),
        authenticity_assessment_id=uid(),
        selfie_match_id=uid(),
        policy_version="identity-verification-policy-v1",
        document_version=current_document.version,
        verified_at=timestamp(1),
        reason_codes=(
            "ALL_CONTROLS_SATISFIED",
        ),
    )


def reference(
    current_verification: IdentityVerificationRecord,
    *,
    evidence_type: IdentityVerificationEvidenceType = (
        IdentityVerificationEvidenceType.OCR_EXTRACTION
    ),
    evidence_id: str | None = None,
    evidence_version: int = 1,
    minute: int = 2,
) -> IdentityVerificationEvidenceReference:
    return IdentityVerificationEvidenceReference(
        tenant_id=current_verification.tenant_id,
        verification_id=(
            current_verification.verification_id
        ),
        evidence_type=evidence_type,
        evidence_id=evidence_id or uid(),
        evidence_version=evidence_version,
        collected_at=timestamp(minute),
        metadata={
            "algorithm_version": "evidence-v1",
        },
    )


@pytest.fixture
def connection() -> sqlite3.Connection:
    database = sqlite3.connect(":memory:")

    try:
        yield database
    finally:
        database.close()


@pytest.fixture
def document_repository(
    connection: sqlite3.Connection,
) -> SQLiteIdentityDocumentRepository:
    return SQLiteIdentityDocumentRepository(
        connection
    )


@pytest.fixture
def verification_repository(
    connection: sqlite3.Connection,
) -> SQLiteIdentityVerificationRepository:
    return SQLiteIdentityVerificationRepository(
        connection
    )


@pytest.fixture
def repository(
    connection: sqlite3.Connection,
) -> SQLiteIdentityVerificationEvidenceRepository:
    return SQLiteIdentityVerificationEvidenceRepository(
        connection
    )


def persist_verification(
    document_repository: SQLiteIdentityDocumentRepository,
    verification_repository: SQLiteIdentityVerificationRepository,
) -> IdentityVerificationRecord:
    current_document = document()

    document_repository.add_document(
        current_document
    )

    current_verification = verification(
        current_document
    )

    verification_repository.add_verification(
        current_verification
    )

    return current_verification


def test_repository_satisfies_protocol(
    repository: SQLiteIdentityVerificationEvidenceRepository,
) -> None:
    assert isinstance(
        repository,
        IdentityVerificationEvidenceRepository,
    )


def test_add_and_get_reference_round_trip(
    document_repository: SQLiteIdentityDocumentRepository,
    verification_repository: SQLiteIdentityVerificationRepository,
    repository: SQLiteIdentityVerificationEvidenceRepository,
) -> None:
    current_verification = persist_verification(
        document_repository,
        verification_repository,
    )
    current = reference(current_verification)

    repository.add_evidence_reference(current)

    restored = repository.get_evidence_reference(
        tenant_id=current.tenant_id,
        verification_id=current.verification_id,
        evidence_type=current.evidence_type,
    )

    assert restored == current
    assert restored is not current


def test_missing_reference_returns_none(
    repository: SQLiteIdentityVerificationEvidenceRepository,
) -> None:
    assert repository.get_evidence_reference(
        tenant_id=uid(),
        verification_id=uid(),
        evidence_type=(
            IdentityVerificationEvidenceType.OCR_EXTRACTION
        ),
    ) is None


def test_cross_tenant_read_fails_closed(
    document_repository: SQLiteIdentityDocumentRepository,
    verification_repository: SQLiteIdentityVerificationRepository,
    repository: SQLiteIdentityVerificationEvidenceRepository,
) -> None:
    current_verification = persist_verification(
        document_repository,
        verification_repository,
    )
    current = reference(current_verification)

    repository.add_evidence_reference(current)

    assert repository.get_evidence_reference(
        tenant_id=uid(),
        verification_id=current.verification_id,
        evidence_type=current.evidence_type,
    ) is None


def test_missing_verification_is_rejected(
    repository: SQLiteIdentityVerificationEvidenceRepository,
) -> None:
    missing = IdentityVerificationEvidenceReference(
        tenant_id=uid(),
        verification_id=uid(),
        evidence_type=(
            IdentityVerificationEvidenceType.OCR_EXTRACTION
        ),
        evidence_id=uid(),
        evidence_version=1,
        collected_at=timestamp(),
    )

    with pytest.raises(
        DocumentPersistenceIntegrityError,
        match=(
            "IDENTITY_VERIFICATION_NOT_FOUND_"
            "FOR_EVIDENCE_REFERENCE"
        ),
    ):
        repository.add_evidence_reference(
            missing
        )


def test_duplicate_evidence_type_is_rejected(
    document_repository: SQLiteIdentityDocumentRepository,
    verification_repository: SQLiteIdentityVerificationRepository,
    repository: SQLiteIdentityVerificationEvidenceRepository,
) -> None:
    current_verification = persist_verification(
        document_repository,
        verification_repository,
    )

    first = reference(current_verification)
    duplicate = reference(
        current_verification,
        evidence_id=uid(),
    )

    repository.add_evidence_reference(first)

    with pytest.raises(
        DocumentPersistenceConflictError,
        match=(
            "IDENTITY_VERIFICATION_EVIDENCE_"
            "REFERENCE_ALREADY_EXISTS"
        ),
    ):
        repository.add_evidence_reference(
            duplicate
        )


def test_same_evidence_type_is_allowed_for_another_verification(
    document_repository: SQLiteIdentityDocumentRepository,
    verification_repository: SQLiteIdentityVerificationRepository,
    repository: SQLiteIdentityVerificationEvidenceRepository,
) -> None:
    first_verification = persist_verification(
        document_repository,
        verification_repository,
    )
    second_verification = persist_verification(
        document_repository,
        verification_repository,
    )

    first = reference(first_verification)
    second = reference(second_verification)

    repository.add_evidence_reference(first)
    repository.add_evidence_reference(second)

    assert repository.get_evidence_reference(
        tenant_id=first.tenant_id,
        verification_id=first.verification_id,
        evidence_type=first.evidence_type,
    ) == first

    assert repository.get_evidence_reference(
        tenant_id=second.tenant_id,
        verification_id=second.verification_id,
        evidence_type=second.evidence_type,
    ) == second


def test_all_supported_evidence_types_can_be_stored(
    document_repository: SQLiteIdentityDocumentRepository,
    verification_repository: SQLiteIdentityVerificationRepository,
    repository: SQLiteIdentityVerificationEvidenceRepository,
) -> None:
    current_verification = persist_verification(
        document_repository,
        verification_repository,
    )

    expected = tuple(
        reference(
            current_verification,
            evidence_type=evidence_type,
            minute=index + 2,
        )
        for index, evidence_type in enumerate(
            IdentityVerificationEvidenceType
        )
    )

    for item in expected:
        repository.add_evidence_reference(item)

    restored = repository.list_verification_evidence(
        tenant_id=current_verification.tenant_id,
        verification_id=(
            current_verification.verification_id
        ),
    )

    assert {
        item.evidence_type
        for item in restored
    } == set(IdentityVerificationEvidenceType)


def test_list_is_deterministically_ordered(
    document_repository: SQLiteIdentityDocumentRepository,
    verification_repository: SQLiteIdentityVerificationRepository,
    repository: SQLiteIdentityVerificationEvidenceRepository,
) -> None:
    current_verification = persist_verification(
        document_repository,
        verification_repository,
    )

    selfie = reference(
        current_verification,
        evidence_type=(
            IdentityVerificationEvidenceType
            .DOCUMENT_SELFIE_MATCH
        ),
    )
    authenticity = reference(
        current_verification,
        evidence_type=(
            IdentityVerificationEvidenceType
            .DOCUMENT_AUTHENTICITY
        ),
    )
    ocr = reference(
        current_verification,
        evidence_type=(
            IdentityVerificationEvidenceType
            .OCR_EXTRACTION
        ),
    )

    repository.add_evidence_reference(selfie)
    repository.add_evidence_reference(ocr)
    repository.add_evidence_reference(authenticity)

    restored = repository.list_verification_evidence(
        tenant_id=current_verification.tenant_id,
        verification_id=(
            current_verification.verification_id
        ),
    )

    assert tuple(
        item.evidence_type.value
        for item in restored
    ) == tuple(
        sorted(
            (
                selfie.evidence_type.value,
                authenticity.evidence_type.value,
                ocr.evidence_type.value,
            )
        )
    )


def test_empty_history_returns_empty_tuple(
    repository: SQLiteIdentityVerificationEvidenceRepository,
) -> None:
    assert repository.list_verification_evidence(
        tenant_id=uid(),
        verification_id=uid(),
    ) == ()


def test_exists_is_tenant_scoped(
    document_repository: SQLiteIdentityDocumentRepository,
    verification_repository: SQLiteIdentityVerificationRepository,
    repository: SQLiteIdentityVerificationEvidenceRepository,
) -> None:
    current_verification = persist_verification(
        document_repository,
        verification_repository,
    )
    current = reference(current_verification)

    repository.add_evidence_reference(current)

    assert repository.evidence_reference_exists(
        tenant_id=current.tenant_id,
        verification_id=current.verification_id,
        evidence_type=current.evidence_type,
    )

    assert not repository.evidence_reference_exists(
        tenant_id=uid(),
        verification_id=current.verification_id,
        evidence_type=current.evidence_type,
    )


def test_metadata_round_trips_defensively(
    document_repository: SQLiteIdentityDocumentRepository,
    verification_repository: SQLiteIdentityVerificationRepository,
    repository: SQLiteIdentityVerificationEvidenceRepository,
) -> None:
    current_verification = persist_verification(
        document_repository,
        verification_repository,
    )
    current = reference(current_verification)

    repository.add_evidence_reference(current)

    restored = repository.get_evidence_reference(
        tenant_id=current.tenant_id,
        verification_id=current.verification_id,
        evidence_type=current.evidence_type,
    )

    assert restored is not None
    assert restored.metadata == current.metadata
    assert restored.metadata is not current.metadata


def test_corrupt_metadata_fails_closed(
    connection: sqlite3.Connection,
    document_repository: SQLiteIdentityDocumentRepository,
    verification_repository: SQLiteIdentityVerificationRepository,
    repository: SQLiteIdentityVerificationEvidenceRepository,
) -> None:
    current_verification = persist_verification(
        document_repository,
        verification_repository,
    )
    current = reference(current_verification)

    repository.add_evidence_reference(current)

    connection.execute(
        """
        UPDATE novaid_identity_verification_evidence_refs
        SET metadata_json = ?
        WHERE tenant_id = ?
          AND verification_id = ?
          AND evidence_type = ?
        """,
        (
            "{",
            current.tenant_id,
            current.verification_id,
            current.evidence_type.value,
        ),
    )
    connection.commit()

    with pytest.raises(
        DocumentPersistenceIntegrityError,
        match=(
            "STORED_EVIDENCE_REFERENCE_METADATA_INVALID"
        ),
    ):
        repository.get_evidence_reference(
            tenant_id=current.tenant_id,
            verification_id=current.verification_id,
            evidence_type=current.evidence_type,
        )


def test_invalid_stored_timestamp_fails_closed(
    connection: sqlite3.Connection,
    document_repository: SQLiteIdentityDocumentRepository,
    verification_repository: SQLiteIdentityVerificationRepository,
    repository: SQLiteIdentityVerificationEvidenceRepository,
) -> None:
    current_verification = persist_verification(
        document_repository,
        verification_repository,
    )
    current = reference(current_verification)

    repository.add_evidence_reference(current)

    connection.execute(
        """
        UPDATE novaid_identity_verification_evidence_refs
        SET collected_at = ?
        WHERE tenant_id = ?
          AND verification_id = ?
          AND evidence_type = ?
        """,
        (
            "not-a-date",
            current.tenant_id,
            current.verification_id,
            current.evidence_type.value,
        ),
    )
    connection.commit()

    with pytest.raises(
        DocumentPersistenceIntegrityError,
        match=(
            "STORED_EVIDENCE_REFERENCE_TIMESTAMP_INVALID"
        ),
    ):
        repository.get_evidence_reference(
            tenant_id=current.tenant_id,
            verification_id=current.verification_id,
            evidence_type=current.evidence_type,
        )


def test_invalid_stored_version_fails_closed(
    connection: sqlite3.Connection,
    document_repository: SQLiteIdentityDocumentRepository,
    verification_repository: SQLiteIdentityVerificationRepository,
    repository: SQLiteIdentityVerificationEvidenceRepository,
) -> None:
    current_verification = persist_verification(
        document_repository,
        verification_repository,
    )
    current = reference(current_verification)

    repository.add_evidence_reference(current)

    connection.execute(
        "PRAGMA ignore_check_constraints = ON"
    )
    connection.execute(
        """
        UPDATE novaid_identity_verification_evidence_refs
        SET evidence_version = 0
        WHERE tenant_id = ?
          AND verification_id = ?
          AND evidence_type = ?
        """,
        (
            current.tenant_id,
            current.verification_id,
            current.evidence_type.value,
        ),
    )
    connection.commit()
    connection.execute(
        "PRAGMA ignore_check_constraints = OFF"
    )

    with pytest.raises(
        DocumentPersistenceIntegrityError,
        match=(
            "STORED_EVIDENCE_REFERENCE_VERSION_INVALID"
        ),
    ):
        repository.get_evidence_reference(
            tenant_id=current.tenant_id,
            verification_id=current.verification_id,
            evidence_type=current.evidence_type,
        )


@pytest.mark.parametrize(
    ("method_name", "arguments", "error_code"),
    (
        (
            "get_evidence_reference",
            {
                "tenant_id": "",
                "verification_id": "verification-1",
                "evidence_type": (
                    IdentityVerificationEvidenceType
                    .OCR_EXTRACTION
                ),
            },
            "TENANT_ID_REQUIRED",
        ),
        (
            "get_evidence_reference",
            {
                "tenant_id": "tenant-1",
                "verification_id": "",
                "evidence_type": (
                    IdentityVerificationEvidenceType
                    .OCR_EXTRACTION
                ),
            },
            "IDENTITY_VERIFICATION_ID_REQUIRED",
        ),
        (
            "list_verification_evidence",
            {
                "tenant_id": "tenant-1",
                "verification_id": "",
            },
            "IDENTITY_VERIFICATION_ID_REQUIRED",
        ),
    ),
)
def test_blank_identifiers_are_rejected(
    repository: SQLiteIdentityVerificationEvidenceRepository,
    method_name: str,
    arguments: dict[str, object],
    error_code: str,
) -> None:
    method = getattr(repository, method_name)

    with pytest.raises(
        ValueError,
        match=error_code,
    ):
        method(**arguments)


def test_invalid_evidence_type_is_rejected(
    repository: SQLiteIdentityVerificationEvidenceRepository,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "INVALID_IDENTITY_VERIFICATION_EVIDENCE_TYPE"
        ),
    ):
        repository.get_evidence_reference(
            tenant_id=uid(),
            verification_id=uid(),
            evidence_type="OCR_EXTRACTION",  # type: ignore[arg-type]
        )


def test_wrong_reference_type_is_rejected(
    repository: SQLiteIdentityVerificationEvidenceRepository,
) -> None:
    with pytest.raises(
        TypeError,
        match=(
            "IDENTITY_VERIFICATION_EVIDENCE_REFERENCE_REQUIRED"
        ),
    ):
        repository.add_evidence_reference(
            object()  # type: ignore[arg-type]
        )


def test_repository_does_not_close_caller_connection(
    connection: sqlite3.Connection,
) -> None:
    repository = (
        SQLiteIdentityVerificationEvidenceRepository(
            connection
        )
    )

    del repository

    assert connection.execute(
        "SELECT 1"
    ).fetchone() == (1,)


def test_invalid_connection_is_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="SQLITE_CONNECTION_REQUIRED",
    ):
        SQLiteIdentityVerificationEvidenceRepository(
            object()  # type: ignore[arg-type]
        )
