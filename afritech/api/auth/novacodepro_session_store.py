from __future__ import annotations

import base64
import hashlib
import json
import os
import sqlite3
import secrets
import hmac
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException, Request

from afritech.afriprogramming.rbac import canonical_role_name, role_definition
from afritech.novacodepro.auth_accounts import AUTH_PASSWORD, find_account


ACCESS_COOKIE_NAME = "novacodepro_access_token"
REFRESH_COOKIE_NAME = "novacodepro_refresh_token"
SESSION_COOKIE_NAME = "novacodepro_session"
CSRF_COOKIE_NAME = "novacodepro_csrf_token"

DEFAULT_IDLE_TIMEOUT_MINUTES = int(os.environ.get("NOVACODEPRO_IDLE_TIMEOUT_MINUTES", "30"))
DEFAULT_ABSOLUTE_TIMEOUT_HOURS = int(os.environ.get("NOVACODEPRO_ABSOLUTE_TIMEOUT_HOURS", "8"))
DEFAULT_WARNING_SECONDS = 120


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _canonical_roles(account: dict[str, Any]) -> list[str]:
    roles = account.get("assigned_roles")
    if roles:
        return [str(role).upper() for role in roles]
    return [str(account["role"]).upper()]


def _effective_permissions(role: str) -> list[str]:
    canonical = canonical_role_name(role)
    permissions = list(role_definition(canonical).get("permissions", ()))
    if canonical in {"ADMIN", "PLATFORM_ADMIN", "PLATFORM_OWNER", "SUPER_ADMIN", "SYSTEM_ADMIN"}:
        extras = [
            "workspace.read",
            "workspace.create",
            "workspace.update",
            "workspace.member.read",
            "workspace.member.manage",
            "workspace.settings.manage",
            "workspace.activity.read",
            "workspace.notification.read",
            "workspace.favorite.manage",
            "project.read",
            "project.create",
            "project.update",
            "project.archive",
            "project.member.manage",
            "project.milestone.manage",
            "project.work_item.manage",
            "project.risk.manage",
            "request.read",
            "request.create",
            "request.update",
            "request.submit",
            "request.assign",
            "request.comment",
            "request.transition",
            "request.archive",
            "notification.read",
            "attachment.upload",
            "attachment.read",
            "comment.create",
        ]
    elif canonical in {"DEVELOPER", "PRODUCT_MANAGER", "BUSINESS_ANALYST", "PROJECT_MANAGER", "ARCHITECT", "QA_ENGINEER", "DEVOPS_ENGINEER"}:
        extras = [
            "workspace.read",
            "workspace.update",
            "workspace.activity.read",
            "workspace.notification.read",
            "workspace.favorite.manage",
            "project.read",
            "project.create",
            "project.update",
            "project.archive",
            "project.member.manage",
            "project.milestone.manage",
            "project.work_item.manage",
            "project.risk.manage",
            "request.read",
            "request.create",
            "request.update",
            "request.submit",
            "request.assign",
            "request.comment",
            "request.transition",
            "request.archive",
            "notification.read",
            "attachment.upload",
            "attachment.read",
            "comment.create",
        ]
    elif canonical == "CUSTOMER":
        extras = [
            "workspace.read",
            "workspace.activity.read",
            "workspace.notification.read",
            "request.read",
            "request.create",
            "request.comment",
            "attachment.upload",
            "attachment.read",
            "comment.create",
            "notification.read",
        ]
    elif canonical == "AUDITOR":
        extras = [
            "workspace.read",
            "workspace.activity.read",
            "request.read",
            "notification.read",
        ]
    elif canonical == "EXTERNAL_REGULATOR":
        extras = [
            "workspace.read",
            "request.read",
        ]
    else:
        extras = [
            "workspace.read",
            "request.read",
            "notification.read",
        ]
    for permission in extras:
        if permission not in permissions:
            permissions.append(permission)
    return permissions


def _default_jwt_service() -> Any:
    return LocalJWTService()


