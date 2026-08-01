from __future__ import annotations

import json
import types
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from enum import Enum
from typing import (
    Any,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from afritech.novaid.domain.document_models import (
    DocumentCaptureReference,
    DocumentVerificationEvidence,
    IdentityDocument,
)


class DocumentPersistenceCodecError(ValueError):
    """Base error for deterministic document encoding."""


class DocumentPersistenceEncodingError(
    DocumentPersistenceCodecError
):
    """Raised when a document cannot be encoded safely."""


class DocumentPersistenceDecodingError(
    DocumentPersistenceCodecError
):
    """Raised when persisted data cannot be decoded safely."""


DOCUMENT_CODEC_VERSION = 1
DOCUMENT_CODEC_TYPE = "NOVAID_IDENTITY_DOCUMENT"


FORBIDDEN_DOCUMENT_CODEC_FIELDS = frozenset(
    {
        "raw_image",
        "raw_images",
        "image",
        "images",
        "image_bytes",
        "document_bytes",
        "raw_document",
        "raw_selfie",
        "selfie_bytes",
        "raw_video",
        "video",
        "video_bytes",
        "frames",
        "raw_frames",
        "raw_text",
        "raw_mrz",
        "mrz_raw",
        "mrz_text",
        "barcode_payload",
        "raw_barcode",
        "nfc_dump",
        "raw_nfc",
        "provider_payload",
        "provider_response",
        "full_provider_response",
        "embedding",
        "embeddings",
        "face_embedding",
        "feature_vector",
        "biometric_template",
        "template_bytes",
        "api_key",
        "provider_secret",
        "private_key",
        "access_token",
        "refresh_token",
        "password",
        "credential",
        "secret",
    }
)


T = TypeVar("T")


_ALLOWED_DATACLASSES: dict[str, type[Any]] = {
    DocumentCaptureReference.__name__: DocumentCaptureReference,
    DocumentVerificationEvidence.__name__: (
        DocumentVerificationEvidence
    ),
    IdentityDocument.__name__: IdentityDocument,
}


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

            if normalized in FORBIDDEN_DOCUMENT_CODEC_FIELDS:
                raise DocumentPersistenceCodecError(
                    "RAW_DOCUMENT_PERSISTENCE_MATERIAL_FORBIDDEN:"
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


def _encode_value(value: object) -> object:
    if value is None:
        return None

    if isinstance(value, Enum):
        return {
            "__kind__": "enum",
            "type": value.__class__.__name__,
            "value": value.value,
        }

    if isinstance(value, datetime):
        return {
            "__kind__": "datetime",
            "value": value.isoformat(),
        }

    if isinstance(value, date):
        return {
            "__kind__": "date",
            "value": value.isoformat(),
        }

    if is_dataclass(value) and not isinstance(value, type):
        dataclass_name = value.__class__.__name__

        if dataclass_name not in _ALLOWED_DATACLASSES:
            raise DocumentPersistenceEncodingError(
                "UNSUPPORTED_DOCUMENT_DATACLASS:"
                f"{dataclass_name}"
            )

        payload = {
            item.name: _encode_value(
                getattr(value, item.name)
            )
            for item in fields(value)
        }

        _assert_safe_value(payload)

        return {
            "__kind__": "dataclass",
            "type": dataclass_name,
            "fields": payload,
        }

    if isinstance(value, tuple):
        return {
            "__kind__": "tuple",
            "items": [
                _encode_value(item)
                for item in value
            ],
        }

    if isinstance(value, list):
        return {
            "__kind__": "list",
            "items": [
                _encode_value(item)
                for item in value
            ],
        }

    if isinstance(value, Mapping):
        encoded = {
            str(key): _encode_value(nested)
            for key, nested in value.items()
        }

        _assert_safe_value(encoded)
        return encoded

    if isinstance(value, (str, int, float, bool)):
        return value

    raise DocumentPersistenceEncodingError(
        "UNSUPPORTED_DOCUMENT_PERSISTENCE_VALUE:"
        f"{type(value).__name__}"
    )


def _decode_datetime(value: object) -> datetime:
    if not isinstance(value, str):
        raise DocumentPersistenceDecodingError(
            "INVALID_DOCUMENT_DATETIME"
        )

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise DocumentPersistenceDecodingError(
            "INVALID_DOCUMENT_DATETIME"
        ) from exc

    if parsed.tzinfo is None:
        raise DocumentPersistenceDecodingError(
            "DOCUMENT_DATETIME_TIMEZONE_REQUIRED"
        )

    return parsed


def _decode_date(value: object) -> date:
    if not isinstance(value, str):
        raise DocumentPersistenceDecodingError(
            "INVALID_DOCUMENT_DATE"
        )

    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise DocumentPersistenceDecodingError(
            "INVALID_DOCUMENT_DATE"
        ) from exc


def _decode_typed_value(
    annotation: object,
    value: object,
) -> object:
    if annotation is Any:
        return _decode_untyped_value(value)

    origin = get_origin(annotation)
    arguments = get_args(annotation)

    if origin in (Union, types.UnionType):
        if value is None and type(None) in arguments:
            return None

        non_none = tuple(
            argument
            for argument in arguments
            if argument is not type(None)
        )

        errors: list[Exception] = []

        for candidate in non_none:
            try:
                return _decode_typed_value(
                    candidate,
                    value,
                )
            except (
                DocumentPersistenceDecodingError,
                TypeError,
                ValueError,
            ) as exc:
                errors.append(exc)

        raise DocumentPersistenceDecodingError(
            "DOCUMENT_UNION_VALUE_INVALID"
        ) from (
            errors[-1]
            if errors
            else None
        )

    if annotation is datetime:
        if isinstance(value, Mapping):
            if value.get("__kind__") != "datetime":
                raise DocumentPersistenceDecodingError(
                    "DOCUMENT_DATETIME_KIND_INVALID"
                )

            return _decode_datetime(
                value.get("value")
            )

        return _decode_datetime(value)

    if annotation is date:
        if isinstance(value, Mapping):
            if value.get("__kind__") != "date":
                raise DocumentPersistenceDecodingError(
                    "DOCUMENT_DATE_KIND_INVALID"
                )

            return _decode_date(
                value.get("value")
            )

        return _decode_date(value)

    if (
        isinstance(annotation, type)
        and issubclass(annotation, Enum)
    ):
        raw_value = value

        if isinstance(value, Mapping):
            if value.get("__kind__") != "enum":
                raise DocumentPersistenceDecodingError(
                    "DOCUMENT_ENUM_KIND_INVALID"
                )

            raw_value = value.get("value")

        try:
            return annotation(raw_value)
        except (TypeError, ValueError) as exc:
            raise DocumentPersistenceDecodingError(
                "INVALID_DOCUMENT_ENUM_VALUE:"
                f"{annotation.__name__}"
            ) from exc

    if (
        isinstance(annotation, type)
        and is_dataclass(annotation)
    ):
        return _decode_dataclass(
            annotation,
            value,
        )

    if origin is tuple:
        if isinstance(value, Mapping):
            if value.get("__kind__") != "tuple":
                raise DocumentPersistenceDecodingError(
                    "DOCUMENT_TUPLE_KIND_INVALID"
                )

            raw_items = value.get("items")
        else:
            raw_items = value

        if not isinstance(raw_items, list):
            raise DocumentPersistenceDecodingError(
                "DOCUMENT_TUPLE_REQUIRED"
            )

        if len(arguments) == 2 and arguments[1] is Ellipsis:
            return tuple(
                _decode_typed_value(
                    arguments[0],
                    item,
                )
                for item in raw_items
            )

        if arguments and len(arguments) != len(raw_items):
            raise DocumentPersistenceDecodingError(
                "DOCUMENT_TUPLE_LENGTH_MISMATCH"
            )

        if not arguments:
            return tuple(
                _decode_untyped_value(item)
                for item in raw_items
            )

        return tuple(
            _decode_typed_value(
                item_type,
                item,
            )
            for item_type, item in zip(
                arguments,
                raw_items,
                strict=True,
            )
        )

    if origin is list:
        if isinstance(value, Mapping):
            if value.get("__kind__") != "list":
                raise DocumentPersistenceDecodingError(
                    "DOCUMENT_LIST_KIND_INVALID"
                )

            raw_items = value.get("items")
        else:
            raw_items = value

        if not isinstance(raw_items, list):
            raise DocumentPersistenceDecodingError(
                "DOCUMENT_LIST_REQUIRED"
            )

        item_type = (
            arguments[0]
            if arguments
            else Any
        )

        return [
            _decode_typed_value(
                item_type,
                item,
            )
            for item in raw_items
        ]

    if origin is dict:
        if not isinstance(value, Mapping):
            raise DocumentPersistenceDecodingError(
                "DOCUMENT_MAPPING_REQUIRED"
            )

        key_type = (
            arguments[0]
            if arguments
            else str
        )
        value_type = (
            arguments[1]
            if len(arguments) > 1
            else Any
        )

        return {
            _decode_typed_value(
                key_type,
                key,
            ): _decode_typed_value(
                value_type,
                nested,
            )
            for key, nested in value.items()
        }

    if annotation in (str, int, float, bool):
        if annotation is bool:
            if not isinstance(value, bool):
                raise DocumentPersistenceDecodingError(
                    "DOCUMENT_BOOLEAN_REQUIRED"
                )

            return value

        if annotation is int:
            if isinstance(value, bool) or not isinstance(value, int):
                raise DocumentPersistenceDecodingError(
                    "DOCUMENT_INTEGER_REQUIRED"
                )

            return value

        if annotation is float:
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
            ):
                raise DocumentPersistenceDecodingError(
                    "DOCUMENT_NUMBER_REQUIRED"
                )

            return float(value)

        if not isinstance(value, str):
            raise DocumentPersistenceDecodingError(
                "DOCUMENT_TEXT_REQUIRED"
            )

        return value

    return _decode_untyped_value(value)


def _decode_untyped_value(value: object) -> object:
    if not isinstance(value, Mapping):
        if isinstance(value, list):
            return [
                _decode_untyped_value(item)
                for item in value
            ]

        return value

    kind = value.get("__kind__")

    if kind == "datetime":
        return _decode_datetime(value.get("value"))

    if kind == "date":
        return _decode_date(value.get("value"))

    if kind == "tuple":
        items = value.get("items")

        if not isinstance(items, list):
            raise DocumentPersistenceDecodingError(
                "DOCUMENT_TUPLE_REQUIRED"
            )

        return tuple(
            _decode_untyped_value(item)
            for item in items
        )

    if kind == "list":
        items = value.get("items")

        if not isinstance(items, list):
            raise DocumentPersistenceDecodingError(
                "DOCUMENT_LIST_REQUIRED"
            )

        return [
            _decode_untyped_value(item)
            for item in items
        ]

    if kind == "dataclass":
        type_name = value.get("type")

        if not isinstance(type_name, str):
            raise DocumentPersistenceDecodingError(
                "DOCUMENT_DATACLASS_TYPE_REQUIRED"
            )

        model = _ALLOWED_DATACLASSES.get(type_name)

        if model is None:
            raise DocumentPersistenceDecodingError(
                "UNSUPPORTED_DOCUMENT_DATACLASS:"
                f"{type_name}"
            )

        return _decode_dataclass(
            model,
            value,
        )

    return {
        str(key): _decode_untyped_value(nested)
        for key, nested in value.items()
    }


def _decode_dataclass(
    model: type[T],
    value: object,
) -> T:
    if not isinstance(value, Mapping):
        raise DocumentPersistenceDecodingError(
            "DOCUMENT_DATACLASS_MAPPING_REQUIRED"
        )

    if "__kind__" in value:
        if value.get("__kind__") != "dataclass":
            raise DocumentPersistenceDecodingError(
                "DOCUMENT_DATACLASS_KIND_INVALID"
            )

        encoded_type = value.get("type")

        if encoded_type != model.__name__:
            raise DocumentPersistenceDecodingError(
                "DOCUMENT_DATACLASS_TYPE_MISMATCH"
            )

        raw_fields = value.get("fields")
    else:
        raw_fields = value

    if not isinstance(raw_fields, Mapping):
        raise DocumentPersistenceDecodingError(
            "DOCUMENT_DATACLASS_FIELDS_REQUIRED"
        )

    _assert_safe_value(raw_fields)

    expected_fields = {
        item.name
        for item in fields(model)
    }
    actual_fields = {
        str(key)
        for key in raw_fields
    }

    unknown = actual_fields - expected_fields

    if unknown:
        raise DocumentPersistenceDecodingError(
            "UNKNOWN_DOCUMENT_PERSISTENCE_FIELDS:"
            + ",".join(sorted(unknown))
        )

    hints = get_type_hints(model)
    values: dict[str, object] = {}

    for item in fields(model):
        if item.name not in raw_fields:
            continue

        annotation = hints.get(
            item.name,
            Any,
        )
        values[item.name] = _decode_typed_value(
            annotation,
            raw_fields[item.name],
        )

    try:
        return model(**values)
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise DocumentPersistenceDecodingError(
            "INVALID_DOCUMENT_PERSISTENCE_PAYLOAD:"
            f"{model.__name__}"
        ) from exc


def encode_identity_document(
    document: IdentityDocument,
) -> dict[str, object]:
    if not isinstance(document, IdentityDocument):
        raise DocumentPersistenceEncodingError(
            "IDENTITY_DOCUMENT_REQUIRED"
        )

    encoded = _encode_value(document)

    if not isinstance(encoded, Mapping):
        raise DocumentPersistenceEncodingError(
            "IDENTITY_DOCUMENT_ENCODING_INVALID"
        )

    envelope: dict[str, object] = {
        "codec_version": DOCUMENT_CODEC_VERSION,
        "record_type": DOCUMENT_CODEC_TYPE,
        "payload": dict(encoded),
    }

    _assert_safe_value(envelope)
    return envelope


def decode_identity_document(
    payload: Mapping[str, object],
) -> IdentityDocument:
    if not isinstance(payload, Mapping):
        raise DocumentPersistenceDecodingError(
            "DOCUMENT_PERSISTENCE_MAPPING_REQUIRED"
        )

    try:
        _assert_safe_value(payload)
    except DocumentPersistenceCodecError as exc:
        raise DocumentPersistenceDecodingError(
            str(exc)
        ) from exc

    expected_envelope_fields = {
        "codec_version",
        "record_type",
        "payload",
    }
    actual_envelope_fields = {
        str(key)
        for key in payload
    }

    unknown = (
        actual_envelope_fields
        - expected_envelope_fields
    )

    if unknown:
        raise DocumentPersistenceDecodingError(
            "UNKNOWN_DOCUMENT_CODEC_ENVELOPE_FIELDS:"
            + ",".join(sorted(unknown))
        )

    if payload.get("codec_version") != DOCUMENT_CODEC_VERSION:
        raise DocumentPersistenceDecodingError(
            "UNSUPPORTED_DOCUMENT_CODEC_VERSION"
        )

    if payload.get("record_type") != DOCUMENT_CODEC_TYPE:
        raise DocumentPersistenceDecodingError(
            "INVALID_DOCUMENT_CODEC_RECORD_TYPE"
        )

    return _decode_dataclass(
        IdentityDocument,
        payload.get("payload"),
    )


def encode_identity_document_json(
    document: IdentityDocument,
) -> str:
    payload = encode_identity_document(document)

    try:
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise DocumentPersistenceEncodingError(
            "DOCUMENT_JSON_ENCODING_FAILED"
        ) from exc


def decode_identity_document_json(
    payload: str,
) -> IdentityDocument:
    if not isinstance(payload, str):
        raise DocumentPersistenceDecodingError(
            "DOCUMENT_JSON_TEXT_REQUIRED"
        )

    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise DocumentPersistenceDecodingError(
            "INVALID_DOCUMENT_PERSISTENCE_JSON"
        ) from exc

    if not isinstance(decoded, Mapping):
        raise DocumentPersistenceDecodingError(
            "DOCUMENT_JSON_OBJECT_REQUIRED"
        )

    return decode_identity_document(decoded)


__all__ = [
    "DOCUMENT_CODEC_TYPE",
    "DOCUMENT_CODEC_VERSION",
    "FORBIDDEN_DOCUMENT_CODEC_FIELDS",
    "DocumentPersistenceCodecError",
    "DocumentPersistenceDecodingError",
    "DocumentPersistenceEncodingError",
    "decode_identity_document",
    "decode_identity_document_json",
    "encode_identity_document",
    "encode_identity_document_json",
]
