from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from inspect import signature
from uuid import uuid4

import pytest

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
from afritech.novaid.persistence.identity_verification_codec import (
    FORBIDDEN_VERIFICATION_CODEC_FIELDS,
    VERIFICATION_CODEC_TYPE,
    VERIFICATION_CODEC_VERSION,
    VERIFICATION_RECORD_FIELDS,
    VerificationPersistenceDecodingError,
    VerificationPersistenceEncodingError,
    decode_identity_verification_record,
    decode_identity_verification_record_json,
    encode_identity_verification_record,
    encode_identity_verification_record_json,
)


def uid() -> str:
    return str(uuid4())


def verification(
    **overrides: object,
) -> IdentityVerificationRecord:
    values: dict[str, object] = {
        "verification_id": uid(),
        "workflow_id": uid(),
        "tenant_id": uid(),
        "identity_id": uid(),
        "document_id": uid(),
        "document_type": IdentityDocumentType.PASSPORT,
        "purpose": BiometricPurpose.EKYC,
        "decision": IdentityVerificationDecision.VERIFIED,
        "assurance_level": AssuranceLevel.NID_AL2,
        "combined_score": 0.965,
        "ocr_score": 0.97,
        "authenticity_score": 0.96,
        "selfie_match_score": 0.95,
        "liveness_score": 0.98,
        "ocr_extraction_id": uid(),
        "authenticity_assessment_id": uid(),
        "selfie_match_id": uid(),
        "policy_version": (
            "identity-verification-policy-v1"
        ),
        "document_version": 5,
        "verified_at": datetime(
            2026,
            8,
            1,
            6,
            30,
            0,
            tzinfo=timezone.utc,
        ),
        "reason_codes": (
            "ALL_CONTROLS_SATISFIED",
        ),
        "metadata": {
            "channel": "MOBILE_APP",
            "region": "AU",
        },
    }
    values.update(overrides)

    return IdentityVerificationRecord(**values)


def test_verification_record_round_trip() -> None:
    current = verification()

    payload = encode_identity_verification_record(
        current
    )
    restored = decode_identity_verification_record(
        payload
    )

    assert restored == current
    assert restored is not current


def test_verification_record_json_round_trip() -> None:
    current = verification()

    payload = encode_identity_verification_record_json(
        current
    )
    restored = decode_identity_verification_record_json(
        payload
    )

    assert restored == current


def test_json_encoding_is_deterministic() -> None:
    current = verification()

    first = encode_identity_verification_record_json(
        current
    )
    second = encode_identity_verification_record_json(
        current
    )

    assert first == second
    assert json.loads(first) == json.loads(second)


def test_codec_envelope_is_versioned() -> None:
    payload = encode_identity_verification_record(
        verification()
    )

    assert payload["codec_version"] == VERIFICATION_CODEC_VERSION
    assert payload["record_type"] == VERIFICATION_CODEC_TYPE
    assert "payload" in payload


def test_payload_contains_exact_record_contract() -> None:
    envelope = encode_identity_verification_record(
        verification()
    )

    payload = envelope["payload"]

    assert isinstance(payload, dict)
    assert set(payload) == VERIFICATION_RECORD_FIELDS


def test_codec_preserves_enum_types() -> None:
    current = verification()

    restored = decode_identity_verification_record(
        encode_identity_verification_record(current)
    )

    assert (
        restored.document_type
        is IdentityDocumentType.PASSPORT
    )
    assert restored.purpose is BiometricPurpose.EKYC
    assert (
        restored.decision
        is IdentityVerificationDecision.VERIFIED
    )
    assert (
        restored.assurance_level
        is AssuranceLevel.NID_AL2
    )


def test_codec_preserves_component_scores() -> None:
    current = verification()

    restored = decode_identity_verification_record(
        encode_identity_verification_record(current)
    )

    assert restored.combined_score == 0.965
    assert restored.ocr_score == 0.97
    assert restored.authenticity_score == 0.96
    assert restored.selfie_match_score == 0.95
    assert restored.liveness_score == 0.98


def test_codec_preserves_evidence_references() -> None:
    current = verification()

    restored = decode_identity_verification_record(
        encode_identity_verification_record(current)
    )

    assert (
        restored.ocr_extraction_id
        == current.ocr_extraction_id
    )
    assert (
        restored.authenticity_assessment_id
        == current.authenticity_assessment_id
    )
    assert (
        restored.selfie_match_id
        == current.selfie_match_id
    )


