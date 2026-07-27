from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from .models import (
    AssuranceLevel,
    Identity,
    RequestContext,
    VerificationStatus,
    utcnow,
)
from .verification_events import (
    IdentityVerificationEvent,
    verification_event,
)
from .tenant_boundary import TenantBoundaryService


VERIFICATION_TRANSITIONS: dict[
    VerificationStatus,
    set[VerificationStatus],
] = {
    VerificationStatus.UNVERIFIED: {
        VerificationStatus.PENDING,
    },
    VerificationStatus.PENDING: {
        VerificationStatus.IN_PROGRESS,
        VerificationStatus.REJECTED,
        VerificationStatus.EXPIRED,
    },
    VerificationStatus.IN_PROGRESS: {
        VerificationStatus.MANUAL_REVIEW,
        VerificationStatus.VERIFIED,
        VerificationStatus.REJECTED,
        VerificationStatus.EXPIRED,
    },
    VerificationStatus.MANUAL_REVIEW: {
        VerificationStatus.VERIFIED,
        VerificationStatus.REJECTED,
        VerificationStatus.EXPIRED,
    },
    VerificationStatus.VERIFIED: {
        VerificationStatus.EXPIRED,
    },
    VerificationStatus.REJECTED: {
        VerificationStatus.PENDING,
    },
    VerificationStatus.EXPIRED: {
        VerificationStatus.PENDING,
    },
}


ASSURANCE_ORDER = {
    AssuranceLevel.NID_AL0: 0,
    AssuranceLevel.NID_AL1: 1,
    AssuranceLevel.NID_AL2: 2,
    AssuranceLevel.NID_AL3: 3,
    AssuranceLevel.NID_AL4: 4,
}


@dataclass(frozen=True)
class IdentityVerificationResult:
    identity: Identity
    event: IdentityVerificationEvent


class IdentityVerificationService:
    def __init__(
        self,
        boundary: TenantBoundaryService | None = None,
    ) -> None:
        self.boundary = boundary or TenantBoundaryService()

    _EVENT_TYPES = {
        VerificationStatus.PENDING:
            "IDENTITY_VERIFICATION_STARTED",
        VerificationStatus.IN_PROGRESS:
            "IDENTITY_VERIFICATION_IN_PROGRESS",
        VerificationStatus.MANUAL_REVIEW:
            "IDENTITY_VERIFICATION_MANUAL_REVIEW_REQUIRED",
        VerificationStatus.VERIFIED:
            "IDENTITY_VERIFIED",
        VerificationStatus.REJECTED:
            "IDENTITY_VERIFICATION_REJECTED",
        VerificationStatus.EXPIRED:
            "IDENTITY_VERIFICATION_EXPIRED",
    }

    def transition(
        self,
        *,
        context: RequestContext,
        identity: Identity,
        target: VerificationStatus,
        expected_version: int,
        assurance_level: AssuranceLevel | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> IdentityVerificationResult:
        self.boundary.assert_identity_access(
            context,
            identity,
        )
        self.boundary.assert_expected_version(
            actual_version=identity.version,
            expected_version=expected_version,
        )
        self._assert_transition(identity.verification_status, target)

        next_assurance = self._resolve_assurance_level(
            identity=identity,
            target=target,
            requested=assurance_level,
        )

        previous_status = identity.verification_status
        previous_assurance = identity.assurance_level

        transitioned = replace(
            identity,
            verification_status=target,
            assurance_level=next_assurance,
            updated_at=utcnow(),
            version=identity.version + 1,
        )

        event_type = self._EVENT_TYPES.get(target)
        if event_type is None:
            raise ValueError("UNSUPPORTED_VERIFICATION_TARGET")

        event = verification_event(
            event_type=event_type,
            tenant_id=identity.tenant_id,
            identity_id=identity.identity_id,
            actor_identity_id=context.actor_identity_id,
            correlation_id=context.correlation_id,
            request_id=context.request_id,
            previous_status=previous_status,
            current_status=target,
            previous_assurance_level=previous_assurance,
            current_assurance_level=next_assurance,
            identity_version=transitioned.version,
            metadata=metadata,
        )

        return IdentityVerificationResult(
            identity=transitioned,
            event=event,
        )

    def start(
        self,
        *,
        context: RequestContext,
        identity: Identity,
        expected_version: int,
        metadata: dict[str, Any] | None = None,
    ) -> IdentityVerificationResult:
        return self.transition(
            context=context,
            identity=identity,
            target=VerificationStatus.PENDING,
            expected_version=expected_version,
            metadata=metadata,
        )

    def begin_processing(
        self,
        *,
        context: RequestContext,
        identity: Identity,
        expected_version: int,
        metadata: dict[str, Any] | None = None,
    ) -> IdentityVerificationResult:
        return self.transition(
            context=context,
            identity=identity,
            target=VerificationStatus.IN_PROGRESS,
            expected_version=expected_version,
            metadata=metadata,
        )

    def require_manual_review(
        self,
        *,
        context: RequestContext,
        identity: Identity,
        expected_version: int,
        metadata: dict[str, Any] | None = None,
    ) -> IdentityVerificationResult:
        return self.transition(
            context=context,
            identity=identity,
            target=VerificationStatus.MANUAL_REVIEW,
            expected_version=expected_version,
            metadata=metadata,
        )

    def approve(
        self,
        *,
        context: RequestContext,
        identity: Identity,
        expected_version: int,
        assurance_level: AssuranceLevel,
        metadata: dict[str, Any] | None = None,
    ) -> IdentityVerificationResult:
        return self.transition(
            context=context,
            identity=identity,
            target=VerificationStatus.VERIFIED,
            expected_version=expected_version,
            assurance_level=assurance_level,
            metadata=metadata,
        )

    def reject(
        self,
        *,
        context: RequestContext,
        identity: Identity,
        expected_version: int,
        metadata: dict[str, Any] | None = None,
    ) -> IdentityVerificationResult:
        return self.transition(
            context=context,
            identity=identity,
            target=VerificationStatus.REJECTED,
            expected_version=expected_version,
            metadata=metadata,
        )

    def expire(
        self,
        *,
        context: RequestContext,
        identity: Identity,
        expected_version: int,
        metadata: dict[str, Any] | None = None,
    ) -> IdentityVerificationResult:
        return self.transition(
            context=context,
            identity=identity,
            target=VerificationStatus.EXPIRED,
            expected_version=expected_version,
            metadata=metadata,
        )

    @staticmethod
    def _assert_transition(
        current: VerificationStatus,
        target: VerificationStatus,
    ) -> None:
        if target not in VERIFICATION_TRANSITIONS[current]:
            raise ValueError("INVALID_VERIFICATION_TRANSITION")

    @staticmethod
    def _resolve_assurance_level(
        *,
        identity: Identity,
        target: VerificationStatus,
        requested: AssuranceLevel | None,
    ) -> AssuranceLevel:
        if target is not VerificationStatus.VERIFIED:
            if requested is not None:
                raise ValueError(
                    "ASSURANCE_LEVEL_ONLY_ALLOWED_FOR_VERIFIED"
                )
            return identity.assurance_level

        if requested is None:
            raise ValueError(
                "VERIFIED_ASSURANCE_LEVEL_REQUIRED"
            )

        if requested is AssuranceLevel.NID_AL0:
            raise ValueError(
                "VERIFIED_ASSURANCE_LEVEL_TOO_LOW"
            )

        if (
            ASSURANCE_ORDER[requested]
            < ASSURANCE_ORDER[identity.assurance_level]
        ):
            raise ValueError("ASSURANCE_LEVEL_DOWNGRADE_DENIED")

        return requested
