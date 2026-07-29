from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable

from .biometric_events import (
    FaceEnrollmentEvent,
    face_enrollment_event,
)
from .biometric_models import (
    BiometricConsent,
    BiometricEnrollment,
    BiometricEnrollmentStatus,
    BiometricPurpose,
    BiometricType,
    CaptureDevice,
    CaptureEnvironment,
    CaptureQuality,
    new_biometric_enrollment_id,
)
from .models import (
    RequestContext,
    Tenant,
    utcnow,
)


NON_TERMINAL_ENROLLMENT_STATUSES = frozenset(
    {
        BiometricEnrollmentStatus.PENDING,
        BiometricEnrollmentStatus.ACTIVE,
        BiometricEnrollmentStatus.SUSPENDED,
    }
)


@dataclass(frozen=True)
class FaceEnrollmentResult:
    enrollment: BiometricEnrollment
    event: FaceEnrollmentEvent


class FaceEnrollmentService:
    """Create a governed face enrollment from secure provider references."""

    def enroll(
        self,
        *,
        context: RequestContext,
        tenant: Tenant,
        identity_id: str,
        consent: BiometricConsent,
        template_reference: str,
        provider_reference: str,
        algorithm_version: str,
        capture_device: CaptureDevice,
        capture_environment: CaptureEnvironment,
        capture_quality: CaptureQuality,
        existing_enrollments: Iterable[BiometricEnrollment] = (),
        expires_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
        now: datetime | None = None,
    ) -> FaceEnrollmentResult:
        moment = now or utcnow()
        normalized_identity_id = self._required_text(
            identity_id,
            "IDENTITY_ID_REQUIRED",
        )

        self._assert_tenant_boundary(
            context=context,
            tenant=tenant,
        )
        self._assert_consent(
            tenant=tenant,
            identity_id=normalized_identity_id,
            consent=consent,
            at=moment,
        )
        self._assert_capture_quality(
            capture_quality=capture_quality,
        )
        self._assert_device_policy(
            tenant=tenant,
            capture_device=capture_device,
            capture_environment=capture_environment,
        )
        self._assert_no_duplicate_enrollment(
            tenant_id=tenant.tenant_id,
            identity_id=normalized_identity_id,
            existing_enrollments=existing_enrollments,
        )

        enrollment = BiometricEnrollment(
            enrollment_id=new_biometric_enrollment_id(),
            tenant_id=tenant.tenant_id,
            identity_id=normalized_identity_id,
            biometric_type=BiometricType.FACE,
            purpose=BiometricPurpose.ENROLLMENT,
            consent_id=consent.consent_id,
            template_reference=self._required_text(
                template_reference,
                "BIOMETRIC_TEMPLATE_REFERENCE_REQUIRED",
            ),
            provider_reference=self._required_text(
                provider_reference,
                "BIOMETRIC_PROVIDER_REFERENCE_REQUIRED",
            ),
            algorithm_version=self._required_text(
                algorithm_version,
                "BIOMETRIC_ALGORITHM_VERSION_REQUIRED",
            ),
            status=BiometricEnrollmentStatus.PENDING,
            capture_device=capture_device,
            capture_environment=capture_environment,
            capture_quality=capture_quality,
            expires_at=expires_at,
            created_at=moment,
            updated_at=moment,
            metadata=dict(metadata or {}),
        ).transition(
            BiometricEnrollmentStatus.ACTIVE,
            at=moment,
        )

        event = face_enrollment_event(
            tenant_id=enrollment.tenant_id,
            identity_id=enrollment.identity_id,
            enrollment_id=enrollment.enrollment_id,
            consent_id=enrollment.consent_id,
            actor_identity_id=context.actor_identity_id,
            correlation_id=context.correlation_id,
            request_id=context.request_id,
            enrollment_status=enrollment.status,
            enrollment_version=enrollment.version,
            quality_score=capture_quality.overall_score,
            metadata=metadata,
        )

        return FaceEnrollmentResult(
            enrollment=enrollment,
            event=event,
        )

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

    @staticmethod
    def _assert_tenant_boundary(
        *,
        context: RequestContext,
        tenant: Tenant,
    ) -> None:
        if context.tenant_id != tenant.tenant_id:
            raise PermissionError(
                "TENANT_ACCESS_DENIED"
            )

    @staticmethod
    def _assert_consent(
        *,
        tenant: Tenant,
        identity_id: str,
        consent: BiometricConsent,
        at: datetime,
    ) -> None:
        if consent.tenant_id != tenant.tenant_id:
            raise PermissionError(
                "BIOMETRIC_CONSENT_TENANT_MISMATCH"
            )

        if consent.identity_id != identity_id:
            raise PermissionError(
                "BIOMETRIC_CONSENT_IDENTITY_MISMATCH"
            )

        if consent.purpose is not BiometricPurpose.ENROLLMENT:
            raise ValueError(
                "BIOMETRIC_CONSENT_PURPOSE_MISMATCH"
            )

        if not consent.is_active(
            at=at,
            purpose=BiometricPurpose.ENROLLMENT,
        ):
            raise PermissionError(
                "ACTIVE_BIOMETRIC_CONSENT_REQUIRED"
            )

    @staticmethod
    def _assert_capture_quality(
        *,
        capture_quality: CaptureQuality,
    ) -> None:
        if not capture_quality.acceptable():
            raise ValueError(
                "ACCEPTABLE_FACE_CAPTURE_REQUIRED"
            )

    @staticmethod
    def _assert_device_policy(
        *,
        tenant: Tenant,
        capture_device: CaptureDevice,
        capture_environment: CaptureEnvironment,
    ) -> None:
        if (
            tenant.security_policy.device_binding_required
            and not capture_device.integrity_verified
        ):
            raise PermissionError(
                "CAPTURE_DEVICE_INTEGRITY_REQUIRED"
            )

        if capture_environment.emulator_detected:
            raise PermissionError(
                "BIOMETRIC_CAPTURE_EMULATOR_DENIED"
            )

        if capture_environment.rooted_or_jailbroken:
            raise PermissionError(
                "BIOMETRIC_CAPTURE_COMPROMISED_DEVICE_DENIED"
            )

    @staticmethod
    def _assert_no_duplicate_enrollment(
        *,
        tenant_id: str,
        identity_id: str,
        existing_enrollments: Iterable[
            BiometricEnrollment
        ],
    ) -> None:
        for enrollment in existing_enrollments:
            if (
                enrollment.tenant_id == tenant_id
                and enrollment.identity_id == identity_id
                and enrollment.biometric_type
                is BiometricType.FACE
                and enrollment.purpose
                is BiometricPurpose.ENROLLMENT
                and enrollment.status
                in NON_TERMINAL_ENROLLMENT_STATUSES
            ):
                raise ValueError(
                    "DUPLICATE_ACTIVE_FACE_ENROLLMENT"
                )
