from __future__ import annotations

from collections.abc import Mapping as ABCMapping
from dataclasses import fields as dataclass_fields
from dataclasses import is_dataclass
from datetime import datetime as GenericDateTime
from enum import Enum as GenericEnum
from types import UnionType
from typing import Any as GenericAny
from typing import Union, get_args, get_origin, get_type_hints

from afritech.novaid.domain import (
    IdentityVerificationEvidence,
    IdentityVerificationOutcomeEvent,
)

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from afritech.novaid.domain.biometric_models import (
    BiometricPurpose,
)
from afritech.novaid.domain.document_models import (
    IdentityDocumentType,
)
from afritech.novaid.domain.identity_verification_models import (
    IdentityVerificationDecision,
    IdentityVerificationRecord,
)
from afritech.novaid.domain.models import AssuranceLevel


class VerificationPersistenceCodecError(ValueError):
    """Base error for governed verification persistence."""


class VerificationPersistenceEncodingError(
    VerificationPersistenceCodecError
):
    """Raised when a verification record cannot be encoded safely."""


class IdentityVerificationRecordTypeError(
    VerificationPersistenceEncodingError,
    TypeError,
):
    """Raised when the public record encoder receives an invalid type."""


class VerificationPersistenceDecodingError(
    VerificationPersistenceCodecError
):
    """Raised when persisted verification data is invalid."""


VERIFICATION_CODEC_VERSION = 1
VERIFICATION_CODEC_TYPE = "NOVAID_IDENTITY_VERIFICATION_RECORD"


VERIFICATION_RECORD_FIELDS = frozenset(
    {
        "verification_id",
        "workflow_id",
        "tenant_id",
        "identity_id",
        "document_id",
        "document_type",
        "purpose",
        "decision",
        "assurance_level",
        "combined_score",
        "ocr_score",
        "authenticity_score",
        "selfie_match_score",
        "liveness_score",
        "ocr_extraction_id",
        "authenticity_assessment_id",
        "selfie_match_id",
        "policy_version",
        "document_version",
        "verified_at",
        "reason_codes",
        "metadata",
    }
)


FORBIDDEN_VERIFICATION_CODEC_FIELDS = frozenset(
    {
        "access_token",
        "api_key",
        "barcode_payload",
        "biometric_template",
        "credential",
        "document_bytes",
        "embedding",
        "embeddings",
        "face_embedding",
        "face_template",
        "feature_vector",
        "frames",
        "full_provider_response",
        "image",
        "image_bytes",
        "images",
        "mrz_raw",
        "mrz_text",
        "nfc_dump",
        "password",
        "private_key",
        "provider_payload",
        "provider_response",
        "provider_secret",
        "raw_barcode",
        "raw_document",
        "raw_frames",
        "raw_image",
        "raw_images",
        "raw_mrz",
        "raw_nfc",
        "raw_provider_response",
        "raw_selfie",
        "raw_text",
        "raw_video",
        "refresh_token",
        "secret",
        "selfie_bytes",
        "template_bytes",
        "video",
        "video_bytes",
    }
)


def _normalized_key(value: object) -> str:
    return str(value).strip().lower()


def _assert_safe_value(
    value: object,
    *,
    path: str = "$",
) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = _normalized_key(key)

            if normalized in FORBIDDEN_VERIFICATION_CODEC_FIELDS:
                raise VerificationPersistenceCodecError(
                    "RAW_VERIFICATION_PERSISTENCE_MATERIAL_FORBIDDEN:"
                    f"{path}.{normalized}"
                )

            _assert_safe_value(
                nested,
                path=f"{path}.{normalized}",
            )

        return

    if isinstance(value, (list, tuple, set, frozenset)):
        for index, nested in enumerate(value):
            _assert_safe_value(
                nested,
                path=f"{path}[{index}]",
            )


def _encode_datetime(value: datetime) -> str:
    if not isinstance(value, datetime):
        raise VerificationPersistenceEncodingError(
            "VERIFICATION_DATETIME_REQUIRED"
        )

    if value.tzinfo is None:
        raise VerificationPersistenceEncodingError(
            "VERIFICATION_DATETIME_TIMEZONE_REQUIRED"
        )

    return value.isoformat()


