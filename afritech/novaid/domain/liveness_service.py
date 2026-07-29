from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .biometric_models import (
    BiometricPurpose,
    CaptureDevice,
    CaptureEnvironment,
    CaptureQuality,
)
from .liveness_events import (
    LivenessAssessmentEvent,
    liveness_assessment_event,
)
from .liveness_models import (
    LivenessAssessmentRecord,
    LivenessEvidence,
    LivenessPolicy,
)
from .models import (
    RequestContext,
    Tenant,
    identifier,
    utcnow,
)


@dataclass(frozen=True)
class LivenessAssessmentResult:
    assessment: LivenessAssessmentRecord
    event: LivenessAssessmentEvent


class LivenessAssessmentService:
    """Govern provider-produced liveness and PAD evidence."""

    def assess(
        self,
        *,
        context: RequestContext,
        tenant: Tenant,
        identity_id: str,
        purpose: BiometricPurpose | str,
        attempt_number: int,
        capture_device: CaptureDevice,
        capture_environment: CaptureEnvironment,
        capture_quality: CaptureQuality,
        evidence: LivenessEvidence,
        policy: LivenessPolicy | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LivenessAssessmentResult:
        assessment_policy = policy or LivenessPolicy()
        normalized_identity_id = self._required_text(
            identity_id,
            "IDENTITY_ID_REQUIRED",
        )
        normalized_purpose = BiometricPurpose(purpose)

        self._assert_tenant_boundary(
            context=context,
            tenant=tenant,
        )
        self._assert_capture(
            tenant=tenant,
            policy=assessment_policy,
            capture_device=capture_device,
            capture_environment=capture_environment,
            capture_quality=capture_quality,
        )

        decision, reason_codes = assessment_policy.decide(
            evidence=evidence,
            attempt_number=attempt_number,
        )

        assessment_id = identifier()
        now = utcnow()

        record = LivenessAssessmentRecord(
            assessment_id=assessment_id,
            tenant_id=tenant.tenant_id,
            identity_id=normalized_identity_id,
            purpose=normalized_purpose,
            decision=decision,
            attempt_number=attempt_number,
            mode=evidence.mode,
            liveness_score=evidence.liveness_score,
            presentation_attack_score=(
                evidence.presentation_attack_score
            ),
            provider_reference=evidence.provider_reference,
            algorithm_version=evidence.algorithm_version,
            capture_device=capture_device,
            capture_environment=capture_environment,
            capture_quality=capture_quality,
            assessed_at=now,
            detected_attack_types=(
                evidence.detected_attack_types
            ),
            reason_codes=reason_codes,
            metadata=dict(metadata or {}),
        )

        event = liveness_assessment_event(
            assessment_id=record.assessment_id,
            tenant_id=record.tenant_id,
            identity_id=record.identity_id,
            actor_identity_id=context.actor_identity_id,
            correlation_id=context.correlation_id,
            request_id=context.request_id,
            purpose=record.purpose,
            decision=record.decision,
            mode=record.mode,
            attempt_number=record.attempt_number,
            liveness_score=record.liveness_score,
            presentation_attack_score=(
                record.presentation_attack_score
            ),
            detected_attack_types=(
                record.detected_attack_types
            ),
            reason_codes=record.reason_codes,
            metadata=metadata,
        )

        return LivenessAssessmentResult(
            assessment=record,
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
    def _assert_capture(
        *,
        tenant: Tenant,
        policy: LivenessPolicy,
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
                "LIVENESS_CAPTURE_QUALITY_BELOW_POLICY"
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
