from datetime import UTC, datetime

from afritech.novaid.domain import Permission, Role
from afritech.novaid.persistence.migrations import EXPECTED_REVISIONS
from afritech.novaid.persistence.sqlite import NovaIDUnitOfWork


NOW = datetime(2026, 7, 29, tzinfo=UTC)


def seed_membership(uow):
    uow.create_tenant("tenant-1", "Tenant One", NOW)
    uow.connection.execute(
        "INSERT INTO novaid_identities("
        "identity_id,tenant_id,normalized_email,status,created_at,updated_at"
        ") VALUES(?,?,?,?,?,?)",
        (
            "identity-1",
            "tenant-1",
            "person@example.test",
            "ACTIVE",
            NOW.isoformat(),
            NOW.isoformat(),
        ),
    )
    uow.create_registration_membership(
        "mem-1", "tenant-1", "identity-1", now=NOW.isoformat()
    )


def test_authorization_schema_and_repository_round_trip():
    with NovaIDUnitOfWork() as uow:
        seed_membership(uow)
        permission = Permission("identity", "read", tenant_id="tenant-1")
        assigned_role = Role("role-1", "tenant-1", "OPERATOR", frozenset({permission}))
        uow.authorization.put_permission(
            permission_id="permission-1", permission=permission, now=NOW
        )
        uow.authorization.put_role(assigned_role, now=NOW)
        uow.authorization.grant_permission(
            tenant_id="tenant-1",
            role_id="role-1",
            permission_id="permission-1",
            now=NOW,
        )
        uow.authorization.assign_role(
            tenant_id="tenant-1",
            membership_id="mem-1",
            role_id="role-1",
            now=NOW,
        )
        rows = uow.authorization.list_effective_permissions(
            tenant_id="tenant-1", membership_id="mem-1", now=NOW
        )
        assert [(row["resource"], row["action"], row["effect"]) for row in rows] == [
            ("identity", "read", "ALLOW")
        ]


def test_expired_assignment_is_not_effective():
    with NovaIDUnitOfWork() as uow:
        seed_membership(uow)
        permission = Permission("identity", "read")
        uow.authorization.put_permission(
            permission_id="permission-1", permission=permission, now=NOW
        )
        uow.authorization.put_role(Role("role-1", "tenant-1", "OPERATOR"), now=NOW)
        uow.authorization.grant_permission(
            tenant_id="tenant-1",
            role_id="role-1",
            permission_id="permission-1",
            now=NOW,
        )
        uow.authorization.assign_role(
            tenant_id="tenant-1",
            membership_id="mem-1",
            role_id="role-1",
            now=NOW,
            valid_until=NOW,
        )
        assert (
            uow.authorization.list_effective_permissions(
                tenant_id="tenant-1", membership_id="mem-1", now=NOW
            )
            == []
        )


def test_policy_version_is_immutable_and_tenant_scoped():
    with NovaIDUnitOfWork() as uow:
        uow.create_tenant("tenant-1", "Tenant One", NOW)
        uow.authorization.put_policy_version(
            tenant_id="tenant-1",
            policy_version="NID-P1-002.1",
            status="ACTIVE",
            policy={"default": "DENY"},
            created_by="identity-admin",
            now=NOW,
        )
        row = uow.connection.execute(
            "SELECT * FROM novaid_authorization_policy_versions "
            "WHERE tenant_id=? AND policy_version=?",
            ("tenant-1", "NID-P1-002.1"),
        ).fetchone()
        assert row["status"] == "ACTIVE"
        assert row["policy_json"] == '{"default":"DENY"}'


def test_certification_revision_is_registered():
    assert EXPECTED_REVISIONS[-1] == "0010_tenant_authorization.sql"
