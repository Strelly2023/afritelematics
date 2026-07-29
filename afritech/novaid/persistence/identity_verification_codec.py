from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from datetime import datetime
from enum import Enum
from types import UnionType
from typing import (
    Any,
    Mapping,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from afritech.novaid.domain import (
    IdentityVerificationEvidence,
    IdentityVerificationOutcomeEvent,
    IdentityVerificationRecord,
)


FORBIDDEN_IDENTITY_VERIFICATION_PERSISTENCE_FIELDS = frozenset(
    {
        "raw_image",
        "raw_images",
        "image",
        "images",
        "image_bytes",
        "raw_selfie",
        "selfie",
        "selfie_image",
        "document_image",
        "front_image",
        "back_image",
        "raw_video",
        "video",
        "video_bytes",
        "frames",
        "camera_buffer",
        "binary_payload",
        "base64",
        "base64_data",
        "blob",
        "file_bytes",
        "document_bytes",
        "pdf_bytes",
        "raw_document",
        "raw_ocr",
        "raw_provider_response",
        "provider_response",
        "provider_payload",
        "embedding",
        "embeddings",
        "feature_vector",
        "feature_vectors",
        "template",
        "biometric_template",
        "face_template",
        "private_key",
        "secret_key",
        "provider_secret",
        "api_key",
        "access_token",
        "refresh_token",
        "password",
    }
)


def _normalized_key(value: Any) -> str:
    return str(value).strip().lower()


def _assert_safe_payload(
    value: Any,
    *,
    path: str = "payload",
) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = _normalized_key(key)

            if (
                normalized
                in FORBIDDEN_IDENTITY_VERIFICATION_PERSISTENCE_FIELDS
            ):
                raise ValueError(
                    "RAW_IDENTITY_VERIFICATION_MATERIAL_FORBIDDEN"
                )

            _assert_safe_payload(
                item,
                path=f"{path}.{normalized}",
            )

        return

    if isinstance(value, (list, tuple, set, frozenset)):
        for index, item in enumerate(value):
            _assert_safe_payload(
                item,
                path=f"{path}[{index}]",
            )


def _json_value(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, datetime):
        return value.isoformat()

    if is_dataclass(value) and not isinstance(value, type):
        payload = {
            field.name: _json_value(
                getattr(value, field.name)
            )
            for field in fields(value)
        }
        _assert_safe_payload(payload)
        return payload

    if isinstance(value, Mapping):
        payload = {
            str(key): _json_value(item)
            for key, item in value.items()
        }
        _assert_safe_payload(payload)
        return payload

    if isinstance(value, tuple):
        return [_json_value(item) for item in value]

    if isinstance(value, frozenset):
        encoded = [_json_value(item) for item in value]

        return sorted(
            encoded,
            key=lambda item: json.dumps(
                item,
                separators=(",", ":"),
                sort_keys=True,
            ),
        )

    if isinstance(value, (list, set)):
        return [_json_value(item) for item in value]

    if isinstance(value, (str, int, float, bool)):
        return value

    raise TypeError(
        "UNSUPPORTED_IDENTITY_VERIFICATION_CODEC_VALUE:"
        f"{type(value).__module__}.{type(value).__qualname__}"
    )


def _decode_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value

    if not isinstance(value, str):
        raise ValueError(
            "INVALID_IDENTITY_VERIFICATION_DATETIME"
        )

    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            "INVALID_IDENTITY_VERIFICATION_DATETIME"
        ) from exc


