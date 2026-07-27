from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from afritech.novaid.domain import (
    AssuranceLevel,
    ContactPoint,
    ContactPointType,
    Identity,
    IdentityIdentifier,
    IdentityStatus,
    IdentifierType,
    RequestContext,
    VerificationStatus,
)
from afritech.novaid.domain.identity_merge_service import (
    IdentityMergeService,
)
from afritech.novaid.domain.merge_events import (
    IdentityMergedEvent,
)


def uid() -> str:
    return str(uuid4())


def context(tenant_id: str, strength: str = "PHISHING_RESISTANT") -> RequestContext:
    return RequestContext(
        tenant_id=tenant_id,
        actor_identity_id=uid(),
        actor_membership_id=uid(),
        correlation_id=uid(),
        request_id=uid(),
        authentication_strength=strength,
    )


def source_identity(tenant_id: str) -> Identity:
    return Identity(
        identity_id=uid(),
        tenant_id=tenant_id,
        normalized_email="source@example.com",
        status=IdentityStatus.DISABLED,
        verification_status=VerificationStatus.VERIFIED,
        assurance_level=AssuranceLevel.NID_AL3,
        contact_points=(
            ContactPoint(
                contact_type=ContactPointType.MOBILE,
                value="+61400000000",
                verified=True,
            ),
        ),
        identifiers=(
            IdentityIdentifier(
                identifier_type=IdentifierType.CUSTOMER_REFERENCE,
                value="source-reference",
            ),
        ),
        metadata={"source": "legacy-record"},
    )


def target_identity(tenant_id: str) -> Identity:
    return Identity(
        identity_id=uid(),
        tenant_id=tenant_id,
        normalized_email="target@example.com",
        status=IdentityStatus.ACTIVE,
        verification_status=VerificationStatus.VERIFIED,
        assurance_level=AssuranceLevel.NID_AL2,
        contact_points=(
            ContactPoint(
                contact_type=ContactPointType.EMAIL,
                value="target@example.com",
                verified=True,
                primary=True,
            ),
        ),
        metadata={"target": "canonical-record"},
    )


def test_merge_consolidates_source_into_target() -> None:
    tenant_id = uid()
    source = source_identity(tenant_id)
    target = target_identity(tenant_id)

    result = IdentityMergeService().merge(
        context=context(tenant_id),
        actor_role="IDENTITY_ADMIN",
        source=source,
        target=target,
        expected_source_version=source.version,
        expected_target_version=target.version,
        metadata={"reason": "duplicate-resolution"},
    )

    assert result.source_identity.status is IdentityStatus.DELETED
    assert result.source_identity.version == source.version + 1
    assert (
        result.source_identity.metadata["merged_into_identity_id"]
        == target.identity_id
    )

    assert result.target_identity.status is IdentityStatus.ACTIVE
    assert result.target_identity.version == target.version + 1
    assert len(result.target_identity.contact_points) == 2
    assert len(result.target_identity.identifiers) == 1
    assert result.target_identity.assurance_level is AssuranceLevel.NID_AL3
    assert result.target_identity.metadata["reason"] == "duplicate-resolution"

    assert result.event.event_type == "IDENTITY_MERGED"
    assert result.event.source_identity_id == source.identity_id
    assert result.event.target_identity_id == target.identity_id


def test_self_merge_is_denied() -> None:
    tenant_id = uid()
    current = source_identity(tenant_id)

    with pytest.raises(
        ValueError,
        match="IDENTITY_SELF_MERGE_DENIED",
    ):
        IdentityMergeService().merge(
            context=context(tenant_id),
            actor_role="IDENTITY_ADMIN",
            source=current,
            target=current,
            expected_source_version=current.version,
            expected_target_version=current.version,
        )


def test_cross_tenant_merge_fails_closed() -> None:
    source = source_identity(uid())
    target = target_identity(uid())

    with pytest.raises(
        PermissionError,
        match="TENANT_ACCESS_DENIED",
    ):
        IdentityMergeService().merge(
            context=context(source.tenant_id),
            actor_role="IDENTITY_ADMIN",
            source=source,
            target=target,
            expected_source_version=source.version,
            expected_target_version=target.version,
        )


