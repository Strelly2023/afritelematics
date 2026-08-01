from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from afritech.novaid.domain.identity_verification_models import (
    IdentityVerificationEvidence,
    IdentityVerificationRecord,
)
from afritech.novaid.persistence.document_repository import (
    DocumentPersistenceConflictError,
    DocumentPersistenceIntegrityError,
)
from afritech.novaid.persistence.document_sqlite_schema import (
    initialize_document_sqlite_schema,
)
from afritech.novaid.persistence.identity_verification_codec import (
    VerificationPersistenceCodecError,
    decode_identity_verification_record_json,
    encode_identity_verification_record_json,
)
from afritech.novaid.persistence.identity_verification_evidence_factory import (
    IdentityVerificationEvidenceFactoryError,
    build_identity_verification_evidence_references,
)
from afritech.novaid.persistence.identity_verification_evidence_repository import (
    IdentityVerificationEvidenceReference,
    IdentityVerificationEvidenceType,
)


@dataclass(frozen=True, slots=True)
class IdentityVerificationPersistenceBundle:
    verification: IdentityVerificationRecord
    evidence_references: tuple[
        IdentityVerificationEvidenceReference,
        ...,
    ]


class SQLiteIdentityVerificationPersistenceCoordinator:
    """
    Atomically persists and deterministically reloads a verification
    record with its four governed evidence references.

    Identical repeated requests are idempotent. Reuse of an existing
    verification identifier with changed content fails closed.

    The caller owns the supplied SQLite connection.
    """

    REQUIRED_EVIDENCE_TYPES = frozenset(
        IdentityVerificationEvidenceType
    )

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
            initialize_document_sqlite_schema(connection)

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    def persist(
        self,
        *,
        verification: IdentityVerificationRecord,
        evidence: IdentityVerificationEvidence,
        metadata: Mapping[str, Any] | None = None,
    ) -> IdentityVerificationPersistenceBundle:
        if self._connection.in_transaction:
            raise DocumentPersistenceIntegrityError(
                "ACTIVE_SQLITE_TRANSACTION_NOT_SUPPORTED"
            )

        try:
            references = (
                build_identity_verification_evidence_references(
                    verification=verification,
                    evidence=evidence,
                    metadata=metadata,
                )
            )
        except IdentityVerificationEvidenceFactoryError:
            raise
        except (TypeError, ValueError) as exc:
            raise DocumentPersistenceIntegrityError(
                "IDENTITY_VERIFICATION_EVIDENCE_BUILD_FAILED"
            ) from exc

        self._assert_complete_reference_set(references)
        self._assert_document_binding(verification)

        requested = IdentityVerificationPersistenceBundle(
            verification=verification,
            evidence_references=references,
        )

        existing = self.load_persisted_bundle(
            tenant_id=verification.tenant_id,
            verification_id=verification.verification_id,
        )

        if existing is not None:
            self._assert_replay_equivalent(
                existing=existing,
                requested=requested,
            )
            return existing

        verification_payload_json = (
            self._encode_verification(verification)
        )
        reason_codes_json = self._encode_json(
            list(verification.reason_codes),
            "IDENTITY_VERIFICATION_REASON_CODES_ENCODING_FAILED",
        )
        verification_metadata_json = self._encode_json(
            dict(verification.metadata),
            "IDENTITY_VERIFICATION_METADATA_ENCODING_FAILED",
        )

        try:
            self._connection.execute("BEGIN IMMEDIATE")

            self._insert_verification(
                verification=verification,
                verification_payload_json=(
                    verification_payload_json
                ),
                reason_codes_json=reason_codes_json,
                metadata_json=verification_metadata_json,
            )

            for reference in references:
                self._insert_evidence_reference(reference)

            self._connection.commit()
        except sqlite3.IntegrityError as exc:
            self._connection.rollback()

            replay = self.load_persisted_bundle(
                tenant_id=verification.tenant_id,
                verification_id=verification.verification_id,
            )

            if replay is not None:
                self._assert_replay_equivalent(
                    existing=replay,
                    requested=requested,
                )
                return replay

            self._raise_integrity_error(
                verification=verification,
                references=references,
                cause=exc,
            )
        except sqlite3.DatabaseError as exc:
            self._connection.rollback()
            raise DocumentPersistenceIntegrityError(
                "IDENTITY_VERIFICATION_ATOMIC_PERSISTENCE_FAILED"
            ) from exc
        except Exception:
            self._connection.rollback()
            raise

        persisted = self.load_persisted_bundle(
            tenant_id=verification.tenant_id,
            verification_id=verification.verification_id,
        )

        if persisted is None:
            raise DocumentPersistenceIntegrityError(
                "IDENTITY_VERIFICATION_PERSISTENCE_CONFIRMATION_FAILED"
            )

        self._assert_replay_equivalent(
            existing=persisted,
            requested=requested,
        )

        return persisted

    def load_persisted_bundle(
        self,
        *,
        tenant_id: str,
        verification_id: str,
    ) -> IdentityVerificationPersistenceBundle | None:
        tenant_id = self._required_text(
            tenant_id,
            "TENANT_ID_REQUIRED",
        )
        verification_id = self._required_text(
            verification_id,
            "IDENTITY_VERIFICATION_ID_REQUIRED",
        )

        verification_row = self._connection.execute(
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

        evidence_rows = self._connection.execute(
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

        if verification_row is None:
            if evidence_rows:
                raise DocumentPersistenceIntegrityError(
                    "ORPHANED_IDENTITY_VERIFICATION_EVIDENCE_SET"
                )

            return None

        verification = self._decode_verification(
            verification_row[5]
        )

        self._assert_verification_row_binding(
            verification=verification,
            tenant_id=str(verification_row[0]),
            verification_id=str(verification_row[1]),
            identity_id=str(verification_row[2]),
            document_id=str(verification_row[3]),
            workflow_id=str(verification_row[4]),
        )

        references = tuple(
            self._decode_evidence_row(row)
            for row in evidence_rows
        )

        self._assert_complete_reference_set(references)
        self._assert_reference_bindings(
            verification=verification,
            references=references,
        )

        return IdentityVerificationPersistenceBundle(
            verification=verification,
            evidence_references=references,
        )

    def _insert_verification(
        self,
        *,
        verification: IdentityVerificationRecord,
        verification_payload_json: str,
        reason_codes_json: str,
        metadata_json: str,
    ) -> None:
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
                ?, ?, ?, ?, ?, NULL, NULL, NULL,
                ?, ?, ?, ?, ?, ?, ?, 1, ?, NULL, ?, ?, ?
            )
            """,
            (
                verification.tenant_id,
                verification.verification_id,
                verification.identity_id,
                verification.document_id,
                verification.workflow_id,
                verification.document_type.value,
                verification.purpose.value,
                verification.decision.value,
                verification.assurance_level.value,
                verification.combined_score,
                verification.policy_version,
                verification.document_version,
                verification.verified_at.isoformat(),
                reason_codes_json,
                verification_payload_json,
                metadata_json,
            ),
        )

    def _insert_evidence_reference(
        self,
        reference: IdentityVerificationEvidenceReference,
    ) -> None:
        metadata_json = self._encode_json(
            dict(reference.metadata),
            "EVIDENCE_REFERENCE_METADATA_ENCODING_FAILED",
        )

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
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                reference.tenant_id,
                reference.verification_id,
                reference.evidence_type.value,
                reference.evidence_id,
                reference.evidence_version,
                reference.collected_at.isoformat(),
                metadata_json,
            ),
        )

    def _assert_document_binding(
        self,
        verification: IdentityVerificationRecord,
    ) -> None:
        if not isinstance(
            verification,
            IdentityVerificationRecord,
        ):
            raise TypeError(
                "IDENTITY_VERIFICATION_RECORD_REQUIRED"
            )

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

        if str(row[0]) != verification.identity_id:
            raise DocumentPersistenceIntegrityError(
                "IDENTITY_VERIFICATION_IDENTITY_BINDING_MISMATCH"
            )

        if str(row[1]) != verification.document_type.value:
            raise DocumentPersistenceIntegrityError(
                "IDENTITY_VERIFICATION_DOCUMENT_TYPE_BINDING_MISMATCH"
            )

        stored_version = row[2]

        if (
            isinstance(stored_version, bool)
            or not isinstance(stored_version, int)
            or stored_version < 1
        ):
            raise DocumentPersistenceIntegrityError(
                "STORED_DOCUMENT_VERSION_INVALID"
            )

        if stored_version != verification.document_version:
            raise DocumentPersistenceIntegrityError(
                "IDENTITY_VERIFICATION_DOCUMENT_VERSION_MISMATCH"
            )

    @classmethod
    def _assert_complete_reference_set(
        cls,
        references: tuple[
            IdentityVerificationEvidenceReference,
            ...,
        ],
    ) -> None:
        if len(references) != len(
            cls.REQUIRED_EVIDENCE_TYPES
        ):
            raise DocumentPersistenceIntegrityError(
                "IDENTITY_VERIFICATION_EVIDENCE_SET_INCOMPLETE"
            )

        evidence_types = {
            reference.evidence_type
            for reference in references
        }

        if evidence_types != cls.REQUIRED_EVIDENCE_TYPES:
            raise DocumentPersistenceIntegrityError(
                "IDENTITY_VERIFICATION_EVIDENCE_SET_INCOMPLETE"
            )

    @staticmethod
    def _assert_reference_bindings(
        *,
        verification: IdentityVerificationRecord,
        references: tuple[
            IdentityVerificationEvidenceReference,
            ...,
        ],
    ) -> None:
        by_type = {
            reference.evidence_type: reference
            for reference in references
        }

        for reference in references:
            if reference.tenant_id != verification.tenant_id:
                raise DocumentPersistenceIntegrityError(
                    "STORED_EVIDENCE_REFERENCE_TENANT_BINDING_MISMATCH"
                )

            if (
                reference.verification_id
                != verification.verification_id
            ):
                raise DocumentPersistenceIntegrityError(
                    "STORED_EVIDENCE_REFERENCE_VERIFICATION_BINDING_MISMATCH"
                )

        expected_identifiers = {
            IdentityVerificationEvidenceType.OCR_EXTRACTION: (
                verification.ocr_extraction_id
            ),
            IdentityVerificationEvidenceType.DOCUMENT_AUTHENTICITY: (
                verification.authenticity_assessment_id
            ),
            IdentityVerificationEvidenceType.DOCUMENT_SELFIE_MATCH: (
                verification.selfie_match_id
            ),
        }

        for evidence_type, expected_id in (
            expected_identifiers.items()
        ):
            if by_type[evidence_type].evidence_id != expected_id:
                raise DocumentPersistenceIntegrityError(
                    "STORED_EVIDENCE_REFERENCE_IDENTIFIER_MISMATCH"
                )

    @staticmethod
    def _assert_verification_row_binding(
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
    def _assert_replay_equivalent(
        *,
        existing: IdentityVerificationPersistenceBundle,
        requested: IdentityVerificationPersistenceBundle,
    ) -> None:
        if existing.verification != requested.verification:
            raise DocumentPersistenceConflictError(
                "IDENTITY_VERIFICATION_REPLAY_PAYLOAD_MISMATCH"
            )

        if (
            existing.evidence_references
            != requested.evidence_references
        ):
            raise DocumentPersistenceConflictError(
                "IDENTITY_VERIFICATION_EVIDENCE_REPLAY_MISMATCH"
            )

    @classmethod
    def _decode_evidence_row(
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

    def _raise_integrity_error(
        self,
        *,
        verification: IdentityVerificationRecord,
        references: tuple[
            IdentityVerificationEvidenceReference,
            ...,
        ],
        cause: sqlite3.IntegrityError,
    ) -> None:
        if self._verification_exists(
            tenant_id=verification.tenant_id,
            verification_id=verification.verification_id,
        ):
            raise DocumentPersistenceConflictError(
                "IDENTITY_VERIFICATION_ALREADY_EXISTS"
            ) from cause

        for reference in references:
            if self._evidence_type_exists(reference):
                raise DocumentPersistenceConflictError(
                    "IDENTITY_VERIFICATION_EVIDENCE_REFERENCE_ALREADY_EXISTS"
                ) from cause

            if self._evidence_id_exists(reference):
                raise DocumentPersistenceConflictError(
                    "IDENTITY_VERIFICATION_EVIDENCE_ID_ALREADY_REFERENCED"
                ) from cause

        raise DocumentPersistenceIntegrityError(
            "IDENTITY_VERIFICATION_ATOMIC_PERSISTENCE_FAILED"
        ) from cause

    def _verification_exists(
        self,
        *,
        tenant_id: str,
        verification_id: str,
    ) -> bool:
        return self._connection.execute(
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
        ).fetchone() is not None

    def _evidence_type_exists(
        self,
        reference: IdentityVerificationEvidenceReference,
    ) -> bool:
        return self._connection.execute(
            """
            SELECT 1
            FROM novaid_identity_verification_evidence_refs
            WHERE tenant_id = ?
              AND verification_id = ?
              AND evidence_type = ?
            """,
            (
                reference.tenant_id,
                reference.verification_id,
                reference.evidence_type.value,
            ),
        ).fetchone() is not None

    def _evidence_id_exists(
        self,
        reference: IdentityVerificationEvidenceReference,
    ) -> bool:
        return self._connection.execute(
            """
            SELECT 1
            FROM novaid_identity_verification_evidence_refs
            WHERE tenant_id = ?
              AND evidence_type = ?
              AND evidence_id = ?
            """,
            (
                reference.tenant_id,
                reference.evidence_type.value,
                reference.evidence_id,
            ),
        ).fetchone() is not None

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
        payload: object,
    ) -> IdentityVerificationRecord:
        if not isinstance(payload, str):
            raise DocumentPersistenceIntegrityError(
                "STORED_VERIFICATION_PAYLOAD_INVALID"
            )

        try:
            return decode_identity_verification_record_json(
                payload
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
            return IdentityVerificationEvidenceType(value)
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
    "IdentityVerificationPersistenceBundle",
    "SQLiteIdentityVerificationPersistenceCoordinator",
]
