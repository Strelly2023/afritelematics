from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Mapping

from afritech.novaid.domain import (
    AssuranceLevel,
    AuthenticationStrength,
    BiometricConsent,
    BiometricConsentStatus,
    BiometricEnrollment,
    BiometricEnrollmentStatus,
    BiometricPurpose,
    BiometricType,
    CaptureChannel,
    CaptureDecision,
    CaptureDevice,
    CaptureEnvironment,
    CaptureLighting,
    CaptureQuality,
    FaceAuthenticationDecision,
    FaceAuthenticationRecord,
    FaceVerificationDecision,
    FaceVerificationRecord,
    LivenessAssessmentRecord,
    LivenessDecision,
    LivenessMode,
    PresentationAttackType,
)


FORBIDDEN_BIOMETRIC_FIELDS = frozenset(
    {
        "raw_image",
        "raw_video",
        "video",
        "frames",
        "embedding",
        "embeddings",
        "feature_vector",
        "feature_vectors",
        "template",
        "biometric_template",
        "camera_buffer",
        "provider_secret",
        "api_key",
        "private_key",
    }
)


def _row_value(
    row: Mapping[str, Any],
    key: str,
    default: Any = None,
) -> Any:
    getter = getattr(row, "get", None)

    if callable(getter):
        return getter(key, default)

    keys = row.keys() if hasattr(row, "keys") else ()
    return row[key] if key in keys else default


def _parse_datetime(
    value: datetime | str | None,
) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if not isinstance(value, str):
        raise ValueError("INVALID_BIOMETRIC_DATETIME")

    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            "INVALID_BIOMETRIC_DATETIME"
        ) from exc


def _datetime_text(
    value: datetime | None,
) -> str | None:
    return value.isoformat() if value is not None else None


def _json_payload(
    value: Any,
    *,
    default: Any,
) -> Any:
    if value is None:
        return default

    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "INVALID_BIOMETRIC_JSON"
            ) from exc

    return value


def _assert_safe_payload(
    payload: Mapping[str, Any],
) -> None:
    forbidden = {
        str(key).strip().lower()
        for key in payload
    } & FORBIDDEN_BIOMETRIC_FIELDS

    if forbidden:
        raise ValueError(
            "RAW_BIOMETRIC_MATERIAL_FORBIDDEN"
        )


def encode_metadata(
    metadata: Mapping[str, Any],
) -> str:
    payload = dict(metadata)
    _assert_safe_payload(payload)

    return json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
    )


def decode_metadata(
    value: Any,
) -> dict[str, Any]:
    payload = _json_payload(
        value,
        default={},
    )

    if not isinstance(payload, dict):
        raise ValueError(
            "INVALID_BIOMETRIC_METADATA"
        )

    _assert_safe_payload(payload)
    return dict(payload)


def encode_reason_codes(
    reason_codes: tuple[str, ...],
) -> str:
    return json.dumps(
        list(reason_codes),
        separators=(",", ":"),
    )


def decode_reason_codes(
    value: Any,
) -> tuple[str, ...]:
    payload = _json_payload(
        value,
        default=[],
    )

    if not isinstance(payload, list):
        raise ValueError(
            "INVALID_BIOMETRIC_REASON_CODES"
        )

    return tuple(
        str(code).strip().upper()
        for code in payload
        if str(code).strip()
    )


def encode_attack_types(
    values: frozenset[PresentationAttackType],
) -> str:
    return json.dumps(
        sorted(item.value for item in values),
        separators=(",", ":"),
    )


def decode_attack_types(
    value: Any,
) -> frozenset[PresentationAttackType]:
    payload = _json_payload(
        value,
        default=[],
    )

    if not isinstance(payload, list):
        raise ValueError(
            "INVALID_PRESENTATION_ATTACK_TYPES"
        )

    return frozenset(
        PresentationAttackType(item)
        for item in payload
    )


def encode_capture_device(
    device: CaptureDevice | None,
) -> str | None:
    if device is None:
        return None

    payload = {
        "device_reference": device.device_reference,
        "channel": device.channel.value,
        "platform": device.platform,
        "operating_system": device.operating_system,
        "application_version": device.application_version,
        "camera_facing": device.camera_facing,
        "integrity_verified": device.integrity_verified,
        "hardware_backed_key_available": (
            device.hardware_backed_key_available
        ),
    }

    return json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
    )


