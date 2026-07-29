from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum
from typing import Any

from .models import identifier, utcnow


class BiometricType(StrEnum):
    FACE = "FACE"
    FINGERPRINT = "FINGERPRINT"
    IRIS = "IRIS"
    VOICE = "VOICE"


class BiometricPurpose(StrEnum):
    ENROLLMENT = "ENROLLMENT"
    LOGIN = "LOGIN"
    STEP_UP = "STEP_UP"
    RECOVERY = "RECOVERY"
    EKYC = "EKYC"
    DOCUMENT_MATCH = "DOCUMENT_MATCH"


class BiometricEnrollmentStatus(StrEnum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class BiometricConsentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class CaptureChannel(StrEnum):
    MOBILE_APP = "MOBILE_APP"
    WEB_BROWSER = "WEB_BROWSER"
    KIOSK = "KIOSK"
    ASSISTED_DESK = "ASSISTED_DESK"
    API = "API"


class CaptureLighting(StrEnum):
    UNKNOWN = "UNKNOWN"
    LOW = "LOW"
    NORMAL = "NORMAL"
    BRIGHT = "BRIGHT"
    BACKLIT = "BACKLIT"


class CaptureDecision(StrEnum):
    ACCEPT = "ACCEPT"
    RECAPTURE = "RECAPTURE"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    REJECT = "REJECT"


BIOMETRIC_ENROLLMENT_TRANSITIONS: dict[
    BiometricEnrollmentStatus,
    frozenset[BiometricEnrollmentStatus],
] = {
    BiometricEnrollmentStatus.PENDING: frozenset(
        {
            BiometricEnrollmentStatus.ACTIVE,
            BiometricEnrollmentStatus.REVOKED,
            BiometricEnrollmentStatus.EXPIRED,
        }
    ),
    BiometricEnrollmentStatus.ACTIVE: frozenset(
        {
            BiometricEnrollmentStatus.SUSPENDED,
            BiometricEnrollmentStatus.REVOKED,
            BiometricEnrollmentStatus.EXPIRED,
        }
    ),
    BiometricEnrollmentStatus.SUSPENDED: frozenset(
        {
            BiometricEnrollmentStatus.ACTIVE,
            BiometricEnrollmentStatus.REVOKED,
            BiometricEnrollmentStatus.EXPIRED,
        }
    ),
    BiometricEnrollmentStatus.REVOKED: frozenset(),
    BiometricEnrollmentStatus.EXPIRED: frozenset(),
}


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


def _optional_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    normalized = value.strip()
    return normalized or None


def _validate_probability(
    value: float,
    error_code: str,
) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(error_code)

    normalized = float(value)

    if not 0.0 <= normalized <= 1.0:
        raise ValueError(error_code)

    return normalized


def _validate_period(
    start: datetime,
    end: datetime | None,
    error_code: str,
) -> None:
    if end is not None and end <= start:
        raise ValueError(error_code)


@dataclass(frozen=True)
class BiometricConsent:
    consent_id: str
    tenant_id: str
    identity_id: str
    purpose: BiometricPurpose
    policy_version: str
    granted_at: datetime
    status: BiometricConsentStatus = BiometricConsentStatus.ACTIVE
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    capture_notice_version: str | None = None
    lawful_basis_reference: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "consent_id",
            _required_text(
                self.consent_id,
                "BIOMETRIC_CONSENT_ID_REQUIRED",
            ),
        )
        object.__setattr__(
            self,
            "tenant_id",
            _required_text(
                self.tenant_id,
                "TENANT_ID_REQUIRED",
            ),
        )
        object.__setattr__(
            self,
            "identity_id",
            _required_text(
                self.identity_id,
                "IDENTITY_ID_REQUIRED",
            ),
        )
        object.__setattr__(
            self,
            "purpose",
            BiometricPurpose(self.purpose),
        )
        object.__setattr__(
            self,
            "policy_version",
            _required_text(
                self.policy_version,
                "BIOMETRIC_POLICY_VERSION_REQUIRED",
            ),
        )
        object.__setattr__(
            self,
            "status",
            BiometricConsentStatus(self.status),
        )
        object.__setattr__(
            self,
            "capture_notice_version",
            _optional_text(self.capture_notice_version),
        )
        object.__setattr__(
            self,
            "lawful_basis_reference",
            _optional_text(self.lawful_basis_reference),
        )
        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )

        _validate_period(
            self.granted_at,
            self.expires_at,
            "INVALID_BIOMETRIC_CONSENT_PERIOD",
        )

        if (
            self.status is BiometricConsentStatus.REVOKED
            and self.revoked_at is None
        ):
            raise ValueError(
                "BIOMETRIC_CONSENT_REVOKED_AT_REQUIRED"
            )

        if (
            self.revoked_at is not None
            and self.revoked_at < self.granted_at
        ):
            raise ValueError(
                "INVALID_BIOMETRIC_CONSENT_REVOCATION_TIME"
            )

    def is_active(
        self,
        *,
        at: datetime | None = None,
        purpose: BiometricPurpose | str | None = None,
    ) -> bool:
        moment = at or utcnow()

        if self.status is not BiometricConsentStatus.ACTIVE:
            return False

        if self.expires_at is not None and moment >= self.expires_at:
            return False

        if purpose is not None:
            try:
                required_purpose = BiometricPurpose(purpose)
            except ValueError:
                return False

            if required_purpose is not self.purpose:
                return False

        return True

    def revoke(
        self,
        *,
        at: datetime | None = None,
    ) -> BiometricConsent:
        if self.status is not BiometricConsentStatus.ACTIVE:
            raise ValueError(
                "INVALID_BIOMETRIC_CONSENT_TRANSITION"
            )

        revoked_at = at or utcnow()

        if revoked_at < self.granted_at:
            raise ValueError(
                "INVALID_BIOMETRIC_CONSENT_REVOCATION_TIME"
            )

        return replace(
            self,
            status=BiometricConsentStatus.REVOKED,
            revoked_at=revoked_at,
        )


