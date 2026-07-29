from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from afritech.novaid.domain import (
    AssuranceLevel,
    AuthenticationStrength,
    Tenant,
    TenantSecurityPolicy,
    TenantStatus,
)


def test_default_security_policy_is_secure() -> None:
    policy = TenantSecurityPolicy()

    assert (
        policy.minimum_authentication_strength
        is AuthenticationStrength.PASSWORD_OTP
    )
    assert (
        policy.minimum_assurance_level
        is AssuranceLevel.NID_AL1
    )
    assert policy.mfa_required is True
    assert (
        policy.phishing_resistant_authentication_required
        is False
    )
    assert policy.audit_logging_required is True
    assert policy.immutable_audit_required is True
    assert policy.pii_encryption_required is True
    assert policy.minimum_password_length == 12
    assert policy.risk_step_up_threshold == 0.60
    assert policy.risk_lock_threshold == 0.90


@pytest.mark.parametrize(
    "strength",
    (
        AuthenticationStrength.PASSWORD_OTP,
        AuthenticationStrength.MFA,
        AuthenticationStrength.FIDO2,
        AuthenticationStrength.PASSKEY,
        AuthenticationStrength.CERTIFICATE,
        AuthenticationStrength.PHISHING_RESISTANT,
    ),
)
def test_default_policy_allows_sufficient_strengths(
    strength: AuthenticationStrength,
) -> None:
    assert (
        TenantSecurityPolicy()
        .allows_authentication_strength(strength)
        is True
    )


def test_default_policy_rejects_password_only() -> None:
    assert (
        TenantSecurityPolicy()
        .allows_authentication_strength(
            AuthenticationStrength.PASSWORD
        )
        is False
    )


def test_unknown_authentication_strength_fails_closed() -> None:
    assert (
        TenantSecurityPolicy()
        .allows_authentication_strength(
            "UNKNOWN"
        )
        is False
    )


@pytest.mark.parametrize(
    "strength",
    (
        AuthenticationStrength.FIDO2,
        AuthenticationStrength.PASSKEY,
        AuthenticationStrength.CERTIFICATE,
        AuthenticationStrength.PHISHING_RESISTANT,
    ),
)
def test_phishing_resistant_policy_accepts_strong_methods(
    strength: AuthenticationStrength,
) -> None:
    policy = TenantSecurityPolicy(
        minimum_authentication_strength=(
            AuthenticationStrength.PASSKEY
        ),
        phishing_resistant_authentication_required=True,
    )

    assert policy.allows_authentication_strength(
        strength
    ) is True


def test_phishing_resistant_policy_rejects_otp() -> None:
    policy = TenantSecurityPolicy(
        minimum_authentication_strength=(
            AuthenticationStrength.PASSKEY
        ),
        phishing_resistant_authentication_required=True,
    )

    assert policy.allows_authentication_strength(
        AuthenticationStrength.PASSWORD_OTP
    ) is False


def test_invalid_phishing_resistant_configuration_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="PHISHING_RESISTANT_STRENGTH_REQUIRED",
    ):
        TenantSecurityPolicy(
            minimum_authentication_strength=(
                AuthenticationStrength.PASSWORD_OTP
            ),
            phishing_resistant_authentication_required=True,
        )


def test_mfa_required_rejects_password_minimum() -> None:
    with pytest.raises(
        ValueError,
        match="MFA_CAPABLE_STRENGTH_REQUIRED",
    ):
        TenantSecurityPolicy(
            minimum_authentication_strength=(
                AuthenticationStrength.PASSWORD
            ),
            mfa_required=True,
        )


@pytest.mark.parametrize(
    ("idle", "absolute", "error"),
    (
        (
            0,
            720,
            "INVALID_SESSION_IDLE_TIMEOUT",
        ),
        (
            30,
            29,
            "INVALID_SESSION_ABSOLUTE_TIMEOUT",
        ),
    ),
)
def test_invalid_session_timeouts_are_rejected(
    idle: int,
    absolute: int,
    error: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=error,
    ):
        TenantSecurityPolicy(
            session_idle_timeout_minutes=idle,
            session_absolute_timeout_minutes=absolute,
        )


@pytest.mark.parametrize(
    ("field", "value", "error"),
    (
        (
            "maximum_concurrent_sessions",
            0,
            "INVALID_MAXIMUM_CONCURRENT_SESSIONS",
        ),
        (
            "maximum_registered_devices",
            0,
            "INVALID_MAXIMUM_REGISTERED_DEVICES",
        ),
        (
            "minimum_password_length",
            7,
            "MINIMUM_PASSWORD_LENGTH_TOO_SHORT",
        ),
        (
            "password_history_count",
            -1,
            "INVALID_PASSWORD_HISTORY_COUNT",
        ),
        (
            "password_rotation_days",
            0,
            "INVALID_PASSWORD_ROTATION_DAYS",
        ),
    ),
)
def test_invalid_security_limits_are_rejected(
    field: str,
    value: int,
    error: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=error,
    ):
        TenantSecurityPolicy(
            **{field: value},
        )