def decode_capture_device(
    value: Any,
) -> CaptureDevice | None:
    if value is None:
        return None

    payload = _json_payload(
        value,
        default=None,
    )

    if payload is None:
        return None

    if not isinstance(payload, dict):
        raise ValueError(
            "INVALID_CAPTURE_DEVICE"
        )

    _assert_safe_payload(payload)

    return CaptureDevice(
        device_reference=payload["device_reference"],
        channel=CaptureChannel(payload["channel"]),
        platform=payload.get("platform"),
        operating_system=payload.get(
            "operating_system"
        ),
        application_version=payload.get(
            "application_version"
        ),
        camera_facing=payload.get("camera_facing"),
        integrity_verified=bool(
            payload.get("integrity_verified", False)
        ),
        hardware_backed_key_available=bool(
            payload.get(
                "hardware_backed_key_available",
                False,
            )
        ),
    )


def encode_capture_environment(
    environment: CaptureEnvironment | None,
) -> str | None:
    if environment is None:
        return None

    payload = {
        "lighting": environment.lighting.value,
        "network_reference": (
            environment.network_reference
        ),
        "country_code": environment.country_code,
        "location_accuracy_metres": (
            environment.location_accuracy_metres
        ),
        "vpn_detected": environment.vpn_detected,
        "emulator_detected": (
            environment.emulator_detected
        ),
        "rooted_or_jailbroken": (
            environment.rooted_or_jailbroken
        ),
    }

    return json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
    )


def decode_capture_environment(
    value: Any,
) -> CaptureEnvironment | None:
    if value is None:
        return None

    payload = _json_payload(
        value,
        default=None,
    )

    if payload is None:
        return None

    if not isinstance(payload, dict):
        raise ValueError(
            "INVALID_CAPTURE_ENVIRONMENT"
        )

    _assert_safe_payload(payload)

    return CaptureEnvironment(
        lighting=CaptureLighting(
            payload.get(
                "lighting",
                CaptureLighting.UNKNOWN.value,
            )
        ),
        network_reference=payload.get(
            "network_reference"
        ),
        country_code=payload.get("country_code"),
        location_accuracy_metres=payload.get(
            "location_accuracy_metres"
        ),
        vpn_detected=bool(
            payload.get("vpn_detected", False)
        ),
        emulator_detected=bool(
            payload.get("emulator_detected", False)
        ),
        rooted_or_jailbroken=bool(
            payload.get(
                "rooted_or_jailbroken",
                False,
            )
        ),
    )


def encode_capture_quality(
    quality: CaptureQuality | None,
) -> str | None:
    if quality is None:
        return None

    payload = {
        "overall_score": quality.overall_score,
        "face_detected": quality.face_detected,
        "single_subject_detected": (
            quality.single_subject_detected
        ),
        "sharpness_score": quality.sharpness_score,
        "illumination_score": (
            quality.illumination_score
        ),
        "pose_score": quality.pose_score,
        "occlusion_score": quality.occlusion_score,
        "minimum_required_score": (
            quality.minimum_required_score
        ),
        "decision": quality.decision.value,
        "reason_codes": list(
            quality.reason_codes
        ),
    }

    return json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
    )


def decode_capture_quality(
    value: Any,
) -> CaptureQuality | None:
    if value is None:
        return None

    payload = _json_payload(
        value,
        default=None,
    )

    if payload is None:
        return None

    if not isinstance(payload, dict):
        raise ValueError(
            "INVALID_CAPTURE_QUALITY"
        )

    _assert_safe_payload(payload)

    return CaptureQuality(
        overall_score=float(
            payload["overall_score"]
        ),
        face_detected=bool(
            payload["face_detected"]
        ),
        single_subject_detected=bool(
            payload["single_subject_detected"]
        ),
        sharpness_score=payload.get(
            "sharpness_score"
        ),
        illumination_score=payload.get(
            "illumination_score"
        ),
        pose_score=payload.get("pose_score"),
        occlusion_score=payload.get(
            "occlusion_score"
        ),
        minimum_required_score=float(
            payload.get(
                "minimum_required_score",
                0.70,
            )
        ),
        decision=CaptureDecision(
            payload.get(
                "decision",
                CaptureDecision.ACCEPT.value,
            )
        ),
        reason_codes=tuple(
            payload.get("reason_codes", ())
        ),
    )


