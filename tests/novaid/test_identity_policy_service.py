from dataclasses import FrozenInstanceError

import pytest

from afritech.novaid.domain import (
    IdentityStatus,
    VerificationStatus,
)
from afritech.novaid.domain.identity_policy import (
    IdentityPolicyDecision,
    IdentityPolicyOperation,
    IdentityPolicyService,
)


def evaluate(
    operation: IdentityPolicyOperation,
    *,
    role: str = "MEMBER",
    strength: str = "PASSWORD_OTP",
    same_identity: bool = False,
    identity_status: IdentityStatus = IdentityStatus.ACTIVE,
    verification_status: VerificationStatus = VerificationStatus.VERIFIED,
):
    return IdentityPolicyService().evaluate(
        operation=operation,
        actor_role=role,
        authentication_strength=strength,
        same_identity=same_identity,
        identity_status=identity_status,
        verification_status=verification_status,
    )


def test_authenticated_user_may_view_own_identity() -> None:
    result = evaluate(
        IdentityPolicyOperation.VIEW_IDENTITY,
        same_identity=True,
    )

    assert result.decision is IdentityPolicyDecision.ALLOW
    assert result.reason_codes == ("SELF_SERVICE_VIEW",)


def test_member_cannot_view_another_identity() -> None:
    result = evaluate(
        IdentityPolicyOperation.VIEW_IDENTITY,
        same_identity=False,
    )

    assert result.decision is IdentityPolicyDecision.DENY


def test_observer_may_view_identity() -> None:
    result = evaluate(
        IdentityPolicyOperation.VIEW_IDENTITY,
        role="OBSERVER",
    )

    assert result.decision is IdentityPolicyDecision.ALLOW


def test_password_only_profile_update_requires_step_up() -> None:
    result = evaluate(
        IdentityPolicyOperation.UPDATE_PROFILE,
        same_identity=True,
        strength="PASSWORD",
    )

    assert result.decision is IdentityPolicyDecision.REQUIRE_STEP_UP
    assert result.reason_codes == (
        "PROFILE_UPDATE_STEP_UP_REQUIRED",
    )


def test_verified_self_profile_update_is_allowed() -> None:
    result = evaluate(
        IdentityPolicyOperation.UPDATE_PROFILE,
        same_identity=True,
        strength="PASSWORD_OTP",
    )

    assert result.decision is IdentityPolicyDecision.ALLOW


def test_non_admin_lifecycle_management_is_denied() -> None:
    result = evaluate(
        IdentityPolicyOperation.MANAGE_LIFECYCLE,
        role="MEMBER",
    )

    assert result.decision is IdentityPolicyDecision.DENY


def test_admin_lifecycle_management_is_allowed_with_mfa() -> None:
    result = evaluate(
        IdentityPolicyOperation.MANAGE_LIFECYCLE,
        role="ADMIN",
        strength="PASSWORD_OTP",
    )

    assert result.decision is IdentityPolicyDecision.ALLOW


def test_verifier_may_manage_verification() -> None:
    result = evaluate(
        IdentityPolicyOperation.MANAGE_VERIFICATION,
        role="VERIFIER",
        strength="PASSWORD_OTP",
    )

    assert result.decision is IdentityPolicyDecision.ALLOW


def test_merge_requires_phishing_resistant_authentication() -> None:
    result = evaluate(
        IdentityPolicyOperation.MERGE_IDENTITIES,
        role="IDENTITY_ADMIN",
        strength="PASSWORD_OTP",
    )

    assert result.decision is IdentityPolicyDecision.REQUIRE_STEP_UP
    assert result.reason_codes == (
        "IDENTITY_MERGE_STEP_UP_REQUIRED",
    )


def test_merge_requires_verified_target() -> None:
    result = evaluate(
        IdentityPolicyOperation.MERGE_IDENTITIES,
        role="IDENTITY_ADMIN",
        strength="PHISHING_RESISTANT",
        verification_status=VerificationStatus.IN_PROGRESS,
    )

    assert result.decision is IdentityPolicyDecision.DENY
    assert result.reason_codes == (
        "IDENTITY_MERGE_REQUIRES_VERIFIED_TARGET",
    )


def test_delete_requires_disabled_identity() -> None:
    result = evaluate(
        IdentityPolicyOperation.DELETE_IDENTITY,
        role="SECURITY_ADMIN",
        strength="PHISHING_RESISTANT",
        identity_status=IdentityStatus.ACTIVE,
    )

    assert result.decision is IdentityPolicyDecision.DENY
    assert result.reason_codes == (
        "IDENTITY_DELETE_REQUIRES_DISABLED_STATE",
    )


def test_delete_disabled_identity_is_allowed_for_strong_admin() -> None:
    result = evaluate(
        IdentityPolicyOperation.DELETE_IDENTITY,
        role="SECURITY_ADMIN",
        strength="PHISHING_RESISTANT",
        identity_status=IdentityStatus.DISABLED,
    )

    assert result.decision is IdentityPolicyDecision.ALLOW


def test_deleted_identity_fails_closed() -> None:
    result = evaluate(
        IdentityPolicyOperation.VIEW_IDENTITY,
        role="ADMIN",
        identity_status=IdentityStatus.DELETED,
    )

    assert result.decision is IdentityPolicyDecision.DENY
    assert result.reason_codes == ("IDENTITY_DELETED",)


def test_unknown_role_fails_closed_for_privileged_operation() -> None:
    result = evaluate(
        IdentityPolicyOperation.MANAGE_LIFECYCLE,
        role="UNKNOWN_ROLE",
    )

    assert result.decision is IdentityPolicyDecision.DENY


def test_unsupported_authentication_strength_fails_closed() -> None:
    result = evaluate(
        IdentityPolicyOperation.VIEW_IDENTITY,
        role="ADMIN",
        strength="UNKNOWN",
    )

    assert result.decision is IdentityPolicyDecision.DENY
    assert result.reason_codes == (
        "UNSUPPORTED_AUTHENTICATION_STRENGTH",
    )


def test_policy_result_and_service_are_immutable() -> None:
    service = IdentityPolicyService()
    result = evaluate(
        IdentityPolicyOperation.VIEW_IDENTITY,
        same_identity=True,
    )

    with pytest.raises(FrozenInstanceError):
        service.changed = True  # type: ignore[attr-defined]

    with pytest.raises(FrozenInstanceError):
        result.decision = IdentityPolicyDecision.DENY  # type: ignore[misc]
