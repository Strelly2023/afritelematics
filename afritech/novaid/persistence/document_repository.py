from __future__ import annotations

from typing import Protocol, runtime_checkable

from afritech.novaid.domain.document_models import (
    IdentityDocument,
)
from afritech.novaid.domain.identity_verification_models import (
    IdentityVerificationRecord,
)


class DocumentPersistenceError(RuntimeError):
    """Base error for governed document persistence."""


class DocumentPersistenceConflictError(
    DocumentPersistenceError
):
    """Raised when optimistic concurrency validation fails."""


class DocumentPersistenceNotFoundError(
    DocumentPersistenceError
):
    """Raised when a tenant-scoped persistence record is absent."""


class DocumentPersistenceIntegrityError(
    DocumentPersistenceError
):
    """Raised when stored data violates the persistence contract."""


@runtime_checkable
class IdentityDocumentRepository(Protocol):
    def add_document(
        self,
        document: IdentityDocument,
    ) -> None:
        """Persist a new tenant-scoped identity document."""

    def get_document(
        self,
        *,
        tenant_id: str,
        document_id: str,
    ) -> IdentityDocument | None:
        """Return one document only within the supplied tenant."""

    def update_document(
        self,
        document: IdentityDocument,
        *,
        expected_version: int,
    ) -> None:
        """
        Replace a document using optimistic concurrency.

        The operation must fail when the stored version does not
        equal expected_version.
        """

    def delete_document(
        self,
        *,
        tenant_id: str,
        document_id: str,
        expected_version: int,
    ) -> None:
        """
        Delete one tenant-scoped document using optimistic
        concurrency.
        """

    def list_identity_documents(
        self,
        *,
        tenant_id: str,
        identity_id: str,
    ) -> tuple[IdentityDocument, ...]:
        """Return documents belonging to one tenant and identity."""


@runtime_checkable
class IdentityVerificationRepository(Protocol):
    def add_verification(
        self,
        verification: IdentityVerificationRecord,
    ) -> None:
        """Persist an immutable identity-verification record."""

    def get_verification(
        self,
        *,
        tenant_id: str,
        verification_id: str,
    ) -> IdentityVerificationRecord | None:
        """Return one verification only within the supplied tenant."""

    def list_document_verifications(
        self,
        *,
        tenant_id: str,
        document_id: str,
    ) -> tuple[IdentityVerificationRecord, ...]:
        """Return immutable verification history for one document."""

    def verification_exists(
        self,
        *,
        tenant_id: str,
        verification_id: str,
    ) -> bool:
        """Return whether a tenant-scoped verification exists."""


__all__ = [
    "DocumentPersistenceConflictError",
    "DocumentPersistenceError",
    "DocumentPersistenceIntegrityError",
    "DocumentPersistenceNotFoundError",
    "IdentityDocumentRepository",
    "IdentityVerificationRepository",
]