def biometric_consent_from_row(
    row: Mapping[str, Any],
) -> BiometricConsent:
    granted_at = _parse_datetime(
        _row_value(row, "granted_at")
    )

    if granted_at is None:
        raise ValueError(
            "BIOMETRIC_CONSENT_GRANTED_AT_REQUIRED"
        )

    return BiometricConsent(
        consent_id=str(row["consent_id"]),
        tenant_id=str(row["tenant_id"]),
        identity_id=str(row["identity_id"]),
        purpose=BiometricPurpose(
            row["purpose"]
        ),
        policy_version=str(
            row["policy_version"]
        ),
        granted_at=granted_at,
        status=BiometricConsentStatus(
            _row_value(
                row,
                "status",
                BiometricConsentStatus.ACTIVE.value,
            )
        ),
        expires_at=_parse_datetime(
            _row_value(row, "expires_at")
        ),
        revoked_at=_parse_datetime(
            _row_value(row, "revoked_at")
        ),
        capture_notice_version=_row_value(
            row,
            "capture_notice_version",
        ),
        lawful_basis_reference=_row_value(
            row,
            "lawful_basis_reference",
        ),
        metadata=decode_metadata(
            _row_value(row, "metadata")
        ),
    )


def biometric_enrollment_from_row(
    row: Mapping[str, Any],
) -> BiometricEnrollment:
    created_at = _parse_datetime(
        _row_value(row, "created_at")
    )
    updated_at = _parse_datetime(
        _row_value(row, "updated_at")
    )

    if created_at is None or updated_at is None:
        raise ValueError(
            "BIOMETRIC_ENROLLMENT_TIMESTAMPS_REQUIRED"
        )

    return BiometricEnrollment(
        enrollment_id=str(row["enrollment_id"]),
        tenant_id=str(row["tenant_id"]),
        identity_id=str(row["identity_id"]),
        biometric_type=BiometricType(
            row["biometric_type"]
        ),
        purpose=BiometricPurpose(
            row["purpose"]
        ),
        consent_id=str(row["consent_id"]),
        template_reference=str(
            row["template_reference"]
        ),
        provider_reference=str(
            row["provider_reference"]
        ),
        algorithm_version=str(
            row["algorithm_version"]
        ),
        status=BiometricEnrollmentStatus(
            row["status"]
        ),
        capture_device=decode_capture_device(
            _row_value(row, "capture_device")
        ),
        capture_environment=(
            decode_capture_environment(
                _row_value(
                    row,
                    "capture_environment",
                )
            )
        ),
        capture_quality=decode_capture_quality(
            _row_value(row, "capture_quality")
        ),
        enrolled_at=_parse_datetime(
            _row_value(row, "enrolled_at")
        ),
        expires_at=_parse_datetime(
            _row_value(row, "expires_at")
        ),
        revoked_at=_parse_datetime(
            _row_value(row, "revoked_at")
        ),
        created_at=created_at,
        updated_at=updated_at,
        version=int(row["version"]),
        metadata=decode_metadata(
            _row_value(row, "metadata")
        ),
    )


def face_verification_from_row(
    row: Mapping[str, Any],
) -> FaceVerificationRecord:
    verified_at = _parse_datetime(
        _row_value(row, "verified_at")
    )

    if verified_at is None:
        raise ValueError(
            "FACE_VERIFICATION_TIMESTAMP_REQUIRED"
        )

    device = decode_capture_device(
        _row_value(row, "capture_device")
    )
    environment = decode_capture_environment(
        _row_value(row, "capture_environment")
    )
    quality = decode_capture_quality(
        _row_value(row, "capture_quality")
    )

    if (
        device is None
        or environment is None
        or quality is None
    ):
        raise ValueError(
            "FACE_VERIFICATION_CAPTURE_REQUIRED"
        )

    return FaceVerificationRecord(
        verification_id=str(
            row["verification_id"]
        ),
        tenant_id=str(row["tenant_id"]),
        identity_id=str(row["identity_id"]),
        enrollment_id=str(
            row["enrollment_id"]
        ),
        consent_id=str(row["consent_id"]),
        purpose=BiometricPurpose(
            row["purpose"]
        ),
        decision=FaceVerificationDecision(
            row["decision"]
        ),
        similarity_score=float(
            row["similarity_score"]
        ),
        match_threshold=float(
            row["match_threshold"]
        ),
        manual_review_threshold=float(
            row["manual_review_threshold"]
        ),
        provider_reference=str(
            row["provider_reference"]
        ),
        algorithm_version=str(
            row["algorithm_version"]
        ),
        capture_device=device,
        capture_environment=environment,
        capture_quality=quality,
        verified_at=verified_at,
        version=int(
            _row_value(row, "version", 1)
        ),
        reason_codes=decode_reason_codes(
            _row_value(row, "reason_codes")
        ),
        metadata=decode_metadata(
            _row_value(row, "metadata")
        ),
    )


