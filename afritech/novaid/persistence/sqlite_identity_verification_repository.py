from __future__ import annotations

import json
import sqlite3
from typing import Any

from afritech.novaid.domain.identity_verification_models import (
    IdentityVerificationRecord,
)
from afritech.novaid.persistence.document_repository import (
    DocumentPersistenceConflictError,
    DocumentPersistenceIntegrityError,
    IdentityVerificationRepository,
)
from afritech.novaid.persistence.document_sqlite_schema import (
    initialize_document_sqlite_schema,
)
from afritech.novaid.persistence.identity_verification_codec import (
    VerificationPersistenceCodecError,
    decode_identity_verification_record_json,
    encode_identity_verification_record_json,
)


class SQLiteIdentityVerificationRepository(
    IdentityVerificationRepository
):
    """
    Append-only, tenant-scoped SQLite repository for immutable
    IdentityVerificationRecord objects.

    The caller retains ownership of the supplied SQLite connection.
    """

    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        initialize_schema: bool = True,
    ) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise TypeError("SQLITE_CONNECTION_REQUIRED")

        self._connection = connection
        self._connection.execute("PRAGMA foreign_keys = ON")

        if initialize_schema:
            initialize_document_sqlite_schema(
                self._connection
            )

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    def add_verification(
        self,
        verification: IdentityVerificationRecord,
    ) -> None:
        verification = self._require_verification(
            verification
        )

        self._assert_document_binding(verification)

        payload_json = self._encode_verification(
            verification
        )
        reason_codes_json = self._encode_json(
            list(verification.reason_codes),
            "IDENTITY_VERIFICATION_REASON_CODES_ENCODING_FAILED",
        )
        metadata_json = self._encode_json(
            dict(verification.metadata),
            "IDENTITY_VERIFICATION_METADATA_ENCODING_FAILED",
        )

        values: dict[str, object] = {
            "tenant_id": verification.tenant_id,
            "verification_id": verification.verification_id,
            "identity_id": verification.identity_id,
            "document_id": verification.document_id,
            "workflow_id": verification.workflow_id,
            "document_type": verification.document_type.value,
            "purpose": verification.purpose.value,
            "decision": verification.decision.value,
            "assurance_level": (
                verification.assurance_level.value
            ),
            "combined_score": verification.combined_score,
            "policy_version": verification.policy_version,
            "document_version": verification.document_version,
            "verified_at": verification.verified_at.isoformat(),
            "reason_codes_json": reason_codes_json,
            "verification_payload_json": payload_json,
            "metadata_json": metadata_json,
        }

        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO novaid_identity_verifications (
                        tenant_id,
                        verification_id,
                        identity_id,
                        document_id,
                        workflow_id,
                        correlation_id,
                        request_id,
                        actor_identity_id,
                        document_type,
                        purpose,
                        decision,
                        assurance_level,
                        combined_score,
                        policy_version,
                        document_version,
                        attempt_number,
                        verified_at,
                        expires_at,
                        reason_codes_json,
                        verification_payload_json,
                        metadata_json
                    )
                    VALUES (
                        :tenant_id,
                        :verification_id,
                        :identity_id,
                        :document_id,
                        :workflow_id,
                        NULL,
                        NULL,
                        NULL,
                        :document_type,
                        :purpose,
                        :decision,
                        :assurance_level,
                        :combined_score,
                        :policy_version,
                        :document_version,
                        1,
                        :verified_at,
                        NULL,
                        :reason_codes_json,
                        :verification_payload_json,
                        :metadata_json
                    )
                    """,
                    values,
                )
        except sqlite3.IntegrityError as exc:
            if self.verification_exists(
                tenant_id=verification.tenant_id,
                verification_id=verification.verification_id,
            ):
                raise DocumentPersistenceConflictError(
                    "IDENTITY_VERIFICATION_ALREADY_EXISTS"
                ) from exc

            raise DocumentPersistenceIntegrityError(
                "IDENTITY_VERIFICATION_INSERT_FAILED"
            ) from exc
        except sqlite3.DatabaseError as exc:
            raise DocumentPersistenceIntegrityError(
                "IDENTITY_VERIFICATION_INSERT_FAILED"
            ) from exc

    def get_verification(
        self,
        *,
        tenant_id: str,
        verification_id: str,
    ) -> IdentityVerificationRecord | None:
        tenant_id = self._required_text(
            tenant_id,
            "TENANT_ID_REQUIRED",
        )
        verification_id = self._required_text(
            verification_id,
            "IDENTITY_VERIFICATION_ID_REQUIRED",
        )

        row = self._connection.execute(
            """
            SELECT
                tenant_id,
                verification_id,
                identity_id,
                document_id,
                workflow_id,
                verification_payload_json
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
            return None

        verification = self._decode_verification(row[5])

        self._assert_row_binding(
            verification=verification,
            tenant_id=str(row[0]),
            verification_id=str(row[1]),
            identity_id=str(row[2]),
            document_id=str(row[3]),
            workflow_id=str(row[4]),
        )

        return verification

    def list_document_verifications(
        self,
        *,
        tenant_id: str,
        document_id: str,
    ) -> tuple[IdentityVerificationRecord, ...]:
        tenant_id = self._required_text(
            tenant_id,
            "TENANT_ID_REQUIRED",
        )
        document_id = self._required_text(
            document_id,
            "DOCUMENT_ID_REQUIRED",
        )

        rows = self._connection.execute(
            """
            SELECT
                tenant_id,
                verification_id,
                identity_id,
                document_id,
                workflow_id,
                verification_payload_json
            FROM novaid_identity_verifications
            WHERE tenant_id = ?
              AND document_id = ?
            ORDER BY
                verified_at ASC,
                verification_id ASC
            """,
            (
                tenant_id,
                document_id,
            ),
        ).fetchall()

        verifications: list[
            IdentityVerificationRecord
        ] = []

        for row in rows:
            verification = self._decode_verification(
                row[5]
            )

            self._assert_row_binding(
                verification=verification,
                tenant_id=str(row[0]),
                verification_id=str(row[1]),
                identity_id=str(row[2]),
                document_id=str(row[3]),
                workflow_id=str(row[4]),
            )

            verifications.append(verification)

        return tuple(verifications)

    def verification_exists(
        self,
        *,
        tenant_id: str,
        verification_id: str,
    ) -> bool:
        tenant_id = self._required_text(
            tenant_id,
            "TENANT_ID_REQUIRED",
        )
        verification_id = self._required_text(
            verification_id,
            "IDENTITY_VERIFICATION_ID_REQUIRED",
        )

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

        return row is not None

    def _assert_document_binding(
        self,
        verification: IdentityVerificationRecord,
    ) -> None:
        row = self._connection.execute(
            """
            SELECT
                identity_id,
                document_type,
                version
            FROM novaid_identity_documents
            WHERE tenant_id = ?
              AND document_id = ?
            """,
            (
                verification.tenant_id,
                verification.document_id,
            ),
        ).fetchone()

        if row is None:
            raise DocumentPersistenceIntegrityError(
                "IDENTITY_VERIFICATION_DOCUMENT_NOT_FOUND"
            )

        stored_identity_id = str(row[0])
        stored_document_type = str(row[1])
        stored_document_version = row[2]

        if stored_identity_id != verification.identity_id:
            raise DocumentPersistenceIntegrityError(
                "IDENTITY_VERIFICATION_IDENTITY_BINDING_MISMATCH"
            )

        if (
            stored_document_type
            != verification.document_type.value
        ):
            raise DocumentPersistenceIntegrityError(
                "IDENTITY_VERIFICATION_DOCUMENT_TYPE_BINDING_MISMATCH"
            )

        if (
            isinstance(stored_document_version, bool)
            or not isinstance(stored_document_version, int)
            or stored_document_version < 1
        ):
            raise DocumentPersistenceIntegrityError(
                "STORED_DOCUMENT_VERSION_INVALID"
            )

        if (
            verification.document_version
            != stored_document_version
        ):
            raise DocumentPersistenceIntegrityError(
                "IDENTITY_VERIFICATION_DOCUMENT_VERSION_MISMATCH"
            )

    @staticmethod
    def _assert_row_binding(
        *,
        verification: IdentityVerificationRecord,
        tenant_id: str,
        verification_id: str,
        identity_id: str,
        document_id: str,
        workflow_id: str,
    ) -> None:
        bindings = (
            (
                verification.tenant_id,
                tenant_id,
                "STORED_VERIFICATION_TENANT_BINDING_MISMATCH",
            ),
            (
                verification.verification_id,
                verification_id,
                "STORED_VERIFICATION_ID_BINDING_MISMATCH",
            ),
            (
                verification.identity_id,
                identity_id,
                "STORED_VERIFICATION_IDENTITY_BINDING_MISMATCH",
            ),
            (
                verification.document_id,
                document_id,
                "STORED_VERIFICATION_DOCUMENT_BINDING_MISMATCH",
            ),
            (
                verification.workflow_id,
                workflow_id,
                "STORED_VERIFICATION_WORKFLOW_BINDING_MISMATCH",
            ),
        )

        for actual, expected, error_code in bindings:
            if actual != expected:
                raise DocumentPersistenceIntegrityError(
                    error_code
                )

    @staticmethod
    def _encode_verification(
        verification: IdentityVerificationRecord,
    ) -> str:
        try:
            return encode_identity_verification_record_json(
                verification
            )
        except VerificationPersistenceCodecError as exc:
            raise DocumentPersistenceIntegrityError(
                "IDENTITY_VERIFICATION_ENCODING_FAILED"
            ) from exc

    @staticmethod
    def _decode_verification(
        payload_json: object,
    ) -> IdentityVerificationRecord:
        if not isinstance(payload_json, str):
            raise DocumentPersistenceIntegrityError(
                "STORED_VERIFICATION_PAYLOAD_INVALID"
            )

        try:
            return decode_identity_verification_record_json(
                payload_json
            )
        except VerificationPersistenceCodecError as exc:
            raise DocumentPersistenceIntegrityError(
                "STORED_VERIFICATION_PAYLOAD_INVALID"
            ) from exc

    @staticmethod
    def _encode_json(
        value: object,
        error_code: str,
    ) -> str:
        try:
            return json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            )
        except (TypeError, ValueError) as exc:
            raise DocumentPersistenceIntegrityError(
                error_code
            ) from exc

    @staticmethod
    def _require_verification(
        verification: IdentityVerificationRecord,
    ) -> IdentityVerificationRecord:
        if not isinstance(
            verification,
            IdentityVerificationRecord,
        ):
            raise TypeError(
                "IDENTITY_VERIFICATION_RECORD_REQUIRED"
            )

        return verification

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
    "SQLiteIdentityVerificationRepository",
]