def _decode_union(
    value: Any,
    annotation: Any,
) -> Any:
    arguments = get_args(annotation)

    if value is None and type(None) in arguments:
        return None

    failures: list[Exception] = []

    for candidate in arguments:
        if candidate is type(None):
            continue

        try:
            return _decode_value(value, candidate)
        except (
            KeyError,
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


def _decode_dataclass(
    payload: Any,
    model_type: type[Any],
) -> Any:
    if not isinstance(payload, Mapping):
        raise ValueError(
            "INVALID_IDENTITY_VERIFICATION_OBJECT"
        )

    _assert_safe_payload(payload)

    type_hints = get_type_hints(model_type)
    known_fields = {
        field.name
        for field in fields(model_type)
    }

    unknown_fields = set(payload) - known_fields

    if unknown_fields:
        raise ValueError(
            "UNKNOWN_IDENTITY_VERIFICATION_FIELDS:"
            + ",".join(
                sorted(str(item) for item in unknown_fields)
            )
        )

    arguments: dict[str, Any] = {}

    for field in fields(model_type):
        if field.name not in payload:
            continue

        annotation = type_hints.get(
            field.name,
            field.type,
        )

        arguments[field.name] = _decode_value(
            payload[field.name],
            annotation,
        )

    try:
        return model_type(**arguments)
    except (
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            "INVALID_IDENTITY_VERIFICATION_DOMAIN_PAYLOAD"
        ) from exc


def _decode_value(
    value: Any,
    annotation: Any,
) -> Any:
    if annotation is Any:
        _assert_safe_payload(value)
        return value

    origin = get_origin(annotation)
    arguments = get_args(annotation)

    if origin in {Union, UnionType}:
        return _decode_union(value, annotation)

    if annotation is datetime:
        return _decode_datetime(value)

    if (
        isinstance(annotation, type)
        and issubclass(annotation, Enum)
    ):
        try:
            return annotation(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "INVALID_IDENTITY_VERIFICATION_ENUM_VALUE"
            ) from exc

    if (
        isinstance(annotation, type)
        and is_dataclass(annotation)
    ):
        return _decode_dataclass(
            value,
            annotation,
        )

    if origin is tuple:
        if not isinstance(value, (list, tuple)):
            raise ValueError(
                "INVALID_IDENTITY_VERIFICATION_TUPLE"
            )

        item_type = arguments[0] if arguments else Any

        return tuple(
            _decode_value(item, item_type)
            for item in value
        )

    if origin is frozenset:
        if not isinstance(
            value,
            (list, tuple, set, frozenset),
        ):
            raise ValueError(
                "INVALID_IDENTITY_VERIFICATION_FROZENSET"
            )

        item_type = arguments[0] if arguments else Any

        return frozenset(
            _decode_value(item, item_type)
            for item in value
        )

    if origin is list:
        if not isinstance(value, list):
            raise ValueError(
                "INVALID_IDENTITY_VERIFICATION_LIST"
            )

        item_type = arguments[0] if arguments else Any

        return [
            _decode_value(item, item_type)
            for item in value
        ]

    if origin in {dict, Mapping}:
        if not isinstance(value, Mapping):
            raise ValueError(
                "INVALID_IDENTITY_VERIFICATION_MAPPING"
            )

        key_type = arguments[0] if arguments else str
        value_type = arguments[1] if len(arguments) > 1 else Any

        decoded = {
            _decode_value(key, key_type): _decode_value(
                item,
                value_type,
            )
            for key, item in value.items()
        }

        _assert_safe_payload(decoded)
        return decoded

    if annotation is bool:
        if not isinstance(value, bool):
            raise ValueError(
                "INVALID_IDENTITY_VERIFICATION_BOOLEAN"
            )
        return value

    if annotation is int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(
                "INVALID_IDENTITY_VERIFICATION_INTEGER"
            )
        return value

    if annotation is float:
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
        ):
            raise ValueError(
                "INVALID_IDENTITY_VERIFICATION_NUMBER"
            )
        return float(value)

    if annotation is str:
        if not isinstance(value, str):
            raise ValueError(
                "INVALID_IDENTITY_VERIFICATION_TEXT"
            )
        return value

    _assert_safe_payload(value)
    return value


def encode_identity_verification_payload(
    value: Any,
) -> str:
    payload = _json_value(value)
    _assert_safe_payload(payload)

    return json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
    )


def decode_identity_verification_payload(
    value: Any,
    model_type: type[Any],
) -> Any:
    if isinstance(value, str):
        try:
            payload = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "INVALID_IDENTITY_VERIFICATION_JSON"
            ) from exc
    else:
        payload = value

    _assert_safe_payload(payload)

    if (
        not isinstance(model_type, type)
        or not is_dataclass(model_type)
    ):
        raise TypeError(
            "IDENTITY_VERIFICATION_MODEL_TYPE_REQUIRED"
        )

    return _decode_dataclass(
        payload,
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
    value: Any,
) -> IdentityVerificationEvidence:
    return decode_identity_verification_payload(
        value,
        IdentityVerificationEvidence,
    )


def encode_identity_verification_record(
    record: IdentityVerificationRecord,
) -> str:
    if not isinstance(
        record,
        IdentityVerificationRecord,
    ):
        raise TypeError(
            "IDENTITY_VERIFICATION_RECORD_REQUIRED"
        )

    return encode_identity_verification_payload(
        record
    )


def identity_verification_record_from_payload(
    value: Any,
) -> IdentityVerificationRecord:
    return decode_identity_verification_payload(
        value,
        IdentityVerificationRecord,
    )


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
    value: Any,
) -> IdentityVerificationOutcomeEvent:
    return decode_identity_verification_payload(
        value,
        IdentityVerificationOutcomeEvent,
    )


__all__ = [
    "FORBIDDEN_IDENTITY_VERIFICATION_PERSISTENCE_FIELDS",
    "decode_identity_verification_payload",
    "encode_identity_verification_evidence",
    "encode_identity_verification_outcome_event",
    "encode_identity_verification_payload",
    "encode_identity_verification_record",
    "identity_verification_evidence_from_payload",
    "identity_verification_outcome_event_from_payload",
    "identity_verification_record_from_payload",
]
