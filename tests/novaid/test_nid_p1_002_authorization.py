from datetime import UTC, datetime, timedelta

import pytest

from afritech.novaid.domain import (
    AssuranceLevel,
    AuthenticationStrength,
    AuthorizationContext,
    AuthorizationOutcome,
    AuthorizationPolicyEngine,
    MembershipLifecycleService,
    MembershipStatus,
    Permission,
    PermissionEffect,
    RequestContext,
    Role,
    TenantMembership,
)


NOW = datetime(2026, 7, 29, tzinfo=UTC)


def membership(**overrides):
    values = {
        "membership_id": "mem-1",
        "tenant_id": "tenant-1",
        "identity_id": "identity-1",
        "role": "operator",
    }
    values.update(overrides)
    return TenantMembership(**values)


def context(**overrides):
    values = {
        "tenant_id": "tenant-1",
        "actor_identity_id": "identity-1",
        "actor_membership_id": "mem-1",
        "resource": "identity",
        "action": "read",
        "correlation_id": "corr-1",
        "request_id": "req-1",
        "authentication_strength": AuthenticationStrength.PASSWORD,
        "evaluated_at": NOW,
    }
    values.update(overrides)
    return AuthorizationContext(**values)


def role(*permissions, name="OPERATOR", tenant_id="tenant-1"):
    return Role(
        role_id=f"role-{name.lower()}",
        tenant_id=tenant_id,
        name=name,
        permissions=frozenset(permissions),
    )


def test_membership_normalizes_roles_permissions_and_status():
    aggregate = membership(
        role=" Operator ",
        status="ACTIVE",
        roles=frozenset({"Auditor"}),
        direct_permissions=frozenset({"Identity:Read"}),
    )
    assert aggregate.role == "OPERATOR"
    assert aggregate.roles == frozenset({"OPERATOR", "AUDITOR"})
    assert aggregate.direct_permissions == frozenset({"identity:read"})
    assert aggregate.status is MembershipStatus.ACTIVE


@pytest.mark.parametrize(
    ("source", "target"),
    [
        (MembershipStatus.INVITED, MembershipStatus.ACTIVE),
        (MembershipStatus.ACTIVE, MembershipStatus.SUSPENDED),
        (MembershipStatus.SUSPENDED, MembershipStatus.ACTIVE),
        (MembershipStatus.ACTIVE, MembershipStatus.REVOKED),
        (MembershipStatus.ACTIVE, MembershipStatus.EXPIRED),
    ],
)
def test_membership_governed_transitions(source, target):
    aggregate = membership(status=source)
    transitioned = aggregate.transition(target, now=NOW)
    assert transitioned.status is target
    assert transitioned.version == 2
    assert transitioned.updated_at == NOW


def test_terminal_membership_cannot_reactivate():
    with pytest.raises(ValueError, match="INVALID_MEMBERSHIP_TRANSITION"):
        membership(status=MembershipStatus.REVOKED).transition(MembershipStatus.ACTIVE)


def test_membership_validity_is_end_exclusive():
    aggregate = membership(valid_from=NOW, valid_until=NOW + timedelta(hours=1))
    assert aggregate.is_effective(now=NOW)
    assert not aggregate.is_effective(now=NOW + timedelta(hours=1))


def test_membership_service_enforces_tenant_and_version_and_emits_event():
    request = RequestContext(
        "tenant-1", "admin-1", "admin-mem", "corr-1", "req-1", "MFA"
    )
    result = MembershipLifecycleService().suspend(
        context=request, membership=membership(), expected_version=1
    )
    assert result.membership.status is MembershipStatus.SUSPENDED
    assert result.event.event_type == "MEMBERSHIP_SUSPENDED"
    assert result.event.membership_version == 2

    with pytest.raises(PermissionError, match="TENANT_ACCESS_DENIED"):
        MembershipLifecycleService().suspend(
            context=RequestContext(
                "tenant-2", "admin-1", "admin-mem", "corr-1", "req-1", "MFA"
            ),
            membership=membership(),
            expected_version=1,
        )
    with pytest.raises(RuntimeError, match="CONCURRENCY_CONFLICT"):
        MembershipLifecycleService().suspend(
            context=request, membership=membership(), expected_version=2
        )