def test_codec_preserves_timezone_aware_datetime() -> None:
    current = verification()

    restored = decode_identity_verification_record(
        encode_identity_verification_record(current)
    )

    assert restored.verified_at == current.verified_at
    assert restored.verified_at.tzinfo is not None


def test_codec_preserves_reason_code_tuple() -> None:
    current = verification(
        reason_codes=(
            "ALL_CONTROLS_SATISFIED",
            "SECONDARY_CONTROL",
        )
    )

    restored = decode_identity_verification_record(
        encode_identity_verification_record(current)
    )

    assert restored.reason_codes == (
        "ALL_CONTROLS_SATISFIED",
        "SECONDARY_CONTROL",
    )
    assert isinstance(restored.reason_codes, tuple)


def test_metadata_is_defensively_reconstructed() -> None:
    current = verification()
    payload = encode_identity_verification_record(
        current
    )

    restored = decode_identity_verification_record(
        payload
    )

    assert restored.metadata == current.metadata
    assert restored.metadata is not current.metadata


def test_codec_output_is_json_safe() -> None:
    payload = encode_identity_verification_record(
        verification()
    )

    encoded = json.dumps(
        payload,
        allow_nan=False,
    )

    assert isinstance(encoded, str)


def test_unknown_envelope_fields_fail_closed() -> None:
    payload = encode_identity_verification_record(
        verification()
    )
    payload["unexpected"] = True

    with pytest.raises(
        VerificationPersistenceDecodingError,
        match=(
            "UNKNOWN_VERIFICATION_CODEC_ENVELOPE_FIELDS"
        ),
    ):
        decode_identity_verification_record(payload)


def test_unknown_record_fields_fail_closed() -> None:
    envelope = encode_identity_verification_record(
        verification()
    )
    payload = envelope["payload"]

    assert isinstance(payload, dict)
    payload["unexpected"] = "value"

    with pytest.raises(
        VerificationPersistenceDecodingError,
        match=(
            "UNKNOWN_VERIFICATION_PERSISTENCE_FIELDS"
        ),
    ):
        decode_identity_verification_record(envelope)


def test_missing_record_fields_fail_closed() -> None:
    envelope = encode_identity_verification_record(
        verification()
    )
    payload = envelope["payload"]

    assert isinstance(payload, dict)
    del payload["policy_version"]

    with pytest.raises(
        VerificationPersistenceDecodingError,
        match=(
            "MISSING_VERIFICATION_PERSISTENCE_FIELDS"
        ),
    ):
        decode_identity_verification_record(envelope)


@pytest.mark.parametrize(
    "codec_version",
    (
        0,
        2,
        "1",
        None,
    ),
)
def test_unknown_codec_versions_fail_closed(
    codec_version: object,
) -> None:
    payload = encode_identity_verification_record(
        verification()
    )
    payload["codec_version"] = codec_version

    with pytest.raises(
        VerificationPersistenceDecodingError,
        match=(
            "UNSUPPORTED_VERIFICATION_CODEC_VERSION"
        ),
    ):
        decode_identity_verification_record(payload)


def test_wrong_record_type_fails_closed() -> None:
    payload = encode_identity_verification_record(
        verification()
    )
    payload["record_type"] = "UNKNOWN_RECORD"

    with pytest.raises(
        VerificationPersistenceDecodingError,
        match=(
            "INVALID_VERIFICATION_CODEC_RECORD_TYPE"
        ),
    ):
        decode_identity_verification_record(payload)


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
        VerificationPersistenceDecodingError,
    ):
        decode_identity_verification_record_json(
            payload
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "combined_score",
        "ocr_score",
        "authenticity_score",
        "selfie_match_score",
        "liveness_score",
    ),
)
@pytest.mark.parametrize(
    "invalid_value",
    (
        -0.01,
        1.01,
        True,
        "0.95",
    ),
)
def test_invalid_scores_fail_closed(
    field_name: str,
    invalid_value: object,
) -> None:
    envelope = encode_identity_verification_record(
        verification()
    )
    payload = envelope["payload"]

    assert isinstance(payload, dict)
    payload[field_name] = invalid_value

    with pytest.raises(
        VerificationPersistenceDecodingError,
    ):
        decode_identity_verification_record(envelope)


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    (
        ("document_type", "INVALID_DOCUMENT"),
        ("purpose", "INVALID_PURPOSE"),
        ("decision", "INVALID_DECISION"),
        ("assurance_level", "INVALID_ASSURANCE"),
    ),
)
def test_invalid_enums_fail_closed(
    field_name: str,
    invalid_value: str,
) -> None:
    envelope = encode_identity_verification_record(
        verification()
    )
    payload = envelope["payload"]

    assert isinstance(payload, dict)
    payload[field_name] = invalid_value

    with pytest.raises(
        VerificationPersistenceDecodingError,
    ):
        decode_identity_verification_record(envelope)


