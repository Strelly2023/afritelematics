from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, TypeVar

from .identity_policy import (
    IdentityPolicyDecision,
    IdentityPolicyOperation,
    IdentityPolicyService,
)
from .merge_events import (
    IdentityMergedEvent,
    identity_merged_event,
)
from .models import (
    AssuranceLevel,
    ContactPoint,
    Identity,
    IdentityAddress,
    IdentityIdentifier,
    IdentityName,
    IdentityStatus,
    RequestContext,
    VerificationStatus,
    utcnow,
)
from .tenant_boundary import TenantBoundaryService


T = TypeVar("T")


ASSURANCE_ORDER = {
    AssuranceLevel.NID_AL0: 0,
    AssuranceLevel.NID_AL1: 1,
    AssuranceLevel.NID_AL2: 2,
    AssuranceLevel.NID_AL3: 3,
    AssuranceLevel.NID_AL4: 4,
}


@dataclass(frozen=True)
class IdentityMergeResult:
    source_identity: Identity
    target_identity: Identity
    event: IdentityMergedEvent


class IdentityMergeService:
    def __init__(
        self,
        *,
        boundary: TenantBoundaryService | None = None,
        policy: IdentityPolicyService | None = None,
    ) -> None:
        self.boundary = boundary or TenantBoundaryService()
        self.policy = policy or IdentityPolicyService()

    def merge(
        self,
        *,
        context: RequestContext,
        actor_role: str,
        source: Identity,
        target: Identity,
        expected_source_version: int,
        expected_target_version: int,
        metadata: dict[str, Any] | None = None,
    ) -> IdentityMergeResult:
        self.boundary.assert_identity_access(context, source)
        self.boundary.assert_identity_access(context, target)

        self.boundary.assert_expected_version(
            actual_version=source.version,
            expected_version=expected_source_version,
        )
        self.boundary.assert_expected_version(
            actual_version=target.version,
            expected_version=expected_target_version,
        )

        self._assert_distinct(source, target)
        self._assert_mergeable_states(source, target)

        decision = self.policy.evaluate(
            operation=IdentityPolicyOperation.MERGE_IDENTITIES,
            actor_role=actor_role,
            authentication_strength=context.authentication_strength,
            same_identity=False,
            identity_status=target.status,
            verification_status=target.verification_status,
        )

        if decision.decision is IdentityPolicyDecision.REQUIRE_STEP_UP:
            raise PermissionError("STEP_UP_REQUIRED")

        if decision.decision is not IdentityPolicyDecision.ALLOW:
            raise PermissionError("IDENTITY_MERGE_DENIED")

        now = utcnow()

        merged_target = replace(
            target,
            legal_name=target.legal_name or source.legal_name,
            preferred_name=target.preferred_name or source.preferred_name,
            alternative_names=self._merge_unique(
                target.alternative_names,
                source.alternative_names,
            ),
            contact_points=self._merge_unique(
                target.contact_points,
                source.contact_points,
            ),
            addresses=self._merge_unique(
                target.addresses,
                source.addresses,
            ),
            identifiers=self._merge_unique(
                target.identifiers,
                source.identifiers,
            ),
            assurance_level=self._max_assurance(
                target.assurance_level,
                source.assurance_level,
            ),
            metadata=self._merge_metadata(
                source=source,
                target=target,
                metadata=metadata,
            ),
            updated_at=now,
            version=target.version + 1,
        )

        retired_source = replace(
            source,
            status=IdentityStatus.DELETED,
            metadata={
                **source.metadata,
                "merged_into_identity_id": target.identity_id,
            },
            updated_at=now,
            version=source.version + 1,
        )

        event = identity_merged_event(
            tenant_id=target.tenant_id,
            source_identity_id=source.identity_id,
            target_identity_id=target.identity_id,
            actor_identity_id=context.actor_identity_id,
            correlation_id=context.correlation_id,
            request_id=context.request_id,
            source_version=retired_source.version,
            target_version=merged_target.version,
            metadata=metadata,
        )

        return IdentityMergeResult(
            source_identity=retired_source,
            target_identity=merged_target,
            event=event,
        )

    @staticmethod
    def _assert_distinct(
        source: Identity,
        target: Identity,
    ) -> None:
        if source.identity_id == target.identity_id:
            raise ValueError("IDENTITY_SELF_MERGE_DENIED")

    @staticmethod
    def _assert_mergeable_states(
        source: Identity,
        target: Identity,
    ) -> None:
        if source.status is not IdentityStatus.DISABLED:
            raise ValueError("MERGE_SOURCE_MUST_BE_DISABLED")

        if target.status is not IdentityStatus.ACTIVE:
            raise ValueError("MERGE_TARGET_MUST_BE_ACTIVE")

        if target.verification_status is not VerificationStatus.VERIFIED:
            raise ValueError("MERGE_TARGET_MUST_BE_VERIFIED")

    @staticmethod
    def _merge_unique(
        first: tuple[T, ...],
        second: tuple[T, ...],
    ) -> tuple[T, ...]:
        merged = list(first)

        for item in second:
            if item not in merged:
                merged.append(item)

        return tuple(merged)

    @staticmethod
    def _max_assurance(
        first: AssuranceLevel,
        second: AssuranceLevel,
    ) -> AssuranceLevel:
        return (
            first
            if ASSURANCE_ORDER[first] >= ASSURANCE_ORDER[second]
            else second
        )

    @staticmethod
    def _merge_metadata(
        *,
        source: Identity,
        target: Identity,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        return {
            **source.metadata,
            **target.metadata,
            **dict(metadata or {}),
            "merged_source_identity_id": source.identity_id,
        }