@pytest.mark.parametrize(
    ("step_up", "lock", "error"),
    (
        (
            -0.1,
            0.9,
            "INVALID_RISK_STEP_UP_THRESHOLD",
        ),
        (
            0.6,
            1.1,
            "INVALID_RISK_LOCK_THRESHOLD",
        ),
        (
            0.9,
            0.9,
            "INVALID_RISK_THRESHOLD_ORDER",
        ),
        (
            0.95,
            0.90,
            "INVALID_RISK_THRESHOLD_ORDER",
        ),
    ),
)
def test_invalid_risk_thresholds_are_rejected(
    step_up: float,
    lock: float,
    error: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=error,
    ):
        TenantSecurityPolicy(
            risk_step_up_threshold=step_up,
            risk_lock_threshold=lock,
        )


def test_step_up_is_required_for_elevated_risk() -> None:
    policy = TenantSecurityPolicy()

    assert policy.requires_step_up(
        authentication_strength=(
            AuthenticationStrength.MFA
        ),
        risk_score=0.70,
    ) is True


def test_step_up_is_required_for_weak_authentication() -> None:
    policy = TenantSecurityPolicy()

    assert policy.requires_step_up(
        authentication_strength=(
            AuthenticationStrength.PASSWORD
        ),
        risk_score=0.10,
    ) is True


def test_step_up_not_required_when_controls_are_satisfied() -> None:
    policy = TenantSecurityPolicy()

    assert policy.requires_step_up(
        authentication_strength=(
            AuthenticationStrength.PASSKEY
        ),
        risk_score=0.10,
    ) is False


def test_lock_is_required_at_lock_threshold() -> None:
    policy = TenantSecurityPolicy()

    assert policy.requires_lock(
        risk_score=0.90,
    ) is True

    assert policy.requires_lock(
        risk_score=0.89,
    ) is False


@pytest.mark.parametrize(
    "risk_score",
    (
        -0.1,
        1.1,
    ),
)
def test_invalid_risk_score_is_rejected(
    risk_score: float,
) -> None:
    policy = TenantSecurityPolicy()

    with pytest.raises(
        ValueError,
        match="INVALID_RISK_SCORE",
    ):
        policy.requires_step_up(
            authentication_strength=(
                AuthenticationStrength.MFA
            ),
            risk_score=risk_score,
        )

    with pytest.raises(
        ValueError,
        match="INVALID_RISK_SCORE",
    ):
        policy.requires_lock(
            risk_score=risk_score,
        )


def test_security_policy_is_immutable() -> None:
    policy = TenantSecurityPolicy()

    with pytest.raises(FrozenInstanceError):
        policy.mfa_required = False  # type: ignore[misc]


def test_tenant_uses_default_security_policy() -> None:
    tenant = Tenant(
        tenant_id="tenant-default-security",
        name="Default Security Tenant",
    )

    assert isinstance(
        tenant.security_policy,
        TenantSecurityPolicy,
    )
    assert tenant.security_policy.mfa_required is True


def test_tenant_accepts_custom_security_policy() -> None:
    policy = TenantSecurityPolicy(
        minimum_authentication_strength=(
            AuthenticationStrength.PASSKEY
        ),
        minimum_assurance_level=AssuranceLevel.NID_AL2,
        phishing_resistant_authentication_required=True,
        device_binding_required=True,
        maximum_concurrent_sessions=3,
    )

    tenant = Tenant(
        tenant_id="tenant-custom-security",
        name="Custom Security Tenant",
        security_policy=policy,
    )

    assert tenant.security_policy is policy
    assert (
        tenant.security_policy.minimum_assurance_level
        is AssuranceLevel.NID_AL2
    )
    assert tenant.security_policy.device_binding_required is True


def test_tenant_transition_preserves_security_policy() -> None:
    policy = TenantSecurityPolicy(
        minimum_authentication_strength=(
            AuthenticationStrength.PASSKEY
        ),
        phishing_resistant_authentication_required=True,
    )

    tenant = Tenant(
        tenant_id="tenant-security-transition",
        name="Security Transition Tenant",
        security_policy=policy,
    )

    suspended = tenant.transition(
        TenantStatus.SUSPENDED,
    )

    assert suspended.security_policy is policy
    assert suspended.version == tenant.version + 1
