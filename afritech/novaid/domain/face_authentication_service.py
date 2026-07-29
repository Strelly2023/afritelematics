from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .biometric_verification_models import (
    FaceVerificationDecision,
)
from .face_authentication_events import (
    FaceAuthenticationEvent,
    face_authentication_event,
)
from .face_authentication_models import (
    FaceAuthenticationContext,
    FaceAuthenticationDecision,
    FaceAuthenticationPolicy,
    FaceAuthenticationRecord,
)
from .models import (
    AuthenticationStrength,
    IdentityStatus,
    RequestContext,
    Tenant,
    identifier,
    utcnow,
)


@dataclass(frozen=True)
class FaceAuthenticationResult:
    authentication: FaceAuthenticationRecord
    event: FaceAuthenticationEvent


class FaceAuthenticationService:
    """Convert face-verification evidence into an auth decision."""

    def authenticate(
        self,
        *,
        request_context: RequestContext,
        tenant: Tenant,
        authentication_context: FaceAuthenticationContext,
        policy: FaceAuthenticationPolicy | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> FaceAuthenticationResult:
        authentication_policy = (
            policy or FaceAuthenticationPolicy()
        )

        self._assert_tenant_boundary(
            request_context=request_context,
            tenant=tenant,
            context=authentication_context,
        )

        decision, reason_codes = self._decide(
            tenant=tenant,
            context=authentication_context,
            policy=authentication_policy,
        )

        authentication_id = identifier()
        now = utcnow()

        record = FaceAuthenticationRecord(
            authentication_id=authentication_id,
            tenant_id=tenant.tenant_id,
            identity_id=(
                authentication_context.verification.identity_id
            ),
            verification_id=(
                authentication_context.verification.verification_id
            ),
            enrollment_id=(
                authentication_context.verification.enrollment_id
            ),
            purpose=authentication_context.purpose,
            decision=decision,
            verification_decision=(
                authentication_context.verification.decision
            ),
            risk_score=authentication_context.risk_score,
            authentication_strength=(
                authentication_context.authentication_strength
            ),
            current_assurance_level=(
                authentication_context.current_assurance_level
            ),
            required_assurance_level=(
                authentication_context.required_assurance_level
            ),
            authenticated_at=now,
            reason_codes=reason_codes,
            metadata=dict(metadata or {}),
        )

        event = face_authentication_event(
            authentication_id=record.authentication_id,
            tenant_id=record.tenant_id,
            identity_id=record.identity_id,
            verification_id=record.verification_id,
            enrollment_id=record.enrollment_id,
            actor_identity_id=(
                request_context.actor_identity_id
            ),
            correlation_id=request_context.correlation_id,
            request_id=request_context.request_id,
            purpose=record.purpose,
            decision=record.decision,
            risk_score=record.risk_score,
            reason_codes=record.reason_codes,
            metadata=metadata,
        )

        return FaceAuthenticationResult(
            authentication=record,
            event=event,
        )

    @staticmethod
    def _assert_tenant_boundary(
        *,
        request_context: RequestContext,
        tenant: Tenant,
        context: FaceAuthenticationContext,
    ) -> None:
        if request_context.tenant_id != tenant.tenant_id:
            raise PermissionError("TENANT_ACCESS_DENIED")

        if (
            context.verification.tenant_id
            != tenant.tenant_id
        ):
            raise PermissionError(
                "FACE_VERIFICATION_TENANT_MISMATCH"
            )

    @staticmethod
    def _decide(
        *,
        tenant: Tenant,
        context: FaceAuthenticationContext,
        policy: FaceAuthenticationPolicy,
    ) -> tuple[
        FaceAuthenticationDecision,
        tuple[str, ...],
    ]:
        if context.identity_status is not IdentityStatus.ACTIVE:
            return (
                FaceAuthenticationDecision.DENY,
                ("IDENTITY_NOT_ACTIVE",),
            )

        if not context.membership_active:
            return (
                FaceAuthenticationDecision.DENY,
                ("MEMBERSHIP_NOT_ACTIVE",),
            )

        if not context.credential_active:
            return (
                FaceAuthenticationDecision.DENY,
                ("CREDENTIAL_NOT_ACTIVE",),
            )

        if not context.session_active:
            return (
                FaceAuthenticationDecision.DENY,
                ("SESSION_NOT_ACTIVE",),
            )

        if (
            context.previous_failed_attempts
            >= policy.maximum_failed_attempts_before_identity_lock
        ):
            return (
                FaceAuthenticationDecision.LOCK_IDENTITY,
                ("IDENTITY_FAILURE_THRESHOLD_REACHED",),
            )

        if (
            context.risk_score
            >= policy.identity_lock_risk_threshold
        ):
            return (
                FaceAuthenticationDecision.LOCK_IDENTITY,
                ("CRITICAL_AUTHENTICATION_RISK",),
            )

        if (
            context.previous_failed_attempts
            >= policy.maximum_failed_attempts_before_session_lock
        ):
            return (
                FaceAuthenticationDecision.LOCK_SESSION,
                ("SESSION_FAILURE_THRESHOLD_REACHED",),
            )

        if (
            context.risk_score
            >= policy.session_lock_risk_threshold
        ):
            return (
                FaceAuthenticationDecision.LOCK_SESSION,
                ("HIGH_AUTHENTICATION_RISK",),
            )

        verification_decision = (
            context.verification.decision
        )

        if (
            verification_decision
            is FaceVerificationDecision.NO_MATCH
        ):
            if policy.no_match_locks_session:
                return (
                    FaceAuthenticationDecision.LOCK_SESSION,
                    ("FACE_NO_MATCH",),
                )

            return (
                FaceAuthenticationDecision.DENY,
                ("FACE_NO_MATCH",),
            )

        if (
            verification_decision
            is FaceVerificationDecision.MANUAL_REVIEW
        ):
            return (
                FaceAuthenticationDecision.REQUIRE_MANUAL_REVIEW,
                ("FACE_MANUAL_REVIEW_REQUIRED",),
            )

        if (
            verification_decision
            is not FaceVerificationDecision.MATCH
        ):
            return (
                FaceAuthenticationDecision.DENY,
                ("UNSUPPORTED_FACE_VERIFICATION_DECISION",),
            )

        if not tenant.security_policy.allows_authentication_strength(
            context.authentication_strength
        ):
            return (
                FaceAuthenticationDecision.REQUIRE_STEP_UP,
                ("AUTHENTICATION_STRENGTH_INSUFFICIENT",),
            )

        if not context.assurance_satisfied():
            return (
                FaceAuthenticationDecision.REQUIRE_STEP_UP,
                ("ASSURANCE_LEVEL_INSUFFICIENT",),
            )

        if (
            context.risk_score
            >= tenant.security_policy.risk_step_up_threshold
        ):
            return (
                FaceAuthenticationDecision.REQUIRE_STEP_UP,
                ("ELEVATED_AUTHENTICATION_RISK",),
            )

        return (
            FaceAuthenticationDecision.ALLOW,
            ("FACE_AUTHENTICATION_CONTROLS_SATISFIED",),
        )
