from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from typing import Any

from afritech.novaid.domain.document_models import (
    IdentityDocument,
)
from afritech.novaid.persistence.document_codec import (
    DocumentPersistenceCodecError,
    decode_identity_document_json,
    encode_identity_document_json,
)
from afritech.novaid.persistence.document_repository import (
    DocumentPersistenceConflictError,
    DocumentPersistenceIntegrityError,
    DocumentPersistenceNotFoundError,
    IdentityDocumentRepository,
)
from afritech.novaid.persistence.document_sqlite_schema import (
    initialize_document_sqlite_schema,
)


class SQLiteIdentityDocumentRepository(
    IdentityDocumentRepository
):
    """
    Tenant-scoped SQLite persistence for IdentityDocument aggregates.

    The caller owns the supplied SQLite connection. This repository
    does not close it.
    """

    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        initialize_schema: bool = True,
    ) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise TypeError(
                "SQLITE_CONNECTION_REQUIRED"
            )

        self._connection = connection
        self._connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        if initialize_schema:
            initialize_document_sqlite_schema(
                self._connection
            )

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    def add_document(
        self,
        document: IdentityDocument,
    ) -> None:
        document = self._require_document(document)
        payload_json = self._encode_document(document)
        metadata_json = self._encode_metadata(
            document.metadata
        )

        values = self._document_values(
            document=document,
            payload_json=payload_json,
            metadata_json=metadata_json,
        )

        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO novaid_identity_documents (
                        tenant_id,
                        document_id,
                        identity_id,
                        document_type,
                        issuing_country,
                        verification_status,
                        document_number_reference,
                        issued_at,
                        expires_at,
                        verified_at,
                        created_at,
                        updated_at,
                        version,
                        document_payload_json,
                        metadata_json
                    )
                    VALUES (
                        :tenant_id,
                        :document_id,
                        :identity_id,
                        :document_type,
                        :issuing_country,
                        :verification_status,
                        :document_number_reference,
                        :issued_at,
                        :expires_at,
                        :verified_at,
                        :created_at,
                        :updated_at,
                        :version,
                        :document_payload_json,
                        :metadata_json
                    )
                    """,
                    values,
                )
        except sqlite3.IntegrityError as exc:
            if self._document_exists(
                tenant_id=document.tenant_id,
                document_id=document.document_id,
            ):
                raise DocumentPersistenceConflictError(
                    "IDENTITY_DOCUMENT_ALREADY_EXISTS"
                ) from exc

            raise DocumentPersistenceIntegrityError(
                "IDENTITY_DOCUMENT_INSERT_FAILED"
            ) from exc
        except sqlite3.DatabaseError as exc:
            raise DocumentPersistenceIntegrityError(
                "IDENTITY_DOCUMENT_INSERT_FAILED"
            ) from exc

    def get_document(
        self,
        *,
        tenant_id: str,
        document_id: str,
    ) -> IdentityDocument | None:
        tenant_id = self._required_text(
            tenant_id,
            "TENANT_ID_REQUIRED",
        )
        document_id = self._required_text(
            document_id,
            "DOCUMENT_ID_REQUIRED",
        )

        row = self._connection.execute(
            """
            SELECT
                tenant_id,
                document_id,
                document_payload_json
            FROM novaid_identity_documents
            WHERE tenant_id = ?
              AND document_id = ?
            """,
            (
                tenant_id,
                document_id,
            ),
        ).fetchone()

        if row is None:
            return None

        stored_tenant_id = str(row[0])
        stored_document_id = str(row[1])
        payload_json = row[2]

        document = self._decode_document(
            payload_json
        )

        self._assert_row_binding(
            document=document,
            tenant_id=stored_tenant_id,
            document_id=stored_document_id,
        )

        return document

    def update_document(
        self,
        document: IdentityDocument,
        *,
        expected_version: int,
    ) -> None:
        document = self._require_document(document)
        expected_version = self._require_version(
            expected_version,
            error_code=(
                "INVALID_EXPECTED_DOCUMENT_VERSION"
            ),
        )

        if document.version != expected_version + 1:
            raise DocumentPersistenceConflictError(
                "INVALID_DOCUMENT_VERSION_TRANSITION"
            )

        payload_json = self._encode_document(document)
        metadata_json = self._encode_metadata(
            document.metadata
        )

        values = self._document_values(
            document=document,
            payload_json=payload_json,
            metadata_json=metadata_json,
        )
        values["expected_version"] = expected_version

        try:
            with self._connection:
                cursor = self._connection.execute(
                    """
                    UPDATE novaid_identity_documents
                    SET
                        identity_id = :identity_id,
                        document_type = :document_type,
                        issuing_country = :issuing_country,
                        verification_status = (
                            :verification_status
                        ),
                        document_number_reference = (
                            :document_number_reference
                        ),
                        issued_at = :issued_at,
                        expires_at = :expires_at,
                        verified_at = :verified_at,
                        created_at = :created_at,
                        updated_at = :updated_at,
                        version = :version,
                        document_payload_json = (
                            :document_payload_json
                        ),
                        metadata_json = :metadata_json
                    WHERE tenant_id = :tenant_id
                      AND document_id = :document_id
                      AND version = :expected_version
                    """,
                    values,
                )

                if cursor.rowcount != 1:
                    self._raise_update_miss(
                        tenant_id=document.tenant_id,
                        document_id=document.document_id,
                        expected_version=expected_version,
                    )
        except (
            DocumentPersistenceConflictError,
            DocumentPersistenceNotFoundError,
        ):
            raise
        except sqlite3.IntegrityError as exc:
            raise DocumentPersistenceIntegrityError(
                "IDENTITY_DOCUMENT_UPDATE_FAILED"
            ) from exc
        except sqlite3.DatabaseError as exc:
            raise DocumentPersistenceIntegrityError(
                "IDENTITY_DOCUMENT_UPDATE_FAILED"
            ) from exc

    def delete_document(
        self,
        *,
        tenant_id: str,
        document_id: str,
        expected_version: int,
    ) -> None:
        tenant_id = self._required_text(
            tenant_id,
            "TENANT_ID_REQUIRED",
        )
        document_id = self._required_text(
            document_id,
            "DOCUMENT_ID_REQUIRED",
        )
        expected_version = self._require_version(
            expected_version,
            error_code=(
                "INVALID_EXPECTED_DOCUMENT_VERSION"
            ),
        )

        try:
            with self._connection:
                cursor = self._connection.execute(
                    """
                    DELETE FROM novaid_identity_documents
                    WHERE tenant_id = ?
                      AND document_id = ?
                      AND version = ?
                    """,
                    (
                        tenant_id,
                        document_id,
                        expected_version,
                    ),
                )

                if cursor.rowcount != 1:
                    self._raise_update_miss(
                        tenant_id=tenant_id,
                        document_id=document_id,
                        expected_version=expected_version,
                    )
        except (
            DocumentPersistenceConflictError,
            DocumentPersistenceNotFoundError,
        ):
            raise
        except sqlite3.IntegrityError as exc:
            raise DocumentPersistenceIntegrityError(
                "IDENTITY_DOCUMENT_DELETE_FAILED"
            ) from exc
        except sqlite3.DatabaseError as exc:
            raise DocumentPersistenceIntegrityError(
                "IDENTITY_DOCUMENT_DELETE_FAILED"
            ) from exc

    def list_identity_documents(
        self,
        *,
        tenant_id: str,
        identity_id: str,
    ) -> tuple[IdentityDocument, ...]:
        tenant_id = self._required_text(
            tenant_id,
            "TENANT_ID_REQUIRED",
        )
        identity_id = self._required_text(
            identity_id,
            "IDENTITY_ID_REQUIRED",
        )

        rows = self._connection.execute(
            """
            SELECT
                tenant_id,
                document_id,
                identity_id,
                document_payload_json
            FROM novaid_identity_documents
            WHERE tenant_id = ?
              AND identity_id = ?
            ORDER BY
                created_at ASC,
                document_id ASC
            """,
            (
                tenant_id,
                identity_id,
            ),
        ).fetchall()

        documents: list[IdentityDocument] = []

        for row in rows:
            stored_tenant_id = str(row[0])
            stored_document_id = str(row[1])
            stored_identity_id = str(row[2])
            payload_json = row[3]

            document = self._decode_document(
                payload_json
            )

            self._assert_row_binding(
                document=document,
                tenant_id=stored_tenant_id,
                document_id=stored_document_id,
                identity_id=stored_identity_id,
            )

            documents.append(document)

        return tuple(documents)

    def _document_exists(
        self,
        *,
        tenant_id: str,
        document_id: str,
    ) -> bool:
        row = self._connection.execute(
            """
            SELECT 1
            FROM novaid_identity_documents
            WHERE tenant_id = ?
              AND document_id = ?
            """,
            (
                tenant_id,
                document_id,
            ),
        ).fetchone()

        return row is not None

    def _stored_version(
        self,
        *,
        tenant_id: str,
        document_id: str,
    ) -> int | None:
        row = self._connection.execute(
            """
            SELECT version
            FROM novaid_identity_documents
            WHERE tenant_id = ?
              AND document_id = ?
            """,
            (
                tenant_id,
                document_id,
            ),
        ).fetchone()

        if row is None:
            return None

        version = row[0]

        if (
            isinstance(version, bool)
            or not isinstance(version, int)
            or version < 1
        ):
            raise DocumentPersistenceIntegrityError(
                "STORED_DOCUMENT_VERSION_INVALID"
            )

        return version

    def _raise_update_miss(
        self,
        *,
        tenant_id: str,
        document_id: str,
        expected_version: int,
    ) -> None:
        stored_version = self._stored_version(
            tenant_id=tenant_id,
            document_id=document_id,
        )

        if stored_version is None:
            raise DocumentPersistenceNotFoundError(
                "IDENTITY_DOCUMENT_NOT_FOUND"
            )

        raise DocumentPersistenceConflictError(
            "IDENTITY_DOCUMENT_VERSION_CONFLICT:"
            f"expected={expected_version},"
            f"actual={stored_version}"
        )

    @staticmethod
    def _document_values(
        *,
        document: IdentityDocument,
        payload_json: str,
        metadata_json: str,
    ) -> dict[str, object]:
        return {
            "tenant_id": document.tenant_id,
            "document_id": document.document_id,
            "identity_id": document.identity_id,
            "document_type": document.document_type.value,
            "issuing_country": (
                document.issuing_country_code
            ),
            "verification_status": (
                document.status.value
            ),
            "document_number_reference": (
                document.document_number_reference
            ),
            "issued_at": (
                document.issued_at.isoformat()
                if document.issued_at is not None
                else None
            ),
            "expires_at": (
                document.expires_at.isoformat()
                if document.expires_at is not None
                else None
            ),
            "verified_at": (
                document.verified_at.isoformat()
                if document.verified_at is not None
                else None
            ),
            "created_at": document.created_at.isoformat(),
            "updated_at": document.updated_at.isoformat(),
            "version": document.version,
            "document_payload_json": payload_json,
            "metadata_json": metadata_json,
        }

    @staticmethod
    def _encode_document(
        document: IdentityDocument,
    ) -> str:
        try:
            return encode_identity_document_json(
                document
            )
        except DocumentPersistenceCodecError as exc:
            raise DocumentPersistenceIntegrityError(
                "IDENTITY_DOCUMENT_ENCODING_FAILED"
            ) from exc

    @staticmethod
    def _decode_document(
        payload_json: object,
    ) -> IdentityDocument:
        if not isinstance(payload_json, str):
            raise DocumentPersistenceIntegrityError(
                "STORED_DOCUMENT_PAYLOAD_INVALID"
            )

        try:
            return decode_identity_document_json(
                payload_json
            )
        except DocumentPersistenceCodecError as exc:
            raise DocumentPersistenceIntegrityError(
                "STORED_DOCUMENT_PAYLOAD_INVALID"
            ) from exc

    @staticmethod
    def _encode_metadata(
        metadata: Mapping[str, Any],
    ) -> str:
        try:
            return json.dumps(
                dict(metadata),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            )
        except (TypeError, ValueError) as exc:
            raise DocumentPersistenceIntegrityError(
                "IDENTITY_DOCUMENT_METADATA_ENCODING_FAILED"
            ) from exc

    @staticmethod
    def _assert_row_binding(
        *,
        document: IdentityDocument,
        tenant_id: str,
        document_id: str,
        identity_id: str | None = None,
    ) -> None:
        if document.tenant_id != tenant_id:
            raise DocumentPersistenceIntegrityError(
                "STORED_DOCUMENT_TENANT_BINDING_MISMATCH"
            )

        if document.document_id != document_id:
            raise DocumentPersistenceIntegrityError(
                "STORED_DOCUMENT_ID_BINDING_MISMATCH"
            )

        if (
            identity_id is not None
            and document.identity_id != identity_id
        ):
            raise DocumentPersistenceIntegrityError(
                "STORED_DOCUMENT_IDENTITY_BINDING_MISMATCH"
            )

    @staticmethod
    def _require_document(
        document: IdentityDocument,
    ) -> IdentityDocument:
        if not isinstance(document, IdentityDocument):
            raise TypeError(
                "IDENTITY_DOCUMENT_REQUIRED"
            )

        return document

    @staticmethod
    def _required_text(
        value: str,
        error_code: str,
    ) -> str:
        if not isinstance(value, str):
            raise ValueError(error_code)

        normalized = value.strip()

        if not normalized:
            raise ValueError(error_code)

        return normalized

    @staticmethod
    def _require_version(
        value: int,
        *,
        error_code: str,
    ) -> int:
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 1
        ):
            raise ValueError(error_code)

        return value


__all__ = [
    "SQLiteIdentityDocumentRepository",
]
