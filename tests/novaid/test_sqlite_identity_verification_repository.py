from __future__ import annotations

import sqlite3
from dataclasses import replace
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
    IdentityVerificationRepository,
)
from afritech.novaid.persistence.identity_verification_codec import (
    encode_identity_verification_record_json,
)
from afritech.novaid.persistence.sqlite_document_repository import (
    SQLiteIdentityDocumentRepository,
)
from afritech.novaid.persistence.sqlite_identity_verification_repository import (
    SQLiteIdentityVerificationRepository,
)


def uid() -> str:
    return str(uuid4())


def timestamp(minute: int = 0) -> datetime:
    return datetime(
        2026,
        8,
        1,
        7,
        minute,
        0,
        tzinfo=timezone.utc,
    )


def document(
    *,
    tenant_id: str | None = None,
    identity_id: str | None = None,
    document_id: str | None = None,
    version: int = 1,
) -> IdentityDocument:
    return IdentityDocument(
        document_id=document_id or uid(),
        tenant_id=tenant_id or uid(),
        identity_id=identity_id or uid(),
        document_type=IdentityDocumentType.PASSPORT,
        issuing_country_code="AU",
        status=DocumentVerificationStatus.IN_PROGRESS,
        purpose=BiometricPurpose.EKYC,
        created_at=timestamp(),
        updated_at=timestamp(),
        version=version,
    )


def verification(
    bound_document: IdentityDocument,
    *,
    verification_id: str | None = None,
    workflow_id: str | None = None,
    minute: int = 1,
    **overrides: object,
) -> IdentityVerificationRecord:
    values: dict[str, object] = {
        "verification_id": verification_id or uid(),
        "workflow_id": workflow_id or uid(),
        "tenant_id": bound_document.tenant_id,
        "identity_id": bound_document.identity_id,
        "document_id": bound_document.document_id,
        "document_type": bound_document.document_type,
        "purpose": BiometricPurpose.EKYC,
        "decision": IdentityVerificationDecision.VERIFIED,
        "assurance_level": AssuranceLevel.NID_AL2,
        "combined_score": 0.965,
        "ocr_score": 0.97,
        "authenticity_score": 0.96,
        "selfie_match_score": 0.95,
        "liveness_score": 0.98,
        "ocr_extraction_id": uid(),
        "authenticity_assessment_id": uid(),
        "selfie_match_id": uid(),
        "policy_version": "identity-verification-policy-v1",
        "document_version": bound_document.version,
        "verified_at": timestamp(minute),
        "reason_codes": (
            "ALL_CONTROLS_SATISFIED",
        ),
        "metadata": {
            "channel": "MOBILE_APP",
        },
    }
    values.update(overrides)

    return IdentityVerificationRecord(**values)


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
    return SQLiteIdentityDocumentRepository(connection)


@pytest.fixture
def repository(
    connection: sqlite3.Connection,
) -> SQLiteIdentityVerificationRepository:
    return SQLiteIdentityVerificationRepository(connection)


def persist_document(
    document_repository: SQLiteIdentityDocumentRepository,
    current: IdentityDocument,
) -> None:
    document_repository.add_document(current)


def test_repository_satisfies_protocol(
    repository: SQLiteIdentityVerificationRepository,
) -> None:
    assert isinstance(
        repository,
        IdentityVerificationRepository,
    )


def test_add_and_get_verification_round_trip(
    document_repository: SQLiteIdentityDocumentRepository,
    repository: SQLiteIdentityVerificationRepository,
) -> None:
    current_document = document()
    persist_document(document_repository, current_document)

    current = verification(current_document)
    repository.add_verification(current)

    restored = repository.get_verification(
        tenant_id=current.tenant_id,
        verification_id=current.verification_id,
    )

    assert restored == current
    assert restored is not current


def test_missing_verification_returns_none(
    repository: SQLiteIdentityVerificationRepository,
) -> None:
    assert repository.get_verification(
        tenant_id=uid(),
        verification_id=uid(),
    ) is None


def test_cross_tenant_read_fails_closed(
    document_repository: SQLiteIdentityDocumentRepository,
    repository: SQLiteIdentityVerificationRepository,
) -> None:
    current_document = document()
    persist_document(document_repository, current_document)

    current = verification(current_document)
    repository.add_verification(current)

    assert repository.get_verification(
        tenant_id=uid(),
        verification_id=current.verification_id,
    ) is None


