from __future__ import annotations

from typing import get_type_hints

from afritech.novaid.persistence.document_repository import (
    DocumentPersistenceConflictError,
    DocumentPersistenceError,
    DocumentPersistenceIntegrityError,
    DocumentPersistenceNotFoundError,
    IdentityDocumentRepository,
    IdentityVerificationRepository,
)


class StructurallyValidDocumentRepository:
    def add_document(self, document) -> None:
        return None

    def get_document(
        self,
        *,
        tenant_id: str,
        document_id: str,
    ):
        return None

    def update_document(
        self,
        document,
        *,
        expected_version: int,
    ) -> None:
        return None

    def delete_document(
        self,
        *,
        tenant_id: str,
        document_id: str,
        expected_version: int,
    ) -> None:
        return None

    def list_identity_documents(
        self,
        *,
        tenant_id: str,
        identity_id: str,
    ) -> tuple:
        return ()


class StructurallyValidVerificationRepository:
    def add_verification(self, verification) -> None:
        return None

    def get_verification(
        self,
        *,
        tenant_id: str,
        verification_id: str,
    ):
        return None

    def list_document_verifications(
        self,
        *,
        tenant_id: str,
        document_id: str,
    ) -> tuple:
        return ()

    def verification_exists(
        self,
        *,
        tenant_id: str,
        verification_id: str,
    ) -> bool:
        return False


class InvalidDocumentRepository:
    pass


def test_document_repository_is_runtime_checkable() -> None:
    repository = StructurallyValidDocumentRepository()

    assert isinstance(
        repository,
        IdentityDocumentRepository,
    )


def test_verification_repository_is_runtime_checkable() -> None:
    repository = StructurallyValidVerificationRepository()

    assert isinstance(
        repository,
        IdentityVerificationRepository,
    )


def test_invalid_repository_does_not_satisfy_contract() -> None:
    assert not isinstance(
        InvalidDocumentRepository(),
        IdentityDocumentRepository,
    )


def test_document_repository_requires_optimistic_versioning() -> None:
    update_hints = get_type_hints(
        IdentityDocumentRepository.update_document
    )
    delete_hints = get_type_hints(
        IdentityDocumentRepository.delete_document
    )

    assert update_hints["expected_version"] is int
    assert delete_hints["expected_version"] is int


def test_repository_contract_is_tenant_scoped() -> None:
    document_hints = get_type_hints(
        IdentityDocumentRepository.get_document
    )
    verification_hints = get_type_hints(
        IdentityVerificationRepository.get_verification
    )

    assert document_hints["tenant_id"] is str
    assert verification_hints["tenant_id"] is str


def test_persistence_errors_share_canonical_base() -> None:
    assert issubclass(
        DocumentPersistenceConflictError,
        DocumentPersistenceError,
    )
    assert issubclass(
        DocumentPersistenceNotFoundError,
        DocumentPersistenceError,
    )
    assert issubclass(
        DocumentPersistenceIntegrityError,
        DocumentPersistenceError,
    )


def test_document_contract_exposes_required_operations() -> None:
    expected = {
        "add_document",
        "get_document",
        "update_document",
        "delete_document",
        "list_identity_documents",
    }

    assert expected.issubset(
        set(IdentityDocumentRepository.__dict__)
    )


def test_verification_contract_exposes_required_operations() -> None:
    expected = {
        "add_verification",
        "get_verification",
        "list_document_verifications",
        "verification_exists",
    }

    assert expected.issubset(
        set(IdentityVerificationRepository.__dict__)
    )