def _b64url_encode(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")


def _b64url_decode(payload: str) -> bytes:
    padding = "=" * (-len(payload) % 4)
    return base64.urlsafe_b64decode(payload + padding)


@dataclass(frozen=True)
class SessionJWTClaims:
    sub: str
    role: str
    organization_id: str
    exp: int
    tenant_id: str | None = None
    workspace_id: str | None = None
    permissions: list[str] | tuple[str, ...] = ()
    sid: str | None = None
    token_kind: str = "access"


class LocalJWTService:
    def __init__(self, secret: str | None = None, ttl_seconds: int = 12 * 60 * 60) -> None:
        self.secret = (secret or os.environ.get("AFRITECH_JWT_SECRET") or secrets.token_urlsafe(48)).encode(
            "utf-8"
        )
        self.ttl_seconds = ttl_seconds

    def create_token(
        self,
        user_id: str,
        *,
        role: str = "OPERATOR",
        organization_id: str | None = None,
        session_id: str | None = None,
        token_kind: str = "access",
        issued_at: int | None = None,
    ) -> str:
        now = int(time.time()) if issued_at is None else issued_at
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": user_id,
            "role": role.upper(),
            "exp": now + self.ttl_seconds,
            "token_kind": token_kind,
        }
        if organization_id:
            payload["organization_id"] = organization_id
        if session_id:
            payload["sid"] = session_id
        signing_input = ".".join(
            (
                _b64url_encode(json.dumps(header, sort_keys=True, separators=(",", ":")).encode()),
                _b64url_encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()),
            )
        )
        signature = hmac.new(self.secret, signing_input.encode("ascii"), hashlib.sha256).digest()
        return f"{signing_input}.{_b64url_encode(signature)}"

    def verify_token(self, token: str, *, now: int | None = None) -> SessionJWTClaims:
        try:
            encoded_header, encoded_payload, encoded_signature = token.split(".")
        except ValueError as exc:
            raise ValueError("invalid_token") from exc
        signing_input = f"{encoded_header}.{encoded_payload}"
        expected = hmac.new(self.secret, signing_input.encode("ascii"), hashlib.sha256).digest()
        supplied = _b64url_decode(encoded_signature)
        if not hmac.compare_digest(expected, supplied):
            raise ValueError("invalid_signature")
        header = json.loads(_b64url_decode(encoded_header))
        if header.get("alg") != "HS256":
            raise ValueError("invalid_algorithm")
        payload = json.loads(_b64url_decode(encoded_payload))
        current_time = int(time.time()) if now is None else now
        if int(payload["exp"]) < current_time:
            raise ValueError("token_expired")
        organization_id = str(payload.get("organization_id", payload.get("tenant_id", "afritech-core")))
        return SessionJWTClaims(
            sub=str(payload["sub"]),
            role=str(payload.get("role", "OPERATOR")).upper(),
            organization_id=organization_id,
            exp=int(payload["exp"]),
            sid=str(payload["sid"]) if payload.get("sid") else None,
            token_kind=str(payload.get("token_kind", "access")),
        )


