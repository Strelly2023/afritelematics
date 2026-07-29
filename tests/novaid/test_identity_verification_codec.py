from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum

import pytest

from afritech.novaid.domain import (
    IdentityVerificationEvidence,
    IdentityVerificationOutcomeEvent,
    IdentityVerificationRecord,
)
from afritech.novaid.persistence.identity_verification_codec import (
    decode_identity_verification_payload,
    encode_identity_verification_evidence,
    encode_identity_verification_outcome_event,
    encode_identity_verification_payload,
    encode_identity_verification_record,
    identity_verification_evidence_from_payload,
    identity_verification_outcome_event_from_payload,
    identity_verification_record_from_payload,
)


class SampleDecision(str, Enum):
    PASS = "PASS"


@dataclass(frozen=True)
class NestedSample:
    value: str
    occurred_at: datetime


@dataclass(frozen=True)
class CodecSample:
    identifier: str
    decision: SampleDecision
    nested: NestedSample
    reason_codes: tuple[str, ...]
    tags: frozenset[str]
    metadata: dict[str, object]


def sample() -> CodecSample:
    return CodecSample(
        identifier="verification-1",
        decision=SampleDecision.PASS,
        nested=NestedSample(
            value="nested-value",
            occurred_at=datetime(
                2026,
                7,
                29,
                1,
                2,
                3,
                tzinfo=UTC,
            ),
        ),
        reason_codes=(
            "CONTROLS_SATISFIED",
            "PROVIDER_EVALUATED",
        ),
        tags=frozenset(
            {
                "governed",
                "replayable",
            }
        ),
        metadata={
            "source": "codec-test",
            "nested": {
                "policy": "identity-verification-v1",
            },
        },
    )


def test_generic_dataclass_round_trip() -> None:
    original = sample()

    encoded = encode_identity_verification_payload(
        original
    )
    restored = decode_identity_verification_payload(
        encoded,
        CodecSample,
    )

    assert restored == original


def test_codec_output_is_canonical_json() -> None:
    original = sample()

    first = encode_identity_verification_payload(
        original
    )
    second = encode_identity_verification_payload(
        original
    )

    assert first == second
    assert " " not in first
    assert json.loads(first)["decision"] == "PASS"


def test_codec_restores_enum_datetime_tuple_and_frozenset() -> None:
    restored = decode_identity_verification_payload(
        encode_identity_verification_payload(
            sample()
        ),
        CodecSample,
    )

    assert restored.decision is SampleDecision.PASS
    assert isinstance(
        restored.nested.occurred_at,
        datetime,
    )
    assert isinstance(restored.reason_codes, tuple)
    assert isinstance(restored.tags, frozenset)


@pytest.mark.parametrize(
    "payload",
    (
        {"raw_image": "base64-document"},
        {"metadata": {"raw_selfie": "base64-selfie"}},
        {"nested": {"embedding": [0.1, 0.2]}},
        {"provider_payload": {"result": "secret"}},
        {"items": [{"document_bytes": "binary"}]},
        {"metadata": {"private_key": "secret"}},
        {"metadata": {"access_token": "secret"}},
    ),
)
def test_raw_verification_material_is_rejected_on_encode(
    payload: dict[str, object],
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "RAW_IDENTITY_VERIFICATION_MATERIAL_FORBIDDEN"
        ),
    ):
        encode_identity_verification_payload(payload)


@pytest.mark.parametrize(
    "payload",
    (
        {"raw_video": "binary"},
        {"metadata": {"face_template": "template"}},
        {"metadata": {"api_key": "secret"}},
        {"items": [{"raw_provider_response": {}}]},
    ),
)
def test_raw_verification_material_is_rejected_on_decode(
    payload: dict[str, object],
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "RAW_IDENTITY_VERIFICATION_MATERIAL_FORBIDDEN"
        ),
    ):
        decode_identity_verification_payload(
            json.dumps(payload),
            CodecSample,
        )


def test_invalid_json_fails_closed() -> None:
    with pytest.raises(
        ValueError,
        match="INVALID_IDENTITY_VERIFICATION_JSON",
    ):
        decode_identity_verification_payload(
            "{not-json",
            CodecSample,
        )


def test_unknown_fields_fail_closed() -> None:
    payload = json.loads(
        encode_identity_verification_payload(
            sample()
        )
    )
    payload["unexpected"] = "value"

    with pytest.raises(
        ValueError,
        match="UNKNOWN_IDENTITY_VERIFICATION_FIELDS",
    ):
        decode_identity_verification_payload(
            payload,
            CodecSample,
        )


def test_wrong_public_encoder_types_are_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="IDENTITY_VERIFICATION_EVIDENCE_REQUIRED",
    ):
        encode_identity_verification_evidence(sample())  # type: ignore[arg-type]

    with pytest.raises(
        TypeError,
        match="IDENTITY_VERIFICATION_RECORD_REQUIRED",
    ):
        encode_identity_verification_record(sample())  # type: ignore[arg-type]

    with pytest.raises(
        TypeError,
        match=(
            "IDENTITY_VERIFICATION_OUTCOME_EVENT_REQUIRED"
        ),
    ):
        encode_identity_verification_outcome_event(
            sample()  # type: ignore[arg-type]
        )


def test_public_decoder_return_annotations_are_canonical() -> None:
    assert (
        identity_verification_evidence_from_payload
        .__annotations__["return"]
        in {
            "IdentityVerificationEvidence",
            IdentityVerificationEvidence,
        }
    )

    assert (
        identity_verification_record_from_payload
        .__annotations__["return"]
        in {
            "IdentityVerificationRecord",
            IdentityVerificationRecord,
        }
    )

    assert (
        identity_verification_outcome_event_from_payload
        .__annotations__["return"]
        in {
            "IdentityVerificationOutcomeEvent",
            IdentityVerificationOutcomeEvent,
        }
    )