@dataclass(frozen=True)
class CaptureDevice:
    device_reference: str
    channel: CaptureChannel
    platform: str | None = None
    operating_system: str | None = None
    application_version: str | None = None
    camera_facing: str | None = None
    integrity_verified: bool = False
    hardware_backed_key_available: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "device_reference",
            _required_text(
                self.device_reference,
                "CAPTURE_DEVICE_REFERENCE_REQUIRED",
            ),
        )
        object.__setattr__(
            self,
            "channel",
            CaptureChannel(self.channel),
        )
        object.__setattr__(
            self,
            "platform",
            _optional_text(self.platform),
        )
        object.__setattr__(
            self,
            "operating_system",
            _optional_text(self.operating_system),
        )
        object.__setattr__(
            self,
            "application_version",
            _optional_text(self.application_version),
        )
        object.__setattr__(
            self,
            "camera_facing",
            (
                _optional_text(self.camera_facing).upper()
                if _optional_text(self.camera_facing)
                else None
            ),
        )


@dataclass(frozen=True)
class CaptureEnvironment:
    lighting: CaptureLighting = CaptureLighting.UNKNOWN
    network_reference: str | None = None
    country_code: str | None = None
    location_accuracy_metres: float | None = None
    vpn_detected: bool = False
    emulator_detected: bool = False
    rooted_or_jailbroken: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "lighting",
            CaptureLighting(self.lighting),
        )
        object.__setattr__(
            self,
            "network_reference",
            _optional_text(self.network_reference),
        )

        if self.country_code is None:
            country_code = None
        else:
            if not isinstance(self.country_code, str):
                raise ValueError(
                    "INVALID_COUNTRY_CODE"
                )

            country_code = (
                self.country_code.strip().upper()
            )

            if (
                len(country_code) != 2
                or not country_code.isalpha()
            ):
                raise ValueError(
                    "INVALID_COUNTRY_CODE"
                )

        object.__setattr__(
            self,
            "country_code",
            country_code,
        )

        if (
            self.location_accuracy_metres is not None
            and self.location_accuracy_metres < 0
        ):
            raise ValueError(
                "INVALID_LOCATION_ACCURACY"
            )


@dataclass(frozen=True)
class CaptureQuality:
    overall_score: float
    face_detected: bool
    single_subject_detected: bool
    sharpness_score: float | None = None
    illumination_score: float | None = None
    pose_score: float | None = None
    occlusion_score: float | None = None
    minimum_required_score: float = 0.70
    decision: CaptureDecision = CaptureDecision.ACCEPT
    reason_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "overall_score",
            _validate_probability(
                self.overall_score,
                "INVALID_CAPTURE_QUALITY_SCORE",
            ),
        )
        object.__setattr__(
            self,
            "minimum_required_score",
            _validate_probability(
                self.minimum_required_score,
                "INVALID_CAPTURE_QUALITY_THRESHOLD",
            ),
        )
        object.__setattr__(
            self,
            "decision",
            CaptureDecision(self.decision),
        )

        optional_scores = (
            "sharpness_score",
            "illumination_score",
            "pose_score",
            "occlusion_score",
        )

        for field_name in optional_scores:
            value = getattr(self, field_name)

            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _validate_probability(
                        value,
                        "INVALID_CAPTURE_COMPONENT_SCORE",
                    ),
                )

        normalized_reasons = tuple(
            dict.fromkeys(
                reason.strip().upper()
                for reason in self.reason_codes
                if reason and reason.strip()
            )
        )

        object.__setattr__(
            self,
            "reason_codes",
            normalized_reasons,
        )

        if (
            self.decision is CaptureDecision.ACCEPT
            and (
                not self.face_detected
                or not self.single_subject_detected
                or self.overall_score
                < self.minimum_required_score
            )
        ):
            raise ValueError(
                "CAPTURE_ACCEPT_DECISION_INCONSISTENT"
            )

    def acceptable(self) -> bool:
        return (
            self.decision is CaptureDecision.ACCEPT
            and self.face_detected
            and self.single_subject_detected
            and self.overall_score
            >= self.minimum_required_score
        )


