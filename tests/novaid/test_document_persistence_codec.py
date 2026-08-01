from __future__ import annotations

import json
from dataclasses import (
    MISSING,
    FrozenInstanceError,
    fields,
    is_dataclass,
)
from datetime import date, datetime, timezone
from enum import Enum
from inspect import signature
from typing import Any, get_args, get_origin, get_type_hints
from uuid import uuid4

import pytest

from afritech.novaid.domain.document_models import (
    DocumentCaptureReference,
    DocumentVerificationEvidence,
    IdentityDocument,
)
from afritech.novaid.persistence.document_codec import (
    DOCUMENT_CODEC_TYPE,
    DOCUMENT_CODEC_VERSION,
    FORBIDDEN_DOCUMENT_CODEC_FIELDS,
    DocumentPersistenceDecodingError,
    DocumentPersistenceEncodingError,
    decode_identity_document,
    decode_identity_document_json,
    encode_identity_document,
    encode_identity_document_json,
)


def uid() -> str:
    return str(uuid4())


def first_enum_member(enum_type: type[Enum]) -> Enum:
    members = tuple(enum_type)

    if not members:
        raise AssertionError(
            f"{enum_type.__name__} has no members."
        )

    preferred_names = (
        "PASSPORT",
        "CAPTURED",
        "PENDING",
        "FRONT",
        "IMAGE_JPEG",
        "JPEG",
        "UNKNOWN",
    )

    for name in preferred_names:
        member = enum_type.__members__.get(name)

        if member is not None:
            return member

    return members[0]


def sample_value(
    field_name: str,
    annotation: object,
) -> object:
    origin = get_origin(annotation)
    arguments = get_args(annotation)

    if origin is not None:
        if origin is tuple:
            return ()

        if origin is list:
            return []

        if origin is dict:
            return {}

        if type(None) in arguments:
            non_none = tuple(
                item
                for item in arguments
                if item is not type(None)
            )

            if not non_none:
                return None

            if field_name in {
                "issued_at",
                "expires_at",
                "verified_at",
            }:
                return None

            return sample_value(
                field_name,
                non_none[0],
            )

    if annotation is str:
        values = {
            "document_id": uid(),
            "tenant_id": uid(),
            "identity_id": uid(),
            "issuing_country": "AU",
            "issuing_country_code": "AU",
            "nationality_code": "AU",
            "country_code": "AU",
            "document_number_reference": (
                "secure://document-number/reference"
            ),
            "capture_reference": (
                "secure://document-capture/reference"
            ),
            "checksum": "a" * 64,
            "media_type": "IMAGE_JPEG",
        }

        return values.get(
            field_name,
            f"{field_name}-value",
        )

    if annotation is int:
        if field_name == "capture_order":
            return 0

        return 1

    if annotation is float:
        return 0.95

    if annotation is bool:
        return False

    if annotation is datetime:
        return datetime(
            2026,
            8,
            1,
            1,
            0,
            0,
            tzinfo=timezone.utc,
        )

    if annotation is date:
        if field_name == "expires_at":
            return date(2030, 1, 1)

        return date(2025, 1, 1)

    if (
        isinstance(annotation, type)
        and issubclass(annotation, Enum)
    ):
        return first_enum_member(annotation)

    if (
        isinstance(annotation, type)
        and is_dataclass(annotation)
    ):
        return build_dataclass(annotation)

    return None


def build_dataclass(model: type[Any]) -> Any:
    hints = get_type_hints(model)
    values: dict[str, object] = {}

    for item in fields(model):
        if item.default is not MISSING:
            continue

        if item.default_factory is not MISSING:
            continue

        annotation = hints.get(
            item.name,
            Any,
        )
        value = sample_value(
            item.name,
            annotation,
        )

        if value is None:
            origin = get_origin(annotation)
            arguments = get_args(annotation)

            allows_none = (
                type(None) in arguments
                if arguments
                else False
            )

            if not allows_none:
                raise AssertionError(
                    "No sample value available for "
                    f"{model.__name__}.{item.name}: "
                    f"{annotation!r}"
                )

        values[item.name] = value

    return model(**values)


def document() -> IdentityDocument:
    item = build_dataclass(IdentityDocument)

    assert isinstance(item, IdentityDocument)
    return item


def walk_values(value: object):
    yield value

    if isinstance(value, dict):
        for nested in value.values():
            yield from walk_values(nested)

    elif isinstance(value, (list, tuple)):
        for nested in value:
            yield from walk_values(nested)


def test_document_models_are_dataclasses() -> None:
    assert is_dataclass(DocumentCaptureReference)
    assert is_dataclass(DocumentVerificationEvidence)
    assert is_dataclass(IdentityDocument)


def test_identity_document_round_trip() -> None:
    current = document()

    payload = encode_identity_document(current)
    restored = decode_identity_document(payload)

    assert restored == current
    assert restored is not current


def test_identity_document_json_round_trip() -> None:
    current = document()

    payload = encode_identity_document_json(current)
    restored = decode_identity_document_json(payload)

    assert restored == current


def test_json_encoding_is_deterministic() -> None:
    current = document()

    first = encode_identity_document_json(current)
    second = encode_identity_document_json(current)

    assert first == second
    assert json.loads(first) == json.loads(second)


def test_codec_envelope_is_versioned() -> None:
    payload = encode_identity_document(document())

    assert payload["codec_version"] == DOCUMENT_CODEC_VERSION
    assert payload["record_type"] == DOCUMENT_CODEC_TYPE
    assert "payload" in payload


