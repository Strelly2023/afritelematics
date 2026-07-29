from __future__ import annotations

from datetime import datetime
import json
from typing import Any

from ..domain.authorization import Permission, Role


class AuthorizationRepository:
    """Tenant-bound authorization persistence shared by both SQL adapters."""

    def __init__(self, connection: Any) -> None:
        self.connection = connection

    def put_permission(
        self,
        *,
        permission_id: str,
        permission: Permission,
        now: datetime,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_permissions("
            "permission_id,tenant_id,resource,action,effect,resource_owner_only,"
            "require_trusted_device,minimum_assurance_level,minimum_authentication_strength,created_at"
            ") VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                permission_id,
                permission.tenant_id,
                permission.resource,
                permission.action,
                permission.effect.value,
                permission.resource_owner_only,
                permission.require_trusted_device,
                permission.minimum_assurance_level.value,
                permission.minimum_authentication_strength.value,
                now.isoformat(),
            ),
        )

    def put_role(self, role: Role, *, now: datetime) -> None:
        self.connection.execute(
            "INSERT INTO novaid_roles"
            "(role_id,tenant_id,name,enabled,created_at,updated_at,version) "
            "VALUES(?,?,?,?,?,?,?)",
            (
                role.role_id,
                role.tenant_id,
                role.name,
                role.enabled,
                now.isoformat(),
                now.isoformat(),
                role.version,
            ),
        )

    def grant_permission(
        self,
        *,
        tenant_id: str,
        role_id: str,
        permission_id: str,
        now: datetime,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_role_permissions"
            "(tenant_id,role_id,permission_id,created_at) VALUES(?,?,?,?)",
            (tenant_id, role_id, permission_id, now.isoformat()),
        )

    def assign_role(
        self,
        *,
        tenant_id: str,
        membership_id: str,
        role_id: str,
        now: datetime,
        valid_from: datetime | None = None,
        valid_until: datetime | None = None,
    ) -> None:
        if valid_from and valid_until and valid_until <= valid_from:
            raise ValueError("INVALID_ROLE_ASSIGNMENT_VALIDITY")
        self.connection.execute(
            "INSERT INTO novaid_membership_roles"
            "(tenant_id,membership_id,role_id,valid_from,valid_until,created_at) "
            "VALUES(?,?,?,?,?,?)",
            (
                tenant_id,
                membership_id,
                role_id,
                valid_from.isoformat() if valid_from else None,
                valid_until.isoformat() if valid_until else None,
                now.isoformat(),
            ),
        )

    def list_effective_permissions(
        self, *, tenant_id: str, membership_id: str, now: datetime
    ) -> list[Any]:
        return self.connection.execute(
            "SELECT p.* FROM novaid_permissions p "
            "JOIN novaid_role_permissions rp ON rp.permission_id=p.permission_id "
            "JOIN novaid_membership_roles mr ON mr.role_id=rp.role_id "
            "AND mr.tenant_id=rp.tenant_id "
            "WHERE mr.tenant_id=? AND mr.membership_id=? "
            "AND (mr.valid_from IS NULL OR mr.valid_from<=?) "
            "AND (mr.valid_until IS NULL OR mr.valid_until>?)",
            (tenant_id, membership_id, now.isoformat(), now.isoformat()),
        ).fetchall()

    def put_policy_version(
        self,
        *,
        tenant_id: str,
        policy_version: str,
        status: str,
        policy: dict[str, Any],
        created_by: str,
        now: datetime,
    ) -> None:
        normalized_status = status.strip().upper()
        if normalized_status not in {"DRAFT", "ACTIVE", "RETIRED"}:
            raise ValueError("INVALID_POLICY_STATUS")
        self.connection.execute(
            "INSERT INTO novaid_authorization_policy_versions"
            "(tenant_id,policy_version,status,policy_json,created_at,activated_at,created_by) "
            "VALUES(?,?,?,?,?,?,?)",
            (
                tenant_id,
                policy_version,
                normalized_status,
                json.dumps(policy, sort_keys=True, separators=(",", ":")),
                now.isoformat(),
                now.isoformat() if normalized_status == "ACTIVE" else None,
                created_by,
            ),
        )