@dataclass(frozen=True)
class BiometricEnrollment:
    enrollment_id: str
    tenant_id: str
    identity_id: str
    biometric_type: BiometricType
    purpose: BiometricPurpose
    consent_id: str
    template_reference: str
    provider_reference: str
    algorithm_version: str
    status: BiometricEnrollmentStatus = (
        BiometricEnrollmentStatus.PENDING
    )
    capture_device: CaptureDevice | None = None
    capture_environment: CaptureEnvironment | None = None
    capture_quality: CaptureQuality | None = None
    enrolled_at: datetime | None = None
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.version < 1:
            raise ValueError(
                "INVALID_AGGREGATE_VERSION"
            )

        object.__setattr__(
            self,
            "enrollment_id",
            _required_text(
                self.enrollment_id,
                "BIOMETRIC_ENROLLMENT_ID_REQUIRED",
            ),
        )
        object.__setattr__(
            self,
            "tenant_id",
            _required_text(
                self.tenant_id,
                "TENANT_ID_REQUIRED",
            ),
        )
        object.__setattr__(
            self,
            "identity_id",
            _required_text(
                self.identity_id,
                "IDENTITY_ID_REQUIRED",
            ),
        )
        object.__setattr__(
            self,
            "biometric_type",
            BiometricType(self.biometric_type),
        )
        object.__setattr__(
            self,
            "purpose",
            BiometricPurpose(self.purpose),
        )
        object.__setattr__(
            self,
            "consent_id",
            _required_text(
                self.consent_id,
                "BIOMETRIC_CONSENT_ID_REQUIRED",
            ),
        )
        object.__setattr__(
            self,
            "template_reference",
            _required_text(
                self.template_reference,
                "BIOMETRIC_TEMPLATE_REFERENCE_REQUIRED",
            ),
        )
        object.__setattr__(
            self,
            "provider_reference",
            _required_text(
                self.provider_reference,
                "BIOMETRIC_PROVIDER_REFERENCE_REQUIRED",
            ),
        )
        object.__setattr__(
            self,
            "algorithm_version",
            _required_text(
                self.algorithm_version,
                "BIOMETRIC_ALGORITHM_VERSION_REQUIRED",
            ),
        )
        object.__setattr__(
            self,
            "status",
            BiometricEnrollmentStatus(self.status),
        )
        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )

        _validate_period(
            self.created_at,
            self.expires_at,
            "INVALID_BIOMETRIC_ENROLLMENT_PERIOD",
        )

        if (
            self.status is BiometricEnrollmentStatus.ACTIVE
            and self.enrolled_at is None
        ):
            raise ValueError(
                "BIOMETRIC_ENROLLED_AT_REQUIRED"
            )

        if (
            self.status is BiometricEnrollmentStatus.REVOKED
            and self.revoked_at is None
        ):
            raise ValueError(
                "BIOMETRIC_REVOKED_AT_REQUIRED"
            )

    def is_effective(
        self,
        *,
        at: datetime | None = None,
    ) -> bool:
        moment = at or utcnow()

        if self.status is not BiometricEnrollmentStatus.ACTIVE:
            return False

        if self.expires_at is not None and moment >= self.expires_at:
            return False

        return True

    def transition(
        self,
        target: BiometricEnrollmentStatus | str,
        *,
        at: datetime | None = None,
    ) -> BiometricEnrollment:
        normalized_target = BiometricEnrollmentStatus(target)

        if (
            normalized_target
            not in BIOMETRIC_ENROLLMENT_TRANSITIONS[self.status]
        ):
            raise ValueError(
                "INVALID_BIOMETRIC_ENROLLMENT_TRANSITION"
            )

        moment = at or utcnow()

        changes: dict[str, Any] = {
            "status": normalized_target,
            "updated_at": moment,
            "version": self.version + 1,
        }

        if normalized_target is BiometricEnrollmentStatus.ACTIVE:
            changes["enrolled_at"] = self.enrolled_at or moment
            changes["revoked_at"] = None

        elif normalized_target is BiometricEnrollmentStatus.REVOKED:
            changes["revoked_at"] = moment

        return replace(
            self,
            **changes,
        )


def new_biometric_enrollment_id() -> str:
    return identifier()