def face_authentication_from_row(
    row: Mapping[str, Any],
) -> FaceAuthenticationRecord:
    authenticated_at = _parse_datetime(
        _row_value(row, "authenticated_at")
    )

    if authenticated_at is None:
        raise ValueError(
            "FACE_AUTHENTICATION_TIMESTAMP_REQUIRED"
        )

    return FaceAuthenticationRecord(
        authentication_id=str(
            row["authentication_id"]
        ),
        tenant_id=str(row["tenant_id"]),
        identity_id=str(row["identity_id"]),
        verification_id=str(
            row["verification_id"]
        ),
        enrollment_id=str(
            row["enrollment_id"]
        ),
        purpose=BiometricPurpose(
            row["purpose"]
        ),
        decision=FaceAuthenticationDecision(
            row["decision"]
        ),
        verification_decision=(
            FaceVerificationDecision(
                row["verification_decision"]
            )
        ),
        risk_score=float(row["risk_score"]),
        authentication_strength=(
            AuthenticationStrength(
                row["authentication_strength"]
            )
        ),
        current_assurance_level=AssuranceLevel(
            row["current_assurance_level"]
        ),
        required_assurance_level=AssuranceLevel(
            row["required_assurance_level"]
        ),
        authenticated_at=authenticated_at,
        reason_codes=decode_reason_codes(
            _row_value(row, "reason_codes")
        ),
        metadata=decode_metadata(
            _row_value(row, "metadata")
        ),
    )


def liveness_assessment_from_row(
    row: Mapping[str, Any],
) -> LivenessAssessmentRecord:
    assessed_at = _parse_datetime(
        _row_value(row, "assessed_at")
    )

    if assessed_at is None:
        raise ValueError(
            "LIVENESS_ASSESSMENT_TIMESTAMP_REQUIRED"
        )

    device = decode_capture_device(
        _row_value(row, "capture_device")
    )
    environment = decode_capture_environment(
        _row_value(row, "capture_environment")
    )
    quality = decode_capture_quality(
        _row_value(row, "capture_quality")
    )

    if (
        device is None
        or environment is None
        or quality is None
    ):
        raise ValueError(
            "LIVENESS_CAPTURE_REQUIRED"
        )

    return LivenessAssessmentRecord(
        assessment_id=str(
            row["assessment_id"]
        ),
        tenant_id=str(row["tenant_id"]),
        identity_id=str(row["identity_id"]),
        purpose=BiometricPurpose(
            row["purpose"]
        ),
        decision=LivenessDecision(
            row["decision"]
        ),
        attempt_number=int(
            row["attempt_number"]
        ),
        mode=LivenessMode(row["mode"]),
        liveness_score=float(
            row["liveness_score"]
        ),
        presentation_attack_score=float(
            row["presentation_attack_score"]
        ),
        provider_reference=str(
            row["provider_reference"]
        ),
        algorithm_version=str(
            row["algorithm_version"]
        ),
        capture_device=device,
        capture_environment=environment,
        capture_quality=quality,
        assessed_at=assessed_at,
        detected_attack_types=(
            decode_attack_types(
                _row_value(
                    row,
                    "detected_attack_types",
                )
            )
        ),
        reason_codes=decode_reason_codes(
            _row_value(row, "reason_codes")
        ),
        metadata=decode_metadata(
            _row_value(row, "metadata")
        ),
    )


__all__ = [
    "FORBIDDEN_BIOMETRIC_FIELDS",
    "biometric_consent_from_row",
    "biometric_enrollment_from_row",
    "decode_attack_types",
    "decode_capture_device",
    "decode_capture_environment",
    "decode_capture_quality",
    "decode_metadata",
    "decode_reason_codes",
    "encode_attack_types",
    "encode_capture_device",
    "encode_capture_environment",
    "encode_capture_quality",
    "encode_metadata",
    "encode_reason_codes",
    "face_authentication_from_row",
    "face_verification_from_row",
    "liveness_assessment_from_row",
]