class NovaCodeProSessionStore:
    def __init__(
        self,
        db_path: Path | str,
        *,
        jwt_service: Any | None = None,
        idle_timeout_minutes: int = DEFAULT_IDLE_TIMEOUT_MINUTES,
        absolute_timeout_hours: int = DEFAULT_ABSOLUTE_TIMEOUT_HOURS,
    ) -> None:
        self.db_path = Path(db_path)
        self.jwt_service = jwt_service or _default_jwt_service()
        self.idle_timeout_minutes = idle_timeout_minutes
        self.absolute_timeout_hours = absolute_timeout_hours
        self._lock = threading.RLock()
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS novacodepro_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    email TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    organization TEXT NOT NULL,
                    active_role TEXT NOT NULL,
                    workspace_id TEXT,
                    assigned_roles TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    absolute_expires_at TEXT NOT NULL,
                    idle_expires_at TEXT NOT NULL,
                    access_token_hash TEXT NOT NULL,
                    refresh_token_hash TEXT NOT NULL,
                    csrf_token_hash TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS novacodepro_audit_events (
                    event_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    role TEXT NOT NULL,
                    organization TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            columns = {str(row[1]) for row in connection.execute("PRAGMA table_info(novacodepro_sessions)").fetchall()}
            if "workspace_id" not in columns:
                connection.execute("ALTER TABLE novacodepro_sessions ADD COLUMN workspace_id TEXT")
            connection.commit()

    def _record_event(
        self,
        *,
        event_type: str,
        actor: str,
        role: str,
        organization: str,
        payload: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO novacodepro_audit_events (
                    event_id, session_id, event_type, actor, role, organization, payload, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    secrets.token_hex(16),
                    session_id,
                    event_type,
                    actor,
                    role,
                    organization,
                    json.dumps(payload or {}, sort_keys=True),
                    _iso(_utcnow()),
                ),
            )
            connection.commit()

    def _load_session_row(self, session_id: str) -> sqlite3.Row | None:
        with self._connect() as connection:
            return connection.execute(
                "SELECT * FROM novacodepro_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()

    def _update_session(self, session_id: str, **fields: Any) -> None:
        if not fields:
            return
        columns = ", ".join(f"{key} = ?" for key in fields)
        values = list(fields.values()) + [session_id]
        with self._connect() as connection:
            connection.execute(
                f"UPDATE novacodepro_sessions SET {columns} WHERE session_id = ?",
                values,
            )
            connection.commit()

    def _session_payload(self, row: sqlite3.Row) -> dict[str, Any]:
        canonical_role = canonical_role_name(str(row["active_role"]))
        permissions = _effective_permissions(canonical_role)
        return {
            "session_id": row["session_id"],
            "user_id": row["user_id"],
            "email": row["email"],
            "display_name": row["display_name"],
            "organization": row["organization"],
            "organization_id": row["organization"],
            "tenant_id": row["organization"],
            "active_role": row["active_role"],
            "workspace_id": row["workspace_id"],
            "assigned_roles": json.loads(row["assigned_roles"]),
            "permissions": permissions,
            "status": row["status"],
            "created_at": row["created_at"],
            "last_seen_at": row["last_seen_at"],
            "absolute_expires_at": row["absolute_expires_at"],
            "idle_expires_at": row["idle_expires_at"],
        }

    def _validate_session_row(self, row: sqlite3.Row | None) -> sqlite3.Row:
        if row is None:
            raise HTTPException(status_code=401, detail="session_not_found")
        if row["status"] != "active":
            raise HTTPException(status_code=401, detail="session_revoked")
        now = _utcnow()
        absolute_expires_at = _parse_iso(row["absolute_expires_at"])
        idle_expires_at = _parse_iso(row["idle_expires_at"])
        if absolute_expires_at is not None and absolute_expires_at <= now:
            self.revoke_session(row["session_id"], event_type="SESSION_TIMEOUT")
            raise HTTPException(status_code=401, detail="session_expired")
        if idle_expires_at is not None and idle_expires_at <= now:
            self.revoke_session(row["session_id"], event_type="SESSION_TIMEOUT")
            raise HTTPException(status_code=401, detail="session_timeout")
        return row

    def _touch(self, row: sqlite3.Row) -> None:
        now = _utcnow()
        idle_expires_at = now + timedelta(minutes=self.idle_timeout_minutes)
        self._update_session(
            row["session_id"],
            last_seen_at=_iso(now),
            idle_expires_at=_iso(idle_expires_at),
        )

    def login(
        self,
        *,
        identifier: str,
        password: str,
        role: str | None = None,
        user_agent: str = "",
        client_ip: str = "",
    ) -> dict[str, Any]:
        self._record_event(
            event_type="LOGIN_ATTEMPT",
            actor=identifier,
            role=(role or "UNKNOWN").upper(),
            organization="NovaTech",
            payload={"user_agent": user_agent, "client_ip": client_ip},
        )
        account = find_account(identifier)
        if account is None:
            self._record_event(
                event_type="LOGIN_FAILURE",
                actor=identifier,
                role="UNKNOWN",
                organization="NovaTech",
                payload={"reason": "account_not_found"},
            )
            raise HTTPException(status_code=401, detail="invalid_credentials")

        normalized_roles = _canonical_roles(account)
        requested_role = (role or normalized_roles[0]).upper()
        if requested_role not in normalized_roles:
            self._record_event(
                event_type="LOGIN_FAILURE",
                actor=account["username"],
                role=normalized_roles[0],
                organization="NovaTech",
                payload={"reason": "role_not_allowed", "requested_role": requested_role},
            )
            raise HTTPException(status_code=403, detail="role_not_allowed")
        if password != account.get("password", AUTH_PASSWORD):
            self._record_event(
                event_type="LOGIN_FAILURE",
                actor=account["username"],
                role=requested_role,
                organization="NovaTech",
                payload={"reason": "invalid_password"},
            )
            raise HTTPException(status_code=401, detail="invalid_credentials")

        session_id = secrets.token_hex(18)
        now = _utcnow()
        absolute_expires_at = now + timedelta(hours=self.absolute_timeout_hours)
        idle_expires_at = now + timedelta(minutes=self.idle_timeout_minutes)
        workspace_id = f"enterprise-{requested_role.lower().replace('_', '-')}"
        access_token = self.jwt_service.create_token(
            account["username"],
            role=requested_role,
            organization_id="NovaTech",
            workspace_id=workspace_id,
            issued_at=int(now.timestamp()),
            session_id=session_id,
        )
        refresh_token = secrets.token_urlsafe(48)
        csrf_token = secrets.token_urlsafe(24)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO novacodepro_sessions (
                    session_id, user_id, email, display_name, organization, active_role, workspace_id,
                    assigned_roles, status, created_at, last_seen_at, absolute_expires_at,
                    idle_expires_at, access_token_hash, refresh_token_hash, csrf_token_hash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    account["username"],
                    account["email"],
                    f'{account["first_name"]} {account["last_name"]}',
                    "NovaTech",
                    requested_role,
                    workspace_id,
                    json.dumps(normalized_roles),
                    "active",
                    _iso(now),
                    _iso(now),
                    _iso(absolute_expires_at),
                    _iso(idle_expires_at),
                    _hash_token(access_token),
                    _hash_token(refresh_token),
                    _hash_token(csrf_token),
                ),
            )
            connection.commit()
        self._record_event(
            event_type="LOGIN_SUCCESS",
            actor=account["username"],
            role=requested_role,
            organization="NovaTech",
            payload={"user_agent": user_agent, "client_ip": client_ip},
            session_id=session_id,
        )
        return {
            "session_id": session_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "csrf_token": csrf_token,
            "session": self.get_session(session_id),
        }

    def get_session(self, session_id: str) -> dict[str, Any]:
        row = self._validate_session_row(self._load_session_row(session_id))
        self._touch(row)
        refreshed = self._load_session_row(session_id)
        assert refreshed is not None
        return self._session_payload(refreshed)

    def get_claims_for_session(self, session_id: str) -> Any:
        row = self._validate_session_row(self._load_session_row(session_id))
        self._touch(row)
        refreshed = self._load_session_row(session_id)
        assert refreshed is not None
        return SessionJWTClaims(
            sub=str(refreshed["user_id"]),
            role=str(refreshed["active_role"]),
            organization_id=str(refreshed["organization"]),
            tenant_id=str(refreshed["organization"]),
            workspace_id=str(refreshed["workspace_id"]) if refreshed["workspace_id"] else None,
            permissions=_effective_permissions(str(refreshed["active_role"])),
            exp=int(_parse_iso(refreshed["absolute_expires_at"]).timestamp()),
            sid=str(refreshed["session_id"]),
        )

    def claims_from_request(self, request: Request) -> Any | None:
        token = request.cookies.get(ACCESS_COOKIE_NAME)
        session_id = request.cookies.get(SESSION_COOKIE_NAME)
        if token:
            try:
                claims = self.jwt_service.verify_token(token)
            except ValueError as exc:
                raise HTTPException(status_code=401, detail=str(exc)) from exc
            if claims.sid:
                self._validate_access_token_session(claims.sid, token)
                return self.get_claims_for_session(claims.sid)
            return claims
        if session_id:
            return self.get_claims_for_session(session_id)
        return None

    def _validate_access_token_session(self, session_id: str, token: str) -> None:
        row = self._validate_session_row(self._load_session_row(session_id))
        if _hash_token(token) != row["access_token_hash"]:
            raise HTTPException(status_code=401, detail="token_revoked")

    def current_session(self, request: Request) -> dict[str, Any]:
        claims = self.claims_from_request(request)
        if claims is None:
            raise HTTPException(status_code=401, detail="session_required")
        row = self._load_session_row(claims.sid) if claims.sid else None
        if row is None and claims.sid:
            raise HTTPException(status_code=401, detail="session_not_found")
        if row is not None:
            self._touch(row)
            refreshed = self._load_session_row(row["session_id"])
            assert refreshed is not None
            payload = self._session_payload(refreshed)
        else:
            canonical_role = canonical_role_name(str(claims.role))
            payload = {
                "session_id": None,
                "user_id": claims.sub,
                "email": None,
                "display_name": claims.sub,
                "organization": claims.organization_id,
                "organization_id": claims.organization_id,
                "tenant_id": claims.organization_id,
                "active_role": claims.role,
                "workspace_id": claims.workspace_id,
                "assigned_roles": [claims.role],
                "permissions": list(claims.permissions) if getattr(claims, "permissions", None) else _effective_permissions(canonical_role),
                "status": "active",
                "created_at": _iso(_utcnow()),
                "last_seen_at": _iso(_utcnow()),
                "absolute_expires_at": _iso(_utcnow() + timedelta(hours=self.absolute_timeout_hours)),
                "idle_expires_at": _iso(_utcnow() + timedelta(minutes=self.idle_timeout_minutes)),
            }
        absolute = _parse_iso(payload["absolute_expires_at"])
        idle = _parse_iso(payload["idle_expires_at"])
        warning_at = idle - timedelta(seconds=DEFAULT_WARNING_SECONDS) if idle else _utcnow()
        return {
            **payload,
            "idle_timeout_minutes": self.idle_timeout_minutes,
            "absolute_timeout_hours": self.absolute_timeout_hours,
            "warning_seconds": DEFAULT_WARNING_SECONDS,
            "warning_at": _iso(warning_at),
            "expires_at": payload["absolute_expires_at"],
            "idle_expires_at": payload["idle_expires_at"],
            "time_remaining_seconds": int((absolute - _utcnow()).total_seconds()) if absolute else None,
            "idle_remaining_seconds": int((idle - _utcnow()).total_seconds()) if idle else None,
        }

    def switch_role(self, request: Request, role: str) -> dict[str, Any]:
        claims = self.claims_from_request(request)
        if claims is None or not claims.sid:
            raise HTTPException(status_code=401, detail="session_required")
        row = self._validate_session_row(self._load_session_row(claims.sid))
        assigned_roles = json.loads(row["assigned_roles"])
        requested_role = role.upper()
        if requested_role not in assigned_roles:
            raise HTTPException(status_code=403, detail="role_not_allowed")
        now = _utcnow()
        access_token = self.jwt_service.create_token(
            row["user_id"],
            role=requested_role,
            organization_id=row["organization"],
            workspace_id=row["workspace_id"],
            issued_at=int(now.timestamp()),
            session_id=row["session_id"],
        )
        self._update_session(
            row["session_id"],
            active_role=requested_role,
            last_seen_at=_iso(now),
            idle_expires_at=_iso(now + timedelta(minutes=self.idle_timeout_minutes)),
            access_token_hash=_hash_token(access_token),
        )
        self._record_event(
            event_type="ROLE_SWITCH",
            actor=row["user_id"],
            role=requested_role,
            organization=row["organization"],
            payload={"previous_role": row["active_role"], "requested_role": requested_role},
            session_id=row["session_id"],
        )
        refreshed = self._load_session_row(row["session_id"])
        assert refreshed is not None
        return {
            "access_token": access_token,
            "session": self._session_payload(refreshed),
            "claims": self.get_claims_for_session(refreshed["session_id"]).__dict__,
        }

    def select_workspace(self, request: Request, workspace_id: str) -> dict[str, Any]:
        claims = self.claims_from_request(request)
        if claims is None or not claims.sid:
            raise HTTPException(status_code=401, detail="session_required")
        row = self._validate_session_row(self._load_session_row(claims.sid))
        now = _utcnow()
        access_token = self.jwt_service.create_token(
            row["user_id"],
            role=row["active_role"],
            organization_id=row["organization"],
            workspace_id=workspace_id,
            issued_at=int(now.timestamp()),
            session_id=row["session_id"],
        )
        refresh_token = secrets.token_urlsafe(48)
        csrf_token = secrets.token_urlsafe(24)
        self._update_session(
            row["session_id"],
            workspace_id=workspace_id,
            last_seen_at=_iso(now),
            idle_expires_at=_iso(now + timedelta(minutes=self.idle_timeout_minutes)),
            access_token_hash=_hash_token(access_token),
            refresh_token_hash=_hash_token(refresh_token),
            csrf_token_hash=_hash_token(csrf_token),
        )
        self._record_event(
            event_type="WORKSPACE_SELECT",
            actor=row["user_id"],
            role=row["active_role"],
            organization=row["organization"],
            payload={"workspace_id": workspace_id},
            session_id=row["session_id"],
        )
        refreshed = self._load_session_row(row["session_id"])
        assert refreshed is not None
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "csrf_token": csrf_token,
            "session": self._session_payload(refreshed),
            "claims": self.get_claims_for_session(refreshed["session_id"]).__dict__,
        }

    def refresh_session(self, request: Request) -> dict[str, Any]:
        claims = self.claims_from_request(request)
        if claims is None or not claims.sid:
            raise HTTPException(status_code=401, detail="session_required")
        row = self._validate_session_row(self._load_session_row(claims.sid))
        now = _utcnow()
        access_token = self.jwt_service.create_token(
            row["user_id"],
            role=row["active_role"],
            organization_id=row["organization"],
            issued_at=int(now.timestamp()),
            session_id=row["session_id"],
        )
        refresh_token = secrets.token_urlsafe(48)
        self._update_session(
            row["session_id"],
            last_seen_at=_iso(now),
            idle_expires_at=_iso(now + timedelta(minutes=self.idle_timeout_minutes)),
            access_token_hash=_hash_token(access_token),
            refresh_token_hash=_hash_token(refresh_token),
        )
        self._record_event(
            event_type="SESSION_REFRESH",
            actor=row["user_id"],
            role=row["active_role"],
            organization=row["organization"],
            payload={},
            session_id=row["session_id"],
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "session": self.get_session(row["session_id"]),
        }

    def revoke_session(self, session_id: str, *, event_type: str = "LOGOUT", actor: str | None = None) -> None:
        row = self._load_session_row(session_id)
        if row is None:
            return
        self._update_session(session_id, status="revoked")
        self._record_event(
            event_type=event_type,
            actor=actor or row["user_id"],
            role=row["active_role"],
            organization=row["organization"],
            payload={},
            session_id=session_id,
        )
        if event_type != "SESSION_REVOKED":
            self._record_event(
                event_type="SESSION_REVOKED",
                actor=actor or row["user_id"],
                role=row["active_role"],
                organization=row["organization"],
                payload={"source_event": event_type},
                session_id=session_id,
            )

    def logout(self, request: Request) -> dict[str, Any]:
        claims = self.claims_from_request(request)
        if claims is None or not claims.sid:
            raise HTTPException(status_code=401, detail="session_required")
        self.revoke_session(claims.sid, event_type="LOGOUT", actor=claims.sub)
        return {"status": "logged_out", "session_id": claims.sid}

    def resolve_session_id(self, request: Request) -> str | None:
        claims = self.claims_from_request(request)
        return claims.sid if claims and claims.sid else None


_DEFAULT_STORE: NovaCodeProSessionStore | None = None


def get_default_novacodepro_session_store() -> NovaCodeProSessionStore:
    global _DEFAULT_STORE
    if _DEFAULT_STORE is None:
        db_path = Path(os.environ.get("NOVACODEPRO_AUTH_DB_PATH", "var/novacodepro-auth.sqlite3"))
        _DEFAULT_STORE = NovaCodeProSessionStore(db_path)
    return _DEFAULT_STORE


def set_default_novacodepro_session_store(store: NovaCodeProSessionStore) -> NovaCodeProSessionStore:
    global _DEFAULT_STORE
    _DEFAULT_STORE = store
    return store


def novacodepro_session_from_request(request: Request) -> dict[str, Any]:
    return get_default_novacodepro_session_store().current_session(request)