def test_codec_preserves_typed_values() -> None:
    current = document()
    restored = decode_identity_document(
        encode_identity_document(current)
    )

    hints = get_type_hints(IdentityDocument)

    for item in fields(IdentityDocument):
        expected = getattr(current, item.name)
        actual = getattr(restored, item.name)

        assert actual == expected

        annotation = hints.get(item.name)

        if (
            isinstance(annotation, type)
            and issubclass(annotation, Enum)
        ):
            assert type(actual) is type(expected)


def test_codec_output_is_json_safe() -> None:
    payload = encode_identity_document(document())

    serialized = json.dumps(
        payload,
        allow_nan=False,
    )

    assert isinstance(serialized, str)

    forbidden_runtime_types = (
        datetime,
        date,
        Enum,
        IdentityDocument,
        DocumentCaptureReference,
        DocumentVerificationEvidence,
    )

    assert not any(
        isinstance(value, forbidden_runtime_types)
        for value in walk_values(payload)
    )


def test_unknown_envelope_fields_fail_closed() -> None:
    payload = encode_identity_document(document())
    payload["unexpected"] = True

    with pytest.raises(
        DocumentPersistenceDecodingError,
        match="UNKNOWN_DOCUMENT_CODEC_ENVELOPE_FIELDS",
    ):
        decode_identity_document(payload)


def test_unknown_document_fields_fail_closed() -> None:
    payload = encode_identity_document(document())

    encoded_document = payload["payload"]

    assert isinstance(encoded_document, dict)

    encoded_fields = encoded_document["fields"]

    assert isinstance(encoded_fields, dict)

    encoded_fields["unexpected"] = "value"

    with pytest.raises(
        DocumentPersistenceDecodingError,
        match="UNKNOWN_DOCUMENT_PERSISTENCE_FIELDS",
    ):
        decode_identity_document(payload)


@pytest.mark.parametrize(
    "codec_version",
    (
        0,
        2,
        "1",
        None,
    ),
)
def test_unknown_codec_version_fails_closed(
    codec_version: object,
) -> None:
    payload = encode_identity_document(document())
    payload["codec_version"] = codec_version

    with pytest.raises(
        DocumentPersistenceDecodingError,
        match="UNSUPPORTED_DOCUMENT_CODEC_VERSION",
    ):
        decode_identity_document(payload)


def test_wrong_record_type_fails_closed() -> None:
    payload = encode_identity_document(document())
    payload["record_type"] = "UNKNOWN_RECORD"

    with pytest.raises(
        DocumentPersistenceDecodingError,
        match="INVALID_DOCUMENT_CODEC_RECORD_TYPE",
    ):
        decode_identity_document(payload)


@pytest.mark.parametrize(
    "payload",
    (
        "",
        "{",
        "[]",
        "null",
        '"text"',
    ),
)
def test_invalid_json_fails_closed(
    payload: str,
) -> None:
    with pytest.raises(
        DocumentPersistenceDecodingError,
    ):
        decode_identity_document_json(payload)


@pytest.mark.parametrize(
    "metadata",
    (
        {"raw_image": "base64"},
        {"provider_payload": {"decision": "PASS"}},
        {"nested": {"raw_selfie": "base64"}},
        {"items": [{"face_embedding": [0.1, 0.2]}]},
        {"raw_mrz": "P<AUS..."},
        {"barcode_payload": "raw"},
        {"api_key": "secret"},
        {"private_key": "secret"},
    ),
)
def test_raw_material_is_rejected_on_decode(
    metadata: dict[str, object],
) -> None:
    payload = encode_identity_document(document())
    payload["unsafe"] = metadata

    with pytest.raises(
        DocumentPersistenceDecodingError,
    ):
        decode_identity_document(payload)


def test_wrong_encoder_type_is_rejected() -> None:
    with pytest.raises(
        DocumentPersistenceEncodingError,
        match="IDENTITY_DOCUMENT_REQUIRED",
    ):
        encode_identity_document(
            object()  # type: ignore[arg-type]
        )


def test_wrong_json_decoder_type_is_rejected() -> None:
    with pytest.raises(
        DocumentPersistenceDecodingError,
        match="DOCUMENT_JSON_TEXT_REQUIRED",
    ):
        decode_identity_document_json(
            object()  # type: ignore[arg-type]
        )


def test_decoded_document_remains_immutable() -> None:
    restored = decode_identity_document(
        encode_identity_document(document())
    )

    first_field = fields(IdentityDocument)[0]

    with pytest.raises(FrozenInstanceError):
        setattr(
            restored,
            first_field.name,
            "changed",
        )


def test_forbidden_registry_covers_sensitive_material() -> None:
    expected = {
        "raw_image",
        "raw_document",
        "raw_selfie",
        "raw_video",
        "raw_mrz",
        "barcode_payload",
        "provider_payload",
        "face_embedding",
        "biometric_template",
        "api_key",
        "private_key",
        "access_token",
        "password",
    }

    assert expected.issubset(
        FORBIDDEN_DOCUMENT_CODEC_FIELDS
    )


def test_codec_does_not_use_pickle() -> None:
    import inspect

    from afritech.novaid.persistence import (
        document_codec,
    )

    source = inspect.getsource(document_codec)

    assert "pickle" not in source.lower()


def test_public_decoder_annotations_are_canonical() -> None:
    assert (
        signature(
            decode_identity_document
        ).return_annotation
        in {
            IdentityDocument,
            "IdentityDocument",
        }
    )

    assert (
        signature(
            decode_identity_document_json
        ).return_annotation
        in {
            IdentityDocument,
            "IdentityDocument",
        }
    )
