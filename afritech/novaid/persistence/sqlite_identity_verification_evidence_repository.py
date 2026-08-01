from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from afritech.novaid.persistence.document_repository import (
    DocumentPersistenceConflictError,
    DocumentPersistenceIntegrityError,
)
from afritech.novaid.persistence.document_sqlite_schema import (
    initialize_document_sqlite_schema,
)
from afritech.novaid.persistence.identity_verification_evidence_repository import (
    IdentityVerificationEvidenceReference,
    IdentityVerificationEvidenceRepository,
    IdentityVerificationEvidenceType,
)


class SQLiteIdentityVerificationEvidenceRepository(
    IdentityVerificationEvidenceRepository
):
    """
    Append-only, tenant-scoped SQLite repository for governed
    identity-verification evidence references.

    The repository stores references and safe metadata only. It does
    not persist raw OCR, document, selfie, liveness, biometric, or
    provider material.

    The caller owns the supplied SQLite connection.
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

    def add_evidence_reference(
        self,
        reference: IdentityVerificationEvidenceReference,
    ) -> None:
        reference = self._require_reference(
            reference
        )

        self._assert_verification_exists(
            tenant_id=reference.tenant_id,
            verification_id=reference.verification_id,
        )

        metadata_json = self._encode_metadata(
            reference.metadata
        )

        values: dict[str, object] = {
            "tenant_id": reference.tenant_id,
            "verification_id": reference.verification_id,
            "evidence_type": reference.evidence_type.value,
            "evidence_id": reference.evidence_id,
            "evidence_version": reference.evidence_version,
            "collected_at": reference.collected_at.isoformat(),
            "metadata_json": metadata_json,
        }

        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO
                        novaid_identity_verification_evidence_refs (
                            tenant_id,
                            verification_id,
                            evidence_type,
                            evidence_id,
                            evidence_version,
                            collected_at,
                            metadata_json
                        )
                    VALUES (
                        :tenant_id,
                        :verification_id,
                        :evidence_type,
                        :evidence_id,
                        :evidence_version,
                        :collected_at,
                        :metadata_json
                    )
                    """,
                    values,
                )
        except sqlite3.IntegrityError as exc:
            if self.evidence_reference_exists(
                tenant_id=reference.tenant_id,
                verification_id=reference.verification_id,
                evidence_type=reference.evidence_type,
            ):
                raise DocumentPersistenceConflictError(
                    "IDENTITY_VERIFICATION_EVIDENCE_REFERENCE_ALREADY_EXISTS"
                ) from exc

            if self._evidence_id_exists(
                tenant_id=reference.tenant_id,
                evidence_type=reference.evidence_type,
                evidence_id=reference.evidence_id,
            ):
                raise DocumentPersistenceConflictError(
                    "IDENTITY_VERIFICATION_EVIDENCE_ID_ALREADY_REFERENCED"
                ) from exc

            raise DocumentPersistenceIntegrityError(
                "IDENTITY_VERIFICATION_EVIDENCE_REFERENCE_INSERT_FAILED"
            ) from exc
        except sqlite3.DatabaseError as exc:
            raise DocumentPersistenceIntegrityError(
                "IDENTITY_VERIFICATION_EVIDENCE_REFERENCE_INSERT_FAILED"
            ) from exc

    def get_evidence_reference(
        self,
        *,
        tenant_id: str,
        verification_id: str,
        evidence_type: IdentityVerificationEvidenceType,
    ) -> IdentityVerificationEvidenceReference | None:
        tenant_id = self._required_text(
            tenant_id,
            "TENANT_ID_REQUIRED",
        )
        verification_id = self._required_text(
            verification_id,
            "IDENTITY_VERIFICATION_ID_REQUIRED",
        )
        evidence_type = self._require_evidence_type(
            evidence_type
        )

        row = self._connection.execute(
            """
            SELECT
                tenant_id,
                verification_id,
                evidence_type,
                evidence_id,
                evidence_version,
                collected_at,
                metadata_json
            FROM novaid_identity_verification_evidence_refs
            WHERE tenant_id = ?
              AND verification_id = ?
              AND evidence_type = ?
            """,
            (
                tenant_id,
                verification_id,
                evidence_type.value,
            ),
        ).fetchone()

        if row is None:
            return None

        return self._decode_row(row)

    def list_verification_evidence(
        self,
        *,
        tenant_id: str,
        verification_id: str,
    ) -> tuple[
        IdentityVerificationEvidenceReference,
        ...,
    ]:
        tenant_id = self._required_text(
            tenant_id,
            "TENANT_ID_REQUIRED",
        )
        verification_id = self._required_text(
            verification_id,
            "IDENTITY_VERIFICATION_ID_REQUIRED",
        )

        rows = self._connection.execute(
            """
            SELECT
                tenant_id,
                verification_id,
                evidence_type,
                evidence_id,
                evidence_version,
                collected_at,
                metadata_json
            FROM novaid_identity_verification_evidence_refs
            WHERE tenant_id = ?
              AND verification_id = ?
            ORDER BY
                evidence_type ASC,
                evidence_id ASC
            """,
            (
                tenant_id,
                verification_id,
            ),
        ).fetchall()

        return tuple(
            self._decode_row(row)
            for row in rows
        )

    def evidence_reference_exists(
        self,
        *,
        tenant_id: str,
        verification_id: str,
        evidence_type: IdentityVerificationEvidenceType,
    ) -> bool:
        tenant_id = self._required_text(
            tenant_id,
            "TENANT_ID_REQUIRED",
        )
        verification_id = self._required_text(
            verification_id,
            "IDENTITY_VERIFICATION_ID_REQUIRED",
        )
        evidence_type = self._require_evidence_type(
            evidence_type
        )

        row = self._connection.execute(
            """
            SELECT 1
            FROM novaid_identity_verification_evidence_refs
            WHERE tenant_id = ?
              AND verification_id = ?
              AND evidence_type = ?
            """,
            (
                tenant_id,
                verification_id,
                evidence_type.value,
            ),
        ).fetchone()

        return row is not None

    def _assert_verification_exists(
        self,
        *,
        tenant_id: str,
        verification_id: str,
    ) -> None:
        row = self._connection.execute(
            """
            SELECT 1
            FROM novaid_identity_verifications
            WHERE tenant_id = ?
              AND verification_id = ?
            """,
            (
                tenant_id,
                verification_id,
            ),
        ).fetchone()

        if row is None:
            raise DocumentPersistenceIntegrityError(
                "IDENTITY_VERIFICATION_NOT_FOUND_FOR_EVIDENCE_REFERENCE"
            )

    def _evidence_id_exists(
        self,
        *,
        tenant_id: str,
        evidence_type: IdentityVerificationEvidenceType,
        evidence_id: str,
    ) -> bool:
        row = self._connection.execute(
            """
            SELECT 1
            FROM novaid_identity_verification_evidence_refs
            WHERE tenant_id = ?
              AND evidence_type = ?
              AND evidence_id = ?
            """,
            (
                tenant_id,
                evidence_type.value,
                evidence_id,
            ),
        ).fetchone()

        return row is not None

    @classmethod
    def _decode_row(
        cls,
        row: sqlite3.Row | tuple[object, ...],
    ) -> IdentityVerificationEvidenceReference:
        try:
            tenant_id = cls._stored_text(
                row[0],
                "STORED_EVIDENCE_REFERENCE_TENANT_INVALID",
            )
            verification_id = cls._stored_text(
                row[1],
                "STORED_EVIDENCE_REFERENCE_VERIFICATION_ID_INVALID",
            )
            evidence_type = cls._decode_evidence_type(
                row[2]
            )
            evidence_id = cls._stored_text(
                row[3],
                "STORED_EVIDENCE_REFERENCE_ID_INVALID",
            )
            evidence_version = cls._decode_version(
                row[4]
            )
            collected_at = cls._decode_datetime(
                row[5]
            )
            metadata = cls._decode_metadata(
                row[6]
            )

            return IdentityVerificationEvidenceReference(
                tenant_id=tenant_id,
                verification_id=verification_id,
                evidence_type=evidence_type,
                evidence_id=evidence_id,
                evidence_version=evidence_version,
                collected_at=collected_at,
                metadata=metadata,
            )
        except DocumentPersistenceIntegrityError:
            raise
        except (TypeError, ValueError) as exc:
            raise DocumentPersistenceIntegrityError(
                "STORED_EVIDENCE_REFERENCE_INVALID"
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
                "EVIDENCE_REFERENCE_METADATA_ENCODING_FAILED"
            ) from exc

    @staticmethod
    def _decode_metadata(
        payload: object,
    ) -> dict[str, Any]:
        if not isinstance(payload, str):
            raise DocumentPersistenceIntegrityError(
                "STORED_EVIDENCE_REFERENCE_METADATA_INVALID"
            )

        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise DocumentPersistenceIntegrityError(
                "STORED_EVIDENCE_REFERENCE_METADATA_INVALID"
            ) from exc

        if not isinstance(decoded, dict):
            raise DocumentPersistenceIntegrityError(
                "STORED_EVIDENCE_REFERENCE_METADATA_INVALID"
            )

        return decoded

    @staticmethod
    def _decode_datetime(
        value: object,
    ) -> datetime:
        if not isinstance(value, str):
            raise DocumentPersistenceIntegrityError(
                "STORED_EVIDENCE_REFERENCE_TIMESTAMP_INVALID"
            )

        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as exc:
            raise DocumentPersistenceIntegrityError(
                "STORED_EVIDENCE_REFERENCE_TIMESTAMP_INVALID"
            ) from exc

        if parsed.tzinfo is None:
            raise DocumentPersistenceIntegrityError(
                "STORED_EVIDENCE_REFERENCE_TIMESTAMP_INVALID"
            )

        return parsed

    @staticmethod
    def _decode_version(
        value: object,
    ) -> int:
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 1
        ):
            raise DocumentPersistenceIntegrityError(
                "STORED_EVIDENCE_REFERENCE_VERSION_INVALID"
            )

        return value

    @staticmethod
    def _decode_evidence_type(
        value: object,
    ) -> IdentityVerificationEvidenceType:
        if not isinstance(value, str):
            raise DocumentPersistenceIntegrityError(
                "STORED_EVIDENCE_REFERENCE_TYPE_INVALID"
            )

        try:
            return IdentityVerificationEvidenceType(
                value
            )
        except ValueError as exc:
            raise DocumentPersistenceIntegrityError(
                "STORED_EVIDENCE_REFERENCE_TYPE_INVALID"
            ) from exc

    @staticmethod
    def _stored_text(
        value: object,
        error_code: str,
    ) -> str:
        if not isinstance(value, str):
            raise DocumentPersistenceIntegrityError(
                error_code
            )

        normalized = value.strip()

        if not normalized:
            raise DocumentPersistenceIntegrityError(
                error_code
            )

        return normalized

    @staticmethod
    def _require_reference(
        reference: IdentityVerificationEvidenceReference,
    ) -> IdentityVerificationEvidenceReference:
        if not isinstance(
            reference,
            IdentityVerificationEvidenceReference,
        ):
            raise TypeError(
                "IDENTITY_VERIFICATION_EVIDENCE_REFERENCE_REQUIRED"
            )

        return reference

    @staticmethod
    def _require_evidence_type(
        evidence_type: IdentityVerificationEvidenceType,
    ) -> IdentityVerificationEvidenceType:
        if not isinstance(
            evidence_type,
            IdentityVerificationEvidenceType,
        ):
            raise ValueError(
                "INVALID_IDENTITY_VERIFICATION_EVIDENCE_TYPE"
            )

        return evidence_type

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


__all__ = [
    "SQLiteIdentityVerificationEvidenceRepository",
]
