# ruff: noqa: E501 -- test fixtures retain visible SQL contracts.
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from afritech.novaid.application.recovery import (
    AccountRecoveryService,
    RecoveryCodeService,
    RecoveryError,
    TenantWebAuthnPolicyService,
)
from afritech.novaid.persistence import NovaIDUnitOfWork


def uid() -> str:
    return str(uuid4())


def seed(tmp_path):
    uow, tenant, identity, member, admin, admin_member = (
        NovaIDUnitOfWork(tmp_path / "phase6c.sqlite"),
        uid(),
        uid(),
        uid(),
        uid(),
        uid(),
    )
    now = datetime.now(UTC)
    with uow:
        uow.create_tenant(tenant, "Recovery tenant", now)
        for subject, email in ((identity, "recover@example.com"), (admin, "admin@example.com")):
            uow.connection.execute(
                "INSERT INTO novaid_identities VALUES(?,?,?,?,?,?,?,?)",
                (subject, tenant, email, "ACTIVE", now.isoformat(), now.isoformat(), 1, 1),
            )
        uow.connection.execute(
            "INSERT INTO novaid_tenant_memberships VALUES(?,?,?,?,?,?,?,?)",
            (member, tenant, identity, "MEMBER", "ACTIVE", now.isoformat(), now.isoformat(), 1),
        )
        uow.connection.execute(
            "INSERT INTO novaid_tenant_memberships VALUES(?,?,?,?,?,?,?,?)",
            (
                admin_member,
                tenant,
                admin,
                "SECURITY_ADMIN",
                "ACTIVE",
                now.isoformat(),
                now.isoformat(),
                1,
            ),
        )
        sessions = []
        for subject, membership in ((identity, member), (admin, admin_member)):
            session = uid()
            sessions.append(session)
            uow.connection.execute(
                "INSERT INTO novaid_authentication_sessions(session_id,tenant_id,identity_id,"
                "authentication_time,authentication_strength,risk_score,status,created_at,last_seen_at,"
                "expires_at,version,membership_id,authenticated_at,idle_expires_at,absolute_expires_at,"
                "step_up_expires_at,authentication_methods,security_version) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    session,
                    tenant,
                    subject,
                    now.isoformat(),
                    "PHISHING_RESISTANT",
                    0.0,
                    "ACTIVE",
                    now.isoformat(),
                    now.isoformat(),
                    (now + timedelta(hours=12)).isoformat(),
                    1,
                    membership,
                    now.isoformat(),
                    (now + timedelta(minutes=30)).isoformat(),
                    (now + timedelta(hours=12)).isoformat(),
                    (now + timedelta(minutes=5)).isoformat(),
                    '["WEBAUTHN"]',
                    1,
                ),
            )
    codes = RecoveryCodeService(uow, pepper=b"phase-6c-recovery-pepper-at-least-32")
    return uow, codes, tenant, identity, member, sessions[0], admin, sessions[1]


def test_recovery_codes_are_one_time_hashed_and_regeneration_supersedes(tmp_path) -> None:
    uow, codes, tenant, identity, _, session, _, _ = seed(tmp_path)
    generated = codes.generate_codes(
        tenant_id=tenant, identity_id=identity, session_id=session, count=3
    )
    plaintext = generated["codes"][0]
    rows = uow.connection.execute(
        "SELECT code_hash,status FROM novaid_recovery_codes WHERE batch_id=?",
        (generated["batch_id"],),
    ).fetchall()
    assert len(rows) == 3
    assert all(plaintext not in row["code_hash"] for row in rows)
    codes.consume_code(tenant_id=tenant, identity_id=identity, code=plaintext)
    with pytest.raises(RecoveryError, match="RECOVERY_CODE_INVALID"):
        codes.consume_code(tenant_id=tenant, identity_id=identity, code=plaintext)
    replacement = codes.generate_codes(
        tenant_id=tenant, identity_id=identity, session_id=session, count=2
    )
    assert replacement["batch_id"] != generated["batch_id"]
    assert codes.remaining(tenant_id=tenant, identity_id=identity) == 2