def _decode_datetime(value: object) -> datetime:
    if not isinstance(value, str):
        raise VerificationPersistenceDecodingError(
            "INVALID_VERIFICATION_DATETIME"
        )

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise VerificationPersistenceDecodingError(
            "INVALID_VERIFICATION_DATETIME"
        ) from exc

    if parsed.tzinfo is None:
        raise VerificationPersistenceDecodingError(
            "VERIFICATION_DATETIME_TIMEZONE_REQUIRED"
        )

    return parsed


def _encode_metadata(
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(metadata, Mapping):
        raise VerificationPersistenceEncodingError(
            "VERIFICATION_METADATA_MAPPING_REQUIRED"
        )

    copied = dict(metadata)

    try:
        _assert_safe_value(copied)
    except VerificationPersistenceCodecError as exc:
        raise VerificationPersistenceEncodingError(
            str(exc)
        ) from exc

    try:
        json.dumps(
            copied,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise VerificationPersistenceEncodingError(
            "VERIFICATION_METADATA_NOT_JSON_SAFE"
        ) from exc

    return copied


def _decode_metadata(
    metadata: object,
) -> dict[str, Any]:
    if not isinstance(metadata, Mapping):
        raise VerificationPersistenceDecodingError(
            "VERIFICATION_METADATA_MAPPING_REQUIRED"
        )

    copied = dict(metadata)

    try:
        _assert_safe_value(copied)
    except VerificationPersistenceCodecError as exc:
        raise VerificationPersistenceDecodingError(
            str(exc)
        ) from exc

    return copied


def _decode_text(
    value: object,
    error_code: str,
) -> str:
    if not isinstance(value, str):
        raise VerificationPersistenceDecodingError(
            error_code
        )

    normalized = value.strip()

    if not normalized:
        raise VerificationPersistenceDecodingError(
            error_code
        )

    return normalized


def _decode_score(
    value: object,
    error_code: str,
) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
    ):
        raise VerificationPersistenceDecodingError(
            error_code
        )

    normalized = float(value)

    if not 0.0 <= normalized <= 1.0:
        raise VerificationPersistenceDecodingError(
            error_code
        )

    return normalized


def _decode_positive_integer(
    value: object,
    error_code: str,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise VerificationPersistenceDecodingError(
            error_code
        )

    return value


def _decode_enum(
    enum_type: type[Any],
    value: object,
    error_code: str,
) -> Any:
    if not isinstance(value, str):
        raise VerificationPersistenceDecodingError(
            error_code
        )

    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        raise VerificationPersistenceDecodingError(
            error_code
        ) from exc


def _decode_reason_codes(
    value: object,
) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise VerificationPersistenceDecodingError(
            "VERIFICATION_REASON_CODES_LIST_REQUIRED"
        )

    reason_codes: list[str] = []

    for item in value:
        normalized = _decode_text(
            item,
            "INVALID_VERIFICATION_REASON_CODE",
        ).upper()

        if normalized not in reason_codes:
            reason_codes.append(normalized)

    return tuple(reason_codes)


def encode_identity_verification_record(
    verification: IdentityVerificationRecord,
) -> dict[str, object]:
    if not isinstance(
        verification,
        IdentityVerificationRecord,
    ):
        raise IdentityVerificationRecordTypeError(
            "IDENTITY_VERIFICATION_RECORD_REQUIRED"
        )

    metadata = _encode_metadata(
        verification.metadata
    )

    payload: dict[str, object] = {
        "verification_id": verification.verification_id,
        "workflow_id": verification.workflow_id,
        "tenant_id": verification.tenant_id,
        "identity_id": verification.identity_id,
        "document_id": verification.document_id,
        "document_type": verification.document_type.value,
        "purpose": verification.purpose.value,
        "decision": verification.decision.value,
        "assurance_level": verification.assurance_level.value,
        "combined_score": verification.combined_score,
        "ocr_score": verification.ocr_score,
        "authenticity_score": verification.authenticity_score,
        "selfie_match_score": verification.selfie_match_score,
        "liveness_score": verification.liveness_score,
        "ocr_extraction_id": verification.ocr_extraction_id,
        "authenticity_assessment_id": (
            verification.authenticity_assessment_id
        ),
        "selfie_match_id": verification.selfie_match_id,
        "policy_version": verification.policy_version,
        "document_version": verification.document_version,
        "verified_at": _encode_datetime(
            verification.verified_at
        ),
        "reason_codes": list(
            verification.reason_codes
        ),
        "metadata": metadata,
    }

    try:
        _assert_safe_value(payload)
    except VerificationPersistenceCodecError as exc:
        raise VerificationPersistenceEncodingError(
            str(exc)
        ) from exc

    return {
        "codec_version": VERIFICATION_CODEC_VERSION,
        "record_type": VERIFICATION_CODEC_TYPE,
        "payload": payload,
    }


def decode_identity_verification_record(
    envelope: Mapping[str, object],
) -> IdentityVerificationRecord:
    if not isinstance(envelope, Mapping):
        raise VerificationPersistenceDecodingError(
            "VERIFICATION_PERSISTENCE_MAPPING_REQUIRED"
        )

    try:
        _assert_safe_value(envelope)
    except VerificationPersistenceCodecError as exc:
        raise VerificationPersistenceDecodingError(
            str(exc)
        ) from exc

    expected_envelope_fields = {
        "codec_version",
        "record_type",
        "payload",
    }
    actual_envelope_fields = {
        str(key)
        for key in envelope
    }

    unknown_envelope_fields = (
        actual_envelope_fields
        - expected_envelope_fields
    )

    if unknown_envelope_fields:
        raise VerificationPersistenceDecodingError(
            "UNKNOWN_VERIFICATION_CODEC_ENVELOPE_FIELDS:"
            + ",".join(
                sorted(unknown_envelope_fields)
            )
        )

    if (
        envelope.get("codec_version")
        != VERIFICATION_CODEC_VERSION
    ):
        raise VerificationPersistenceDecodingError(
            "UNSUPPORTED_VERIFICATION_CODEC_VERSION"
        )

    if envelope.get("record_type") != VERIFICATION_CODEC_TYPE:
        raise VerificationPersistenceDecodingError(
            "INVALID_VERIFICATION_CODEC_RECORD_TYPE"
        )

    payload = envelope.get("payload")

    if not isinstance(payload, Mapping):
        raise VerificationPersistenceDecodingError(
            "VERIFICATION_PAYLOAD_MAPPING_REQUIRED"
        )

    actual_payload_fields = {
        str(key)
        for key in payload
    }

    unknown_payload_fields = (
        actual_payload_fields
        - VERIFICATION_RECORD_FIELDS
    )
    missing_payload_fields = (
        VERIFICATION_RECORD_FIELDS
        - actual_payload_fields
    )

    if unknown_payload_fields:
        raise VerificationPersistenceDecodingError(
            "UNKNOWN_VERIFICATION_PERSISTENCE_FIELDS:"
            + ",".join(
                sorted(unknown_payload_fields)
            )
        )

    if missing_payload_fields:
        raise VerificationPersistenceDecodingError(
            "MISSING_VERIFICATION_PERSISTENCE_FIELDS:"
            + ",".join(
                sorted(missing_payload_fields)
            )
        )

    values: dict[str, object] = {
        "verification_id": _decode_text(
            payload["verification_id"],
            "IDENTITY_VERIFICATION_ID_REQUIRED",
        ),
        "workflow_id": _decode_text(
            payload["workflow_id"],
            "IDENTITY_VERIFICATION_WORKFLOW_ID_REQUIRED",
        ),
        "tenant_id": _decode_text(
            payload["tenant_id"],
            "TENANT_ID_REQUIRED",
        ),
        "identity_id": _decode_text(
            payload["identity_id"],
            "IDENTITY_ID_REQUIRED",
        ),
        "document_id": _decode_text(
            payload["document_id"],
            "DOCUMENT_ID_REQUIRED",
        ),
        "document_type": _decode_enum(
            IdentityDocumentType,
            payload["document_type"],
            "INVALID_IDENTITY_DOCUMENT_TYPE",
        ),
        "purpose": _decode_enum(
            BiometricPurpose,
            payload["purpose"],
            "INVALID_BIOMETRIC_PURPOSE",
        ),
        "decision": _decode_enum(
            IdentityVerificationDecision,
            payload["decision"],
            "INVALID_IDENTITY_VERIFICATION_DECISION",
        ),
        "assurance_level": _decode_enum(
            AssuranceLevel,
            payload["assurance_level"],
            "INVALID_ASSURANCE_LEVEL",
        ),
        "combined_score": _decode_score(
            payload["combined_score"],
            "INVALID_IDENTITY_VERIFICATION_COMBINED_SCORE",
        ),
        "ocr_score": _decode_score(
            payload["ocr_score"],
            "INVALID_IDENTITY_VERIFICATION_OCR_SCORE",
        ),
        "authenticity_score": _decode_score(
            payload["authenticity_score"],
            "INVALID_IDENTITY_VERIFICATION_AUTHENTICITY_SCORE",
        ),
        "selfie_match_score": _decode_score(
            payload["selfie_match_score"],
            "INVALID_IDENTITY_VERIFICATION_SELFIE_MATCH_SCORE",
        ),
        "liveness_score": _decode_score(
            payload["liveness_score"],
            "INVALID_IDENTITY_VERIFICATION_LIVENESS_SCORE",
        ),
        "ocr_extraction_id": _decode_text(
            payload["ocr_extraction_id"],
            "OCR_EXTRACTION_ID_REQUIRED",
        ),
        "authenticity_assessment_id": _decode_text(
            payload["authenticity_assessment_id"],
            "DOCUMENT_AUTHENTICITY_ASSESSMENT_ID_REQUIRED",
        ),
        "selfie_match_id": _decode_text(
            payload["selfie_match_id"],
            "DOCUMENT_SELFIE_MATCH_ID_REQUIRED",
        ),
        "policy_version": _decode_text(
            payload["policy_version"],
            "IDENTITY_VERIFICATION_POLICY_VERSION_REQUIRED",
        ),
        "document_version": _decode_positive_integer(
            payload["document_version"],
            "INVALID_DOCUMENT_VERSION",
        ),
        "verified_at": _decode_datetime(
            payload["verified_at"]
        ),
        "reason_codes": _decode_reason_codes(
            payload["reason_codes"]
        ),
        "metadata": _decode_metadata(
            payload["metadata"]
        ),
    }

    try:
        return IdentityVerificationRecord(**values)
    except (TypeError, ValueError) as exc:
        raise VerificationPersistenceDecodingError(
            "INVALID_IDENTITY_VERIFICATION_PERSISTENCE_PAYLOAD"
        ) from exc


def encode_identity_verification_record_json(
    verification: IdentityVerificationRecord,
) -> str:
    envelope = encode_identity_verification_record(
        verification
    )

    try:
        return json.dumps(
            envelope,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise VerificationPersistenceEncodingError(
            "VERIFICATION_JSON_ENCODING_FAILED"
        ) from exc


def decode_identity_verification_record_json(
    payload: str,
) -> IdentityVerificationRecord:
    if not isinstance(payload, str):
        raise VerificationPersistenceDecodingError(
            "VERIFICATION_JSON_TEXT_REQUIRED"
        )

    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise VerificationPersistenceDecodingError(
            "INVALID_VERIFICATION_PERSISTENCE_JSON"
        ) from exc

    if not isinstance(decoded, Mapping):
        raise VerificationPersistenceDecodingError(
            "VERIFICATION_JSON_OBJECT_REQUIRED"
        )

    return decode_identity_verification_record(
        decoded
    )



def _encode_generic_identity_verification_value(
    value: object,
) -> object:
    if is_dataclass(value) and not isinstance(
        value,
        type,
    ):
        return {
            item.name: (
                _encode_generic_identity_verification_value(
                    getattr(value, item.name)
                )
            )
            for item in dataclass_fields(value)
        }

    if isinstance(value, GenericEnum):
        return _encode_generic_identity_verification_value(
            value.value
        )

    if isinstance(value, GenericDateTime):
        if value.tzinfo is None:
            raise ValueError(
                "IDENTITY_VERIFICATION_DATETIME_MUST_BE_AWARE"
            )

        return value.isoformat()

    if isinstance(value, ABCMapping):
        return {
            str(key): (
                _encode_generic_identity_verification_value(
                    nested
                )
            )
            for key, nested in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            _encode_generic_identity_verification_value(
                nested
            )
            for nested in value
        ]

    if isinstance(value, (set, frozenset)):
        encoded = [
            _encode_generic_identity_verification_value(
                nested
            )
            for nested in value
        ]

        return sorted(
            encoded,
            key=lambda item: json.dumps(
                item,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ),
        )

    if value is None or isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    raise TypeError(
        "UNSUPPORTED_IDENTITY_VERIFICATION_VALUE"
    )


def _decode_generic_identity_verification_value(
    value: object,
    annotation: object,
) -> object:
    if annotation in {
        GenericAny,
        object,
    }:
        return value

    origin = get_origin(annotation)
    arguments = get_args(annotation)

    if origin in {
        Union,
        UnionType,
    }:
        if value is None and type(None) in arguments:
            return None

        failures: list[Exception] = []

        for candidate in arguments:
            if candidate is type(None):
                continue

            try:
                return (
                    _decode_generic_identity_verification_value(
                        value,
                        candidate,
                    )
                )
            except (
                TypeError,
                ValueError,
            ) as exc:
                failures.append(exc)

        raise ValueError(
            "INVALID_IDENTITY_VERIFICATION_UNION_VALUE"
        ) from (
            failures[-1]
            if failures
            else None
        )

    if isinstance(annotation, type) and issubclass(
        annotation,
        GenericEnum,
    ):
        try:
            return annotation(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "INVALID_IDENTITY_VERIFICATION_ENUM"
            ) from exc

    if annotation is GenericDateTime:
        if not isinstance(value, str):
            raise ValueError(
                "INVALID_IDENTITY_VERIFICATION_DATETIME"
            )

        try:
            restored = GenericDateTime.fromisoformat(
                value
            )
        except ValueError as exc:
            raise ValueError(
                "INVALID_IDENTITY_VERIFICATION_DATETIME"
            ) from exc

        if restored.tzinfo is None:
            raise ValueError(
                "INVALID_IDENTITY_VERIFICATION_DATETIME"
            )

        return restored

    if isinstance(annotation, type) and is_dataclass(
        annotation
    ):
        if not isinstance(value, ABCMapping):
            raise ValueError(
                "IDENTITY_VERIFICATION_OBJECT_REQUIRED"
            )

        hints = get_type_hints(annotation)
        field_names = {
            item.name
            for item in dataclass_fields(annotation)
        }
        unknown = set(value) - field_names

        if unknown:
            raise ValueError(
                "UNKNOWN_IDENTITY_VERIFICATION_FIELDS"
            )

        restored: dict[str, object] = {}

        for item in dataclass_fields(annotation):
            if item.name not in value:
                continue

            restored[item.name] = (
                _decode_generic_identity_verification_value(
                    value[item.name],
                    hints.get(
                        item.name,
                        item.type,
                    ),
                )
            )

        try:
            return annotation(**restored)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "INVALID_IDENTITY_VERIFICATION_OBJECT"
            ) from exc

    if origin is tuple:
        if not isinstance(value, list):
            raise ValueError(
                "IDENTITY_VERIFICATION_ARRAY_REQUIRED"
            )

        item_type = (
            arguments[0]
            if arguments
            else GenericAny
        )

        return tuple(
            _decode_generic_identity_verification_value(
                nested,
                item_type,
            )
            for nested in value
        )

    if origin is frozenset:
        if not isinstance(value, list):
            raise ValueError(
                "IDENTITY_VERIFICATION_ARRAY_REQUIRED"
            )

        item_type = (
            arguments[0]
            if arguments
            else GenericAny
        )

        return frozenset(
            _decode_generic_identity_verification_value(
                nested,
                item_type,
            )
            for nested in value
        )

    if origin is set:
        if not isinstance(value, list):
            raise ValueError(
                "IDENTITY_VERIFICATION_ARRAY_REQUIRED"
            )

        item_type = (
            arguments[0]
            if arguments
            else GenericAny
        )

        return {
            _decode_generic_identity_verification_value(
                nested,
                item_type,
            )
            for nested in value
        }

    if origin is list:
        if not isinstance(value, list):
            raise ValueError(
                "IDENTITY_VERIFICATION_ARRAY_REQUIRED"
            )

        item_type = (
            arguments[0]
            if arguments
            else GenericAny
        )

        return [
            _decode_generic_identity_verification_value(
                nested,
                item_type,
            )
            for nested in value
        ]

    if origin in {
        dict,
        ABCMapping,
    }:
        if not isinstance(value, ABCMapping):
            raise ValueError(
                "IDENTITY_VERIFICATION_MAPPING_REQUIRED"
            )

        key_type = (
            arguments[0]
            if arguments
            else str
        )
        value_type = (
            arguments[1]
            if len(arguments) > 1
            else GenericAny
        )

        return {
            _decode_generic_identity_verification_value(
                key,
                key_type,
            ): _decode_generic_identity_verification_value(
                nested,
                value_type,
            )
            for key, nested in value.items()
        }

    if annotation in {
        str,
        int,
        float,
        bool,
    }:
        if not isinstance(value, annotation):
            raise ValueError(
                "INVALID_IDENTITY_VERIFICATION_VALUE_TYPE"
            )

        return value

    return value


def encode_identity_verification_payload(
    value: object,
) -> str:
    encoded = _encode_generic_identity_verification_value(
        value
    )

    try:
        _assert_safe_value(encoded)
    except VerificationPersistenceCodecError as exc:
        if (
            "RAW_VERIFICATION_PERSISTENCE_MATERIAL_FORBIDDEN"
            in str(exc)
        ):
            raise ValueError(
                str(exc).replace(
                    "RAW_VERIFICATION_PERSISTENCE_"
                    "MATERIAL_FORBIDDEN",
                    "RAW_IDENTITY_VERIFICATION_"
                    "MATERIAL_FORBIDDEN",
                    1,
                )
            ) from exc

        raise

    try:
        return json.dumps(
            encoded,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "INVALID_IDENTITY_VERIFICATION_PAYLOAD"
        ) from exc


def decode_identity_verification_payload(
    payload: object,
    model_type: type[object],
) -> object:
    if not isinstance(model_type, type):
        raise TypeError(
            "IDENTITY_VERIFICATION_MODEL_TYPE_REQUIRED"
        )

    if isinstance(payload, str):
        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "INVALID_IDENTITY_VERIFICATION_JSON"
            ) from exc
    elif isinstance(payload, ABCMapping):
        decoded = dict(payload)
    else:
        raise ValueError(
            "INVALID_IDENTITY_VERIFICATION_PAYLOAD"
        )

    try:
        _assert_safe_value(decoded)
    except VerificationPersistenceCodecError as exc:
        if (
            "RAW_VERIFICATION_PERSISTENCE_MATERIAL_FORBIDDEN"
            in str(exc)
        ):
            raise ValueError(
                str(exc).replace(
                    "RAW_VERIFICATION_PERSISTENCE_"
                    "MATERIAL_FORBIDDEN",
                    "RAW_IDENTITY_VERIFICATION_"
                    "MATERIAL_FORBIDDEN",
                    1,
                )
            ) from exc

        raise

    return _decode_generic_identity_verification_value(
        decoded,
        model_type,
    )


def encode_identity_verification_evidence(
    evidence: IdentityVerificationEvidence,
) -> str:
    if not isinstance(
        evidence,
        IdentityVerificationEvidence,
    ):
        raise TypeError(
            "IDENTITY_VERIFICATION_EVIDENCE_REQUIRED"
        )

    return encode_identity_verification_payload(
        evidence
    )


def identity_verification_evidence_from_payload(
    payload: object,
) -> IdentityVerificationEvidence:
    restored = decode_identity_verification_payload(
        payload,
        IdentityVerificationEvidence,
    )

    if not isinstance(
        restored,
        IdentityVerificationEvidence,
    ):
        raise ValueError(
            "INVALID_IDENTITY_VERIFICATION_EVIDENCE"
        )

    return restored


def identity_verification_record_from_payload(
    payload: object,
) -> IdentityVerificationRecord:
    restored = decode_identity_verification_payload(
        payload,
        IdentityVerificationRecord,
    )

    if not isinstance(
        restored,
        IdentityVerificationRecord,
    ):
        raise ValueError(
            "INVALID_IDENTITY_VERIFICATION_RECORD"
        )

    return restored


def encode_identity_verification_outcome_event(
    event: IdentityVerificationOutcomeEvent,
) -> str:
    if not isinstance(
        event,
        IdentityVerificationOutcomeEvent,
    ):
        raise TypeError(
            "IDENTITY_VERIFICATION_OUTCOME_EVENT_REQUIRED"
        )

    return encode_identity_verification_payload(
        event
    )


def identity_verification_outcome_event_from_payload(
    payload: object,
) -> IdentityVerificationOutcomeEvent:
    restored = decode_identity_verification_payload(
        payload,
        IdentityVerificationOutcomeEvent,
    )

    if not isinstance(
        restored,
        IdentityVerificationOutcomeEvent,
    ):
        raise ValueError(
            "INVALID_IDENTITY_VERIFICATION_OUTCOME_EVENT"
        )

    return restored


__all__ = [
    "VerificationPersistenceCodecError",
    "VerificationPersistenceDecodingError",
    "VerificationPersistenceEncodingError",
    "decode_identity_verification_payload",
    "decode_identity_verification_record",
    "decode_identity_verification_record_json",
    "encode_identity_verification_evidence",
    "encode_identity_verification_outcome_event",
    "encode_identity_verification_payload",
    "encode_identity_verification_record",
    "encode_identity_verification_record_json",
    "identity_verification_evidence_from_payload",
    "identity_verification_outcome_event_from_payload",
    "identity_verification_record_from_payload",
]
