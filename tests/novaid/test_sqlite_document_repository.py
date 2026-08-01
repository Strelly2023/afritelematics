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
from afritech.novaid.persistence.document_codec import (
    encode_identity_document_json,
)
from afritech.novaid.persistence.document_repository import (
    DocumentPersistenceConflictError,
    DocumentPersistenceIntegrityError,
    DocumentPersistenceNotFoundError,
    IdentityDocumentRepository,
)
from afritech.novaid.persistence.sqlite_document_repository import (
    SQLiteIdentityDocumentRepository,
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
        3,
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
    created_minute: int = 0,
) -> IdentityDocument:
    return IdentityDocument(
        document_id=document_id or uid(),
        tenant_id=tenant_id or uid(),
        identity_id=identity_id or uid(),
        document_type=IdentityDocumentType.PASSPORT,
        issuing_country_code="AU",
        status=DocumentVerificationStatus.PENDING,
        purpose=BiometricPurpose.EKYC,
        document_number_reference=(
            "secure://document-number/reference"
        ),
        created_at=timestamp(created_minute),
        updated_at=timestamp(created_minute),
        version=version,
        metadata={
            "channel": "MOBILE_APP",
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
def repository(
    connection: sqlite3.Connection,
) -> SQLiteIdentityDocumentRepository:
    return SQLiteIdentityDocumentRepository(
        connection
    )


def test_repository_satisfies_protocol(
    repository: SQLiteIdentityDocumentRepository,
) -> None:
    assert isinstance(
        repository,
        IdentityDocumentRepository,
    )


def test_add_and_get_document_round_trip(
    repository: SQLiteIdentityDocumentRepository,
) -> None:
    current = document()

    repository.add_document(current)

    restored = repository.get_document(
        tenant_id=current.tenant_id,
        document_id=current.document_id,
    )

    assert restored == current
    assert restored is not current


def test_missing_document_returns_none(
    repository: SQLiteIdentityDocumentRepository,
) -> None:
    assert repository.get_document(
        tenant_id=uid(),
        document_id=uid(),
    ) is None


def test_cross_tenant_read_fails_closed(
    repository: SQLiteIdentityDocumentRepository,
) -> None:
    current = document()

    repository.add_document(current)

    assert repository.get_document(
        tenant_id=uid(),
        document_id=current.document_id,
    ) is None


def test_duplicate_document_is_rejected(
    repository: SQLiteIdentityDocumentRepository,
) -> None:
    current = document()

    repository.add_document(current)

    with pytest.raises(
        DocumentPersistenceConflictError,
        match="IDENTITY_DOCUMENT_ALREADY_EXISTS",
    ):
        repository.add_document(current)


def test_same_document_id_is_allowed_in_another_tenant(
    repository: SQLiteIdentityDocumentRepository,
) -> None:
    document_id = uid()

    first = document(
        tenant_id=uid(),
        document_id=document_id,
    )
    second = document(
        tenant_id=uid(),
        document_id=document_id,
    )

    repository.add_document(first)
    repository.add_document(second)

    assert repository.get_document(
        tenant_id=first.tenant_id,
        document_id=document_id,
    ) == first

    assert repository.get_document(
        tenant_id=second.tenant_id,
        document_id=document_id,
    ) == second


def test_update_document_uses_optimistic_versioning(
    repository: SQLiteIdentityDocumentRepository,
) -> None:
    current = document()

    repository.add_document(current)

    updated = replace(
        current,
        status=DocumentVerificationStatus.IN_PROGRESS,
        updated_at=timestamp(1),
        version=2,
    )

    repository.update_document(
        updated,
        expected_version=1,
    )

    assert repository.get_document(
        tenant_id=current.tenant_id,
        document_id=current.document_id,
    ) == updated


def test_update_rejects_stale_expected_version(
    repository: SQLiteIdentityDocumentRepository,
) -> None:
    current = document()

    repository.add_document(current)

    updated = replace(
        current,
        updated_at=timestamp(1),
        version=3,
    )

    with pytest.raises(
        DocumentPersistenceConflictError,
        match="IDENTITY_DOCUMENT_VERSION_CONFLICT",
    ):
        repository.update_document(
            updated,
            expected_version=2,
        )


def test_update_requires_one_version_transition(
    repository: SQLiteIdentityDocumentRepository,
) -> None:
    current = document()

    repository.add_document(current)

    invalid = replace(
        current,
        updated_at=timestamp(2),
        version=3,
    )

    with pytest.raises(
        DocumentPersistenceConflictError,
        match="INVALID_DOCUMENT_VERSION_TRANSITION",
    ):
        repository.update_document(
            invalid,
            expected_version=1,
        )


def test_update_missing_document_is_not_found(
    repository: SQLiteIdentityDocumentRepository,
) -> None:
    missing = document(version=2)

    with pytest.raises(
        DocumentPersistenceNotFoundError,
        match="IDENTITY_DOCUMENT_NOT_FOUND",
    ):
        repository.update_document(
            missing,
            expected_version=1,
        )


def test_cross_tenant_update_does_not_mutate_document(
    repository: SQLiteIdentityDocumentRepository,
) -> None:
    current = document()

    repository.add_document(current)

    other_tenant_update = replace(
        current,
        tenant_id=uid(),
        updated_at=timestamp(1),
        version=2,
    )

    with pytest.raises(
        DocumentPersistenceNotFoundError,
        match="IDENTITY_DOCUMENT_NOT_FOUND",
    ):
        repository.update_document(
            other_tenant_update,
            expected_version=1,
        )

    assert repository.get_document(
        tenant_id=current.tenant_id,
        document_id=current.document_id,
    ) == current


def test_delete_document_uses_expected_version(
    repository: SQLiteIdentityDocumentRepository,
) -> None:
    current = document()

    repository.add_document(current)

    repository.delete_document(
        tenant_id=current.tenant_id,
        document_id=current.document_id,
        expected_version=1,
    )

    assert repository.get_document(
        tenant_id=current.tenant_id,
        document_id=current.document_id,
    ) is None


def test_delete_rejects_stale_version(
    repository: SQLiteIdentityDocumentRepository,
) -> None:
    current = document()

    repository.add_document(current)

    with pytest.raises(
        DocumentPersistenceConflictError,
        match="IDENTITY_DOCUMENT_VERSION_CONFLICT",
    ):
        repository.delete_document(
            tenant_id=current.tenant_id,
            document_id=current.document_id,
            expected_version=2,
        )


def test_delete_missing_document_is_not_found(
    repository: SQLiteIdentityDocumentRepository,
) -> None:
    with pytest.raises(
        DocumentPersistenceNotFoundError,
        match="IDENTITY_DOCUMENT_NOT_FOUND",
    ):
        repository.delete_document(
            tenant_id=uid(),
            document_id=uid(),
            expected_version=1,
        )


def test_cross_tenant_delete_fails_closed(
    repository: SQLiteIdentityDocumentRepository,
) -> None:
    current = document()

    repository.add_document(current)

    with pytest.raises(
        DocumentPersistenceNotFoundError,
        match="IDENTITY_DOCUMENT_NOT_FOUND",
    ):
        repository.delete_document(
            tenant_id=uid(),
            document_id=current.document_id,
            expected_version=1,
        )

    assert repository.get_document(
        tenant_id=current.tenant_id,
        document_id=current.document_id,
    ) == current


def test_list_identity_documents_is_tenant_scoped(
    repository: SQLiteIdentityDocumentRepository,
) -> None:
    tenant_id = uid()
    identity_id = uid()

    first = document(
        tenant_id=tenant_id,
        identity_id=identity_id,
        created_minute=0,
    )
    second = document(
        tenant_id=tenant_id,
        identity_id=identity_id,
        created_minute=1,
    )
    other_identity = document(
        tenant_id=tenant_id,
        identity_id=uid(),
        created_minute=2,
    )
    other_tenant = document(
        tenant_id=uid(),
        identity_id=identity_id,
        created_minute=3,
    )

    for current in (
        first,
        second,
        other_identity,
        other_tenant,
    ):
        repository.add_document(current)

    assert repository.list_identity_documents(
        tenant_id=tenant_id,
        identity_id=identity_id,
    ) == (
        first,
        second,
    )


def test_list_identity_documents_is_deterministic(
    repository: SQLiteIdentityDocumentRepository,
) -> None:
    tenant_id = uid()
    identity_id = uid()

    later = document(
        tenant_id=tenant_id,
        identity_id=identity_id,
        created_minute=2,
    )
    earlier = document(
        tenant_id=tenant_id,
        identity_id=identity_id,
        created_minute=1,
    )

    repository.add_document(later)
    repository.add_document(earlier)

    assert repository.list_identity_documents(
        tenant_id=tenant_id,
        identity_id=identity_id,
    ) == (
        earlier,
        later,
    )


def test_list_missing_identity_returns_empty_tuple(
    repository: SQLiteIdentityDocumentRepository,
) -> None:
    assert repository.list_identity_documents(
        tenant_id=uid(),
        identity_id=uid(),
    ) == ()


def test_corrupt_payload_fails_closed(
    repository: SQLiteIdentityDocumentRepository,
    connection: sqlite3.Connection,
) -> None:
    current = document()

    repository.add_document(current)

    connection.execute(
        """
        UPDATE novaid_identity_documents
        SET document_payload_json = ?
        WHERE tenant_id = ?
          AND document_id = ?
        """,
        (
            "{",
            current.tenant_id,
            current.document_id,
        ),
    )
    connection.commit()

    with pytest.raises(
        DocumentPersistenceIntegrityError,
        match="STORED_DOCUMENT_PAYLOAD_INVALID",
    ):
        repository.get_document(
            tenant_id=current.tenant_id,
            document_id=current.document_id,
        )


def test_payload_tenant_binding_mismatch_fails_closed(
    repository: SQLiteIdentityDocumentRepository,
    connection: sqlite3.Connection,
) -> None:
    current = document()
    repository.add_document(current)

    altered = replace(
        current,
        tenant_id=uid(),
    )

    connection.execute(
        """
        UPDATE novaid_identity_documents
        SET document_payload_json = ?
        WHERE tenant_id = ?
          AND document_id = ?
        """,
        (
            encode_identity_document_json(altered),
            current.tenant_id,
            current.document_id,
        ),
    )
    connection.commit()

    with pytest.raises(
        DocumentPersistenceIntegrityError,
        match=(
            "STORED_DOCUMENT_TENANT_BINDING_MISMATCH"
        ),
    ):
        repository.get_document(
            tenant_id=current.tenant_id,
            document_id=current.document_id,
        )


def test_payload_document_binding_mismatch_fails_closed(
    repository: SQLiteIdentityDocumentRepository,
    connection: sqlite3.Connection,
) -> None:
    current = document()
    repository.add_document(current)

    altered = replace(
        current,
        document_id=uid(),
    )

    connection.execute(
        """
        UPDATE novaid_identity_documents
        SET document_payload_json = ?
        WHERE tenant_id = ?
          AND document_id = ?
        """,
        (
            encode_identity_document_json(altered),
            current.tenant_id,
            current.document_id,
        ),
    )
    connection.commit()

    with pytest.raises(
        DocumentPersistenceIntegrityError,
        match="STORED_DOCUMENT_ID_BINDING_MISMATCH",
    ):
        repository.get_document(
            tenant_id=current.tenant_id,
            document_id=current.document_id,
        )


@pytest.mark.parametrize(
    ("method_name", "arguments", "error_code"),
    (
        (
            "get_document",
            {
                "tenant_id": "",
                "document_id": "document-1",
            },
            "TENANT_ID_REQUIRED",
        ),
        (
            "get_document",
            {
                "tenant_id": "tenant-1",
                "document_id": "",
            },
            "DOCUMENT_ID_REQUIRED",
        ),
        (
            "list_identity_documents",
            {
                "tenant_id": "tenant-1",
                "identity_id": "",
            },
            "IDENTITY_ID_REQUIRED",
        ),
    ),
)
def test_blank_identifiers_are_rejected(
    repository: SQLiteIdentityDocumentRepository,
    method_name: str,
    arguments: dict[str, object],
    error_code: str,
) -> None:
    method = getattr(
        repository,
        method_name,
    )

    with pytest.raises(
        ValueError,
        match=error_code,
    ):
        method(**arguments)


@pytest.mark.parametrize(
    "expected_version",
    (
        0,
        -1,
        True,
        1.5,
    ),
)
def test_invalid_expected_versions_are_rejected(
    repository: SQLiteIdentityDocumentRepository,
    expected_version: object,
) -> None:
    with pytest.raises(
        ValueError,
        match="INVALID_EXPECTED_DOCUMENT_VERSION",
    ):
        repository.delete_document(
            tenant_id=uid(),
            document_id=uid(),
            expected_version=expected_version,  # type: ignore[arg-type]
        )


def test_repository_does_not_close_caller_connection(
    connection: sqlite3.Connection,
) -> None:
    repository = SQLiteIdentityDocumentRepository(
        connection
    )

    current = document()
    repository.add_document(current)

    del repository

    assert connection.execute(
        "SELECT 1"
    ).fetchone() == (1,)


def test_invalid_connection_is_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="SQLITE_CONNECTION_REQUIRED",
    ):
        SQLiteIdentityDocumentRepository(
            object()  # type: ignore[arg-type]
        )