def test_governed_recovery_contains_sessions_credentials_and_tokens(tmp_path) -> None:
    uow, codes, tenant, identity, member, session, admin, _ = seed(tmp_path)
    generated = codes.generate_codes(
        tenant_id=tenant, identity_id=identity, session_id=session, count=2
    )
    now = datetime.now(UTC)
    with uow:
        uow.connection.execute(
            "INSERT INTO novaid_refresh_token_families VALUES(?,?,?,?,?,?,?,?,?)",
            (
                uid(),
                session,
                identity,
                tenant,
                "ACTIVE",
                now.isoformat(),
                (now + timedelta(days=1)).isoformat(),
                None,
                1,
            ),
        )
        uow.connection.execute(
            "INSERT INTO novaid_webauthn_credentials(credential_id,tenant_id,identity_id,membership_id,"
            "user_handle,public_key_cose,public_key_algorithm,sign_count,aaguid,attestation_format,"
            "attestation_type,transports,backup_eligible,backup_state,discoverable,resident_key,"
            "user_verification,created_at,status,version) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "credential",
                tenant,
                identity,
                member,
                b"u",
                b"key",
                -7,
                0,
                "a",
                "none",
                "none",
                "[]",
                0,
                0,
                1,
                1,
                1,
                now.isoformat(),
                "ACTIVE",
                1,
            ),
        )
    recovery = AccountRecoveryService(uow, codes)
    requested = recovery.request_recovery(
        tenant_id=tenant,
        identifier="recover@example.com",
        recovery_method="RECOVERY_CODE",
        correlation_id=uid(),
        request_id=uid(),
    )
    recovery.verify_recovery_code(
        tenant_id=tenant,
        recovery_request_id=requested["recovery_request_id"],
        code=generated["codes"][0],
        correlation_id=uid(),
        request_id=uid(),
    )
    recovery.approve(
        tenant_id=tenant,
        recovery_request_id=requested["recovery_request_id"],
        approver_identity_id=admin,
        reason="verified support case",
    )
    recovery.complete(tenant_id=tenant, recovery_request_id=requested["recovery_request_id"])
    assert (
        uow.connection.execute(
            "SELECT status FROM novaid_authentication_sessions WHERE session_id=?", (session,)
        ).fetchone()[0]
        == "REVOKED"
    )
    assert (
        uow.connection.execute(
            "SELECT status FROM novaid_webauthn_credentials WHERE credential_id='credential'"
        ).fetchone()[0]
        == "SUSPENDED"
    )
    with pytest.raises(RecoveryError, match="ACCOUNT_RECOVERY_DENIED"):
        recovery.complete(tenant_id=tenant, recovery_request_id=requested["recovery_request_id"])


def test_tenant_policy_requires_admin_fresh_step_up_and_optimistic_version(tmp_path) -> None:
    store, _, tenant, identity, _, user_session, admin, admin_session = seed(tmp_path)
    policies = TenantWebAuthnPolicyService(store)
    with pytest.raises(RecoveryError, match="POLICY_CHANGE_DENIED"):
        policies.set_policy(
            tenant_id=tenant,
            actor_identity_id=identity,
            session_id=user_session,
            policy={},
            expected_version=None,
            reason="unauthorized",
        )
    created = policies.set_policy(
        tenant_id=tenant,
        actor_identity_id=admin,
        session_id=admin_session,
        policy={"passwordless_enabled": False},
        expected_version=None,
        reason="tenant mandate",
    )
    assert created["version"] == 1 and not created["passwordless_enabled"]
    with pytest.raises(RecoveryError, match="POLICY_VERSION_CONFLICT"):
        policies.set_policy(
            tenant_id=tenant,
            actor_identity_id=admin,
            session_id=admin_session,
            policy={},
            expected_version=0,
            reason="stale update",
        )


def test_recovery_terminal_states_cannot_reopen(tmp_path) -> None:
    uow, codes, tenant, identity, _, _, admin, _ = seed(tmp_path)
    recovery = AccountRecoveryService(uow, codes)
    rejected = recovery.request_recovery(
        tenant_id=tenant,
        identifier="recover@example.com",
        recovery_method="ADMIN_ASSISTED",
        correlation_id=uid(),
        request_id=uid(),
    )
    recovery.reject(
        tenant_id=tenant,
        recovery_request_id=rejected["recovery_request_id"],
        approver_identity_id=admin,
        reason="evidence mismatch",
    )
    with pytest.raises(RecoveryError, match="ACCOUNT_RECOVERY_DENIED"):
        recovery.cancel(
            tenant_id=tenant,
            recovery_request_id=rejected["recovery_request_id"],
            identity_id=identity,
        )
    # A request outside the cooldown can be expired deterministically.
    with uow:
        uow.connection.execute(
            "UPDATE novaid_account_recovery_requests SET requested_at=?,expires_at=? "
            "WHERE recovery_request_id=?",
            (
                (datetime.now(UTC) - timedelta(hours=2)).isoformat(),
                (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
                rejected["recovery_request_id"],
            ),
        )
    assert recovery.expire_stale(tenant_id=tenant) == 0