def test_duplicate_verification_is_rejected(
    document_repository: SQLiteIdentityDocumentRepository,
    repository: SQLiteIdentityVerificationRepository,
) -> None:
    current_document = document()
    persist_document(document_repository, current_document)

    current = verification(current_document)
    repository.add_verification(current)

    with pytest.raises(
        DocumentPersistenceConflictError,
        match="IDENTITY_VERIFICATION_ALREADY_EXISTS",
    ):
        repository.add_verification(current)


def test_missing_document_is_rejected(
    repository: SQLiteIdentityVerificationRepository,
) -> None:
    current = verification(document())

    with pytest.raises(
        DocumentPersistenceIntegrityError,
        match="IDENTITY_VERIFICATION_DOCUMENT_NOT_FOUND",
    ):
        repository.add_verification(current)


def test_identity_binding_mismatch_is_rejected(
    document_repository: SQLiteIdentityDocumentRepository,
    repository: SQLiteIdentityVerificationRepository,
) -> None:
    current_document = document()
    persist_document(document_repository, current_document)

    current = verification(
        current_document,
        identity_id=uid(),
    )

    with pytest.raises(
        DocumentPersistenceIntegrityError,
        match=(
            "IDENTITY_VERIFICATION_"
            "IDENTITY_BINDING_MISMATCH"
        ),
    ):
        repository.add_verification(current)


def test_document_type_binding_mismatch_is_rejected(
    document_repository: SQLiteIdentityDocumentRepository,
    repository: SQLiteIdentityVerificationRepository,
) -> None:
    current_document = document()
    persist_document(document_repository, current_document)

    alternative = next(
        item
        for item in IdentityDocumentType
        if item is not current_document.document_type
    )

    current = verification(
        current_document,
        document_type=alternative,
    )

    with pytest.raises(
        DocumentPersistenceIntegrityError,
        match=(
            "IDENTITY_VERIFICATION_"
            "DOCUMENT_TYPE_BINDING_MISMATCH"
        ),
    ):
        repository.add_verification(current)


def test_document_version_binding_mismatch_is_rejected(
    document_repository: SQLiteIdentityDocumentRepository,
    repository: SQLiteIdentityVerificationRepository,
) -> None:
    current_document = document(version=2)
    persist_document(document_repository, current_document)

    current = verification(
        current_document,
        document_version=1,
    )

    with pytest.raises(
        DocumentPersistenceIntegrityError,
        match=(
            "IDENTITY_VERIFICATION_"
            "DOCUMENT_VERSION_MISMATCH"
        ),
    ):
        repository.add_verification(current)


def test_verification_exists_is_tenant_scoped(
    document_repository: SQLiteIdentityDocumentRepository,
    repository: SQLiteIdentityVerificationRepository,
) -> None:
    current_document = document()
    persist_document(document_repository, current_document)

    current = verification(current_document)
    repository.add_verification(current)

    assert repository.verification_exists(
        tenant_id=current.tenant_id,
        verification_id=current.verification_id,
    )

    assert not repository.verification_exists(
        tenant_id=uid(),
        verification_id=current.verification_id,
    )


def test_document_history_is_deterministic(
    document_repository: SQLiteIdentityDocumentRepository,
    repository: SQLiteIdentityVerificationRepository,
) -> None:
    current_document = document()
    persist_document(document_repository, current_document)

    later = verification(
        current_document,
        minute=2,
    )
    earlier = verification(
        current_document,
        minute=1,
    )

    repository.add_verification(later)
    repository.add_verification(earlier)

    assert repository.list_document_verifications(
        tenant_id=current_document.tenant_id,
        document_id=current_document.document_id,
    ) == (
        earlier,
        later,
    )


def test_document_history_is_tenant_scoped(
    document_repository: SQLiteIdentityDocumentRepository,
    repository: SQLiteIdentityVerificationRepository,
) -> None:
    shared_document_id = uid()
    shared_identity_id = uid()

    first_document = document(
        tenant_id=uid(),
        identity_id=shared_identity_id,
        document_id=shared_document_id,
    )
    second_document = document(
        tenant_id=uid(),
        identity_id=shared_identity_id,
        document_id=shared_document_id,
    )

    persist_document(document_repository, first_document)
    persist_document(document_repository, second_document)

    first = verification(first_document)
    second = verification(second_document)

    repository.add_verification(first)
    repository.add_verification(second)

    assert repository.list_document_verifications(
        tenant_id=first_document.tenant_id,
        document_id=shared_document_id,
    ) == (first,)

    assert repository.list_document_verifications(
        tenant_id=second_document.tenant_id,
        document_id=shared_document_id,
    ) == (second,)