@pytest.mark.parametrize(
    "verified_at",
    (
        "not-a-date",
        "2026-08-01T06:30:00",
        None,
    ),
)
def test_invalid_verification_datetime_fails_closed(
    verified_at: object,
) -> None:
    envelope = encode_identity_verification_record(
        verification()
    )
    payload = envelope["payload"]

    assert isinstance(payload, dict)
    payload["verified_at"] = verified_at

    with pytest.raises(
        VerificationPersistenceDecodingError,
    ):
        decode_identity_verification_record(envelope)


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
    envelope = encode_identity_verification_record(
        verification()
    )
    payload = envelope["payload"]

    assert isinstance(payload, dict)
    payload["metadata"] = metadata

    with pytest.raises(
        VerificationPersistenceDecodingError,
        match=(
            "RAW_VERIFICATION_PERSISTENCE_MATERIAL_FORBIDDEN"
        ),
    ):
        decode_identity_verification_record(envelope)


@pytest.mark.parametrize(
    "metadata",
    (
        {"raw_image": "base64"},
        {"provider_payload": {"decision": "PASS"}},
        {"nested": {"raw_selfie": "base64"}},
        {"items": [{"face_embedding": [0.1, 0.2]}]},
        {"api_key": "secret"},
    ),
)
def test_raw_material_is_rejected_on_encode(
    metadata: dict[str, object],
) -> None:
    current = verification()

    object.__setattr__(
        current,
        "metadata",
        metadata,
    )

    with pytest.raises(
        VerificationPersistenceEncodingError,
        match=(
            "RAW_VERIFICATION_PERSISTENCE_MATERIAL_FORBIDDEN"
        ),
    ):
        encode_identity_verification_record(current)


def test_wrong_encoder_type_is_rejected() -> None:
    with pytest.raises(
        VerificationPersistenceEncodingError,
        match="IDENTITY_VERIFICATION_RECORD_REQUIRED",
    ):
        encode_identity_verification_record(
            object()  # type: ignore[arg-type]
        )


def test_wrong_json_decoder_type_is_rejected() -> None:
    with pytest.raises(
        VerificationPersistenceDecodingError,
        match="VERIFICATION_JSON_TEXT_REQUIRED",
    ):
        decode_identity_verification_record_json(
            object()  # type: ignore[arg-type]
        )


def test_decoded_record_remains_immutable() -> None:
    restored = decode_identity_verification_record(
        encode_identity_verification_record(
            verification()
        )
    )

    with pytest.raises(FrozenInstanceError):
        restored.decision = (  # type: ignore[misc]
            IdentityVerificationDecision.REJECTED
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
        FORBIDDEN_VERIFICATION_CODEC_FIELDS
    )


def test_codec_does_not_use_unsafe_deserialization() -> None:
    import inspect

    from afritech.novaid.persistence import (
        identity_verification_codec,
    )

    source = inspect.getsource(
        identity_verification_codec
    ).lower()

    for forbidden in (
        "import pickle",
        "from pickle",
        "eval(",
        "exec(",
        "__import__(",
    ):
        assert forbidden not in source


def test_public_decoder_annotations_are_canonical() -> None:
    assert (
        signature(
            decode_identity_verification_record
        ).return_annotation
        in {
            IdentityVerificationRecord,
            "IdentityVerificationRecord",
        }
    )

    assert (
        signature(
            decode_identity_verification_record_json
        ).return_annotation
        in {
            IdentityVerificationRecord,
            "IdentityVerificationRecord",
        }
    )