def test_source_must_be_disabled() -> None:
    tenant_id = uid()
    source = source_identity(tenant_id)
    source = Identity(
        **{
            **source.__dict__,
            "status": IdentityStatus.ACTIVE,
        }
    )

    with pytest.raises(
        ValueError,
        match="MERGE_SOURCE_MUST_BE_DISABLED",
    ):
        IdentityMergeService().merge(
            context=context(tenant_id),
            actor_role="IDENTITY_ADMIN",
            source=source,
            target=target_identity(tenant_id),
            expected_source_version=source.version,
            expected_target_version=1,
        )


def test_target_must_be_active_and_verified() -> None:
    tenant_id = uid()
    source = source_identity(tenant_id)
    target = target_identity(tenant_id)
    target = Identity(
        **{
            **target.__dict__,
            "verification_status": VerificationStatus.IN_PROGRESS,
        }
    )

    with pytest.raises(
        ValueError,
        match="MERGE_TARGET_MUST_BE_VERIFIED",
    ):
        IdentityMergeService().merge(
            context=context(tenant_id),
            actor_role="IDENTITY_ADMIN",
            source=source,
            target=target,
            expected_source_version=source.version,
            expected_target_version=target.version,
        )


def test_merge_requires_phishing_resistant_authentication() -> None:
    tenant_id = uid()
    source = source_identity(tenant_id)
    target = target_identity(tenant_id)

    with pytest.raises(
        PermissionError,
        match="STEP_UP_REQUIRED",
    ):
        IdentityMergeService().merge(
            context=context(tenant_id, "PASSWORD_OTP"),
            actor_role="IDENTITY_ADMIN",
            source=source,
            target=target,
            expected_source_version=source.version,
            expected_target_version=target.version,
        )


def test_non_admin_merge_is_denied() -> None:
    tenant_id = uid()
    source = source_identity(tenant_id)
    target = target_identity(tenant_id)

    with pytest.raises(
        PermissionError,
        match="IDENTITY_MERGE_DENIED",
    ):
        IdentityMergeService().merge(
            context=context(tenant_id),
            actor_role="MEMBER",
            source=source,
            target=target,
            expected_source_version=source.version,
            expected_target_version=target.version,
        )


def test_source_version_conflict_is_rejected() -> None:
    tenant_id = uid()
    source = source_identity(tenant_id)
    target = target_identity(tenant_id)

    with pytest.raises(
        RuntimeError,
        match="CONCURRENCY_CONFLICT",
    ):
        IdentityMergeService().merge(
            context=context(tenant_id),
            actor_role="IDENTITY_ADMIN",
            source=source,
            target=target,
            expected_source_version=source.version + 1,
            expected_target_version=target.version,
        )


def test_target_version_conflict_is_rejected() -> None:
    tenant_id = uid()
    source = source_identity(tenant_id)
    target = target_identity(tenant_id)

    with pytest.raises(
        RuntimeError,
        match="CONCURRENCY_CONFLICT",
    ):
        IdentityMergeService().merge(
            context=context(tenant_id),
            actor_role="IDENTITY_ADMIN",
            source=source,
            target=target,
            expected_source_version=source.version,
            expected_target_version=target.version + 1,
        )


def test_duplicate_values_are_not_added_twice() -> None:
    tenant_id = uid()
    source = source_identity(tenant_id)
    target = target_identity(tenant_id)

    source = Identity(
        **{
            **source.__dict__,
            "contact_points": target.contact_points,
        }
    )

    result = IdentityMergeService().merge(
        context=context(tenant_id),
        actor_role="IDENTITY_ADMIN",
        source=source,
        target=target,
        expected_source_version=source.version,
        expected_target_version=target.version,
    )

    assert result.target_identity.contact_points == target.contact_points


def test_merge_event_is_immutable() -> None:
    tenant_id = uid()
    source = source_identity(tenant_id)
    target = target_identity(tenant_id)

    event = IdentityMergeService().merge(
        context=context(tenant_id),
        actor_role="IDENTITY_ADMIN",
        source=source,
        target=target,
        expected_source_version=source.version,
        expected_target_version=target.version,
    ).event

    assert isinstance(event, IdentityMergedEvent)

    with pytest.raises(FrozenInstanceError):
        event.event_type = "CHANGED"  # type: ignore[misc]