def test_missing_document_history_returns_empty_tuple(
    repository: SQLiteIdentityVerificationRepository,
) -> None:
    assert repository.list_document_verifications(
        tenant_id=uid(),
        document_id=uid(),
    ) == ()


def test_corrupt_payload_fails_closed(
    connection: sqlite3.Connection,
    document_repository: SQLiteIdentityDocumentRepository,
    repository: SQLiteIdentityVerificationRepository,
) -> None:
    current_document = document()
    persist_document(document_repository, current_document)

    current = verification(current_document)
    repository.add_verification(current)

    connection.execute(
        """
        UPDATE novaid_identity_verifications
        SET verification_payload_json = ?
        WHERE tenant_id = ?
          AND verification_id = ?
        """,
        (
            "{",
            current.tenant_id,
            current.verification_id,
        ),
    )
    connection.commit()

    with pytest.raises(
        DocumentPersistenceIntegrityError,
        match="STORED_VERIFICATION_PAYLOAD_INVALID",
    ):
        repository.get_verification(
            tenant_id=current.tenant_id,
            verification_id=current.verification_id,
        )


@pytest.mark.parametrize(
    ("field_name", "error_code"),
    (
        (
            "tenant_id",
            "STORED_VERIFICATION_TENANT_BINDING_MISMATCH",
        ),
        (
            "verification_id",
            "STORED_VERIFICATION_ID_BINDING_MISMATCH",
        ),
        (
            "identity_id",
            "STORED_VERIFICATION_IDENTITY_BINDING_MISMATCH",
        ),
        (
            "document_id",
            "STORED_VERIFICATION_DOCUMENT_BINDING_MISMATCH",
        ),
        (
            "workflow_id",
            "STORED_VERIFICATION_WORKFLOW_BINDING_MISMATCH",
        ),
    ),
)
def test_payload_binding_mismatch_fails_closed(
    field_name: str,
    error_code: str,
    connection: sqlite3.Connection,
    document_repository: SQLiteIdentityDocumentRepository,
    repository: SQLiteIdentityVerificationRepository,
) -> None:
    current_document = document()
    persist_document(document_repository, current_document)

    current = verification(current_document)
    repository.add_verification(current)

    altered = replace(
        current,
        **{field_name: uid()},
    )

    connection.execute(
        """
        UPDATE novaid_identity_verifications
        SET verification_payload_json = ?
        WHERE tenant_id = ?
          AND verification_id = ?
        """,
        (
            encode_identity_verification_record_json(
                altered
            ),
            current.tenant_id,
            current.verification_id,
        ),
    )
    connection.commit()

    with pytest.raises(
        DocumentPersistenceIntegrityError,
        match=error_code,
    ):
        repository.get_verification(
            tenant_id=current.tenant_id,
            verification_id=current.verification_id,
        )


@pytest.mark.parametrize(
    ("method_name", "arguments", "error_code"),
    (
        (
            "get_verification",
            {
                "tenant_id": "",
                "verification_id": "verification-1",
            },
            "TENANT_ID_REQUIRED",
        ),
        (
            "get_verification",
            {
                "tenant_id": "tenant-1",
                "verification_id": "",
            },
            "IDENTITY_VERIFICATION_ID_REQUIRED",
        ),
        (
            "list_document_verifications",
            {
                "tenant_id": "tenant-1",
                "document_id": "",
            },
            "DOCUMENT_ID_REQUIRED",
        ),
    ),
)
def test_blank_identifiers_are_rejected(
    repository: SQLiteIdentityVerificationRepository,
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


def test_wrong_record_type_is_rejected(
    repository: SQLiteIdentityVerificationRepository,
) -> None:
    with pytest.raises(
        TypeError,
        match="IDENTITY_VERIFICATION_RECORD_REQUIRED",
    ):
        repository.add_verification(
            object()  # type: ignore[arg-type]
        )


def test_repository_does_not_close_caller_connection(
    connection: sqlite3.Connection,
) -> None:
    repository = SQLiteIdentityVerificationRepository(
        connection
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
        SQLiteIdentityVerificationRepository(
            object()  # type: ignore[arg-type]
        )