def test_policy_is_deny_by_default():
    decision = AuthorizationPolicyEngine().evaluate(
        context=context(), membership=membership()
    )
    assert decision.outcome is AuthorizationOutcome.DENY
    assert decision.reason_codes == ("PERMISSION_NOT_GRANTED",)


def test_policy_allows_matching_role_permission():
    permission = Permission("identity", "read")
    decision = AuthorizationPolicyEngine().evaluate(
        context=context(), membership=membership(), roles=(role(permission),)
    )
    assert decision.allowed
    assert decision.matched_permissions == ("identity:read",)


def test_policy_supports_resource_and_action_wildcards():
    permission = Permission("identity.*", "*")
    decision = AuthorizationPolicyEngine().evaluate(
        context=context(resource="identity.profile", action="update"),
        membership=membership(),
        roles=(role(permission),),
    )
    assert decision.allowed


@pytest.mark.parametrize(
    ("context_override", "membership_override", "reason"),
    [
        ({"resource_tenant_id": "tenant-2"}, {}, "CROSS_TENANT_RESOURCE"),
        ({}, {"tenant_id": "tenant-2"}, "CROSS_TENANT_MEMBERSHIP"),
        ({"actor_identity_id": "identity-2"}, {}, "ACTOR_MEMBERSHIP_MISMATCH"),
        ({"actor_membership_id": "mem-2"}, {}, "MEMBERSHIP_CONTEXT_MISMATCH"),
        ({}, {"status": MembershipStatus.SUSPENDED}, "MEMBERSHIP_SUSPENDED"),
        ({"risk_score": 0.95}, {}, "CRITICAL_RISK"),
    ],
)
def test_policy_rejects_invalid_security_boundaries(
    context_override, membership_override, reason
):
    decision = AuthorizationPolicyEngine().evaluate(
        context=context(**context_override),
        membership=membership(**membership_override),
        roles=(role(Permission("identity", "read")),),
    )
    assert decision.outcome is AuthorizationOutcome.DENY
    assert decision.reason_codes == (reason,)


def test_explicit_deny_overrides_allow():
    decision = AuthorizationPolicyEngine().evaluate(
        context=context(),
        membership=membership(),
        roles=(
            role(
                Permission("identity", "read"),
                Permission("identity", "read", PermissionEffect.DENY),
            ),
        ),
    )
    assert decision.reason_codes == ("EXPLICIT_DENY",)


@pytest.mark.parametrize(
    ("permission", "context_override", "reason"),
    [
        (
            Permission("identity", "read", require_trusted_device=True),
            {},
            "TRUSTED_DEVICE_REQUIRED",
        ),
        (
            Permission(
                "identity",
                "read",
                minimum_assurance_level=AssuranceLevel.NID_AL2,
            ),
            {},
            "ASSURANCE_LEVEL_INSUFFICIENT",
        ),
        (
            Permission(
                "identity",
                "read",
                minimum_authentication_strength=AuthenticationStrength.FIDO2,
            ),
            {},
            "AUTHENTICATION_STRENGTH_INSUFFICIENT",
        ),
    ],
)
def test_policy_requests_step_up(permission, context_override, reason):
    decision = AuthorizationPolicyEngine().evaluate(
        context=context(**context_override),
        membership=membership(),
        roles=(role(permission),),
    )
    assert decision.outcome is AuthorizationOutcome.REQUIRE_STEP_UP
    assert decision.reason_codes == (reason,)


def test_owner_only_permission_checks_actor():
    permission = Permission("profile", "update", resource_owner_only=True)
    denied = AuthorizationPolicyEngine().evaluate(
        context=context(
            resource="profile", action="update", resource_owner_id="identity-2"
        ),
        membership=membership(),
        roles=(role(permission),),
    )
    allowed = AuthorizationPolicyEngine().evaluate(
        context=context(
            resource="profile", action="update", resource_owner_id="identity-1"
        ),
        membership=membership(),
        roles=(role(permission),),
    )
    assert denied.reason_codes == ("RESOURCE_OWNERSHIP_REQUIRED",)
    assert allowed.allowed


def test_direct_permission_is_authoritative_grant():
    decision = AuthorizationPolicyEngine().evaluate(
        context=context(),
        membership=membership(direct_permissions=frozenset({"identity:read"})),
    )
    assert decision.allowed
