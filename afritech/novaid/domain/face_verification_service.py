from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .biometric_models import (
    BiometricConsent,
    BiometricEnrollment,
    BiometricEnrollmentStatus,
    BiometricPurpose,
    BiometricType,
    CaptureDevice,
    CaptureEnvironment,
    CaptureQuality,
)
from .biometric_verification_events import (
    FaceVerificationEvent,
    face_verification_event,
)
from .biometric_verification_models import (
    FaceMatchEvidence,
    FaceVerificationPolicy,
    FaceVerificationRecord,
)
from .models import (
    RequestContext,
    Tenant,
    identifier,
    utcnow,
)


@dataclass(frozen=True)
class FaceVerificationResult:
    verification: FaceVerificationRecord
    event: FaceVerificationEvent


class FaceVerificationService:
    """Evaluate provider-produced evidence against an active enrollment."""

    def verify(
        self,
        *,
        context: RequestContext,
        tenant: Tenant,
        identity_id: str,
        enrollment: BiometricEnrollment,
        consent: BiometricConsent,
        purpose: BiometricPurpose | str,
        capture_device: CaptureDevice,
        capture_environment: CaptureEnvironment,
        capture_quality: CaptureQuality,
        match_evidence: FaceMatchEvidence,
        policy: FaceVerificationPolicy | None = None,
        metadata: dict[str, Any] | None = None,
        now: datetime | None = None,
    ) -> FaceVerificationResult:
        moment = now or utcnow()
        verification_policy = policy or FaceVerificationPolicy()
        normalized_purpose = BiometricPurpose(purpose)
        normalized_identity_id = self._required_text(
            identity_id,
            "IDENTITY_ID_REQUIRED",
        )

        self._assert_tenant_boundary(
            context=context,
            tenant=tenant,
        )
        self._assert_enrollment(
            tenant=tenant,
            identity_id=normalized_identity_id,
            enrollment=enrollment,
            at=moment,
        )
        self._assert_consent(
            tenant=tenant,
            identity_id=normalized_identity_id,
            consent=consent,
            purpose=normalized_purpose,
            at=moment,
        )
        self._assert_capture(
            tenant=tenant,
            policy=verification_policy,
            capture_device=capture_device,
            capture_environment=capture_environment,
            capture_quality=capture_quality,
        )

        decision = verification_policy.decide(
            match_evidence.similarity_score
        )
        verification_id = identifier()

        record = FaceVerificationRecord(
            verification_id=verification_id,
            tenant_id=tenant.tenant_id,
            identity_id=normalized_identity_id,
            enrollment_id=enrollment.enrollment_id,
            consent_id=consent.consent_id,
            purpose=normalized_purpose,
            decision=decision,
            similarity_score=match_evidence.similarity_score,
            match_threshold=verification_policy.match_threshold,
            manual_review_threshold=(
                verification_policy.manual_review_threshold
            ),
            provider_reference=(
                match_evidence.provider_reference
            ),
            algorithm_version=(
                match_evidence.algorithm_version
            ),
            capture_device=capture_device,
            capture_environment=capture_environment,
            capture_quality=capture_quality,
            verified_at=moment,
            reason_codes=match_evidence.reason_codes,
            metadata=dict(metadata or {}),
        )

        event = face_verification_event(
            verification_id=record.verification_id,
            tenant_id=record.tenant_id,
            identity_id=record.identity_id,
            enrollment_id=record.enrollment_id,
            consent_id=record.consent_id,
            actor_identity_id=context.actor_identity_id,
            correlation_id=context.correlation_id,
            request_id=context.request_id,
            purpose=record.purpose,
            decision=record.decision,
            similarity_score=record.similarity_score,
            threshold=record.match_threshold,
            provider_reference=record.provider_reference,
            algorithm_version=record.algorithm_version,
            metadata=metadata,
        )

        return FaceVerificationResult(
            verification=record,
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
            raise PermissionError("TENANT_ACCESS_DENIED")

    @staticmethod
    def _assert_enrollment(
        *,
        tenant: Tenant,
        identity_id: str,
        enrollment: BiometricEnrollment,
        at: datetime,
    ) -> None:
        if enrollment.tenant_id != tenant.tenant_id:
            raise PermissionError(
                "BIOMETRIC_ENROLLMENT_TENANT_MISMATCH"
            )

        if enrollment.identity_id != identity_id:
            raise PermissionError(
                "BIOMETRIC_ENROLLMENT_IDENTITY_MISMATCH"
            )

        if enrollment.biometric_type is not BiometricType.FACE:
            raise ValueError(
                "ACTIVE_FACE_ENROLLMENT_REQUIRED"
            )

        if enrollment.status is not BiometricEnrollmentStatus.ACTIVE:
            raise PermissionError(
                "ACTIVE_FACE_ENROLLMENT_REQUIRED"
            )

        if not enrollment.is_effective(at=at):
            raise PermissionError(
                "ACTIVE_FACE_ENROLLMENT_REQUIRED"
            )

    @staticmethod
    def _assert_consent(
        *,
        tenant: Tenant,
        identity_id: str,
        consent: BiometricConsent,
        purpose: BiometricPurpose,
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

        if consent.purpose is not purpose:
            raise ValueError(
                "BIOMETRIC_CONSENT_PURPOSE_MISMATCH"
            )

        if not consent.is_active(
            at=at,
            purpose=purpose,
        ):
            raise PermissionError(
                "ACTIVE_BIOMETRIC_CONSENT_REQUIRED"
            )

    @staticmethod
    def _assert_capture(
        *,
        tenant: Tenant,
        policy: FaceVerificationPolicy,
        capture_device: CaptureDevice,
        capture_environment: CaptureEnvironment,
        capture_quality: CaptureQuality,
    ) -> None:
        if not capture_quality.acceptable():
            raise ValueError(
                "ACCEPTABLE_FACE_CAPTURE_REQUIRED"
            )

        if (
            capture_quality.overall_score
            < policy.minimum_capture_quality_score
        ):
            raise ValueError(
                "FACE_CAPTURE_QUALITY_BELOW_POLICY"
            )

        integrity_required = (
            policy.require_device_integrity
            or tenant.security_policy.device_binding_required
        )

        if (
            integrity_required
            and not capture_device.integrity_verified
        ):
            raise PermissionError(
                "CAPTURE_DEVICE_INTEGRITY_REQUIRED"
            )

        if (
            policy.deny_emulators
            and capture_environment.emulator_detected
        ):
            raise PermissionError(
                "BIOMETRIC_CAPTURE_EMULATOR_DENIED"
            )

        if (
            policy.deny_compromised_devices
            and capture_environment.rooted_or_jailbroken
        ):
            raise PermissionError(
                "BIOMETRIC_CAPTURE_COMPROMISED_DEVICE_DENIED"
            )
