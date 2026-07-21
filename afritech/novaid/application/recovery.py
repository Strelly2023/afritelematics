"""Tenant-bound recovery codes, governed recovery, and WebAuthn policy."""
# ruff: noqa: E501 -- security SQL remains explicit at transaction boundaries.

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import json
import secrets
from uuid import uuid4

from ..observability import NovaIDMetrics, NovaIDTracer
from ..outbox import RevocationOutbox


class RecoveryError(ValueError):
    """Stable recovery denial without identity or code enumeration detail."""


def _id() -> str:
    return str(uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


class RecoveryCodeService:
    def __init__(self, uow, *, pepper: bytes, metrics=None, tracer=None) -> None:
        if len(pepper) < 32:
            raise ValueError("recovery_pepper_too_short")
        self.uow, self.pepper = uow, pepper
        self.metrics = metrics or NovaIDMetrics()
        self.tracer = tracer or NovaIDTracer()

    def _hash(self, tenant_id: str, identity_id: str, code: str) -> str:
        material = f"recovery:{tenant_id}:{identity_id}:{code}".encode()
        return hmac.new(self.pepper, material, hashlib.sha256).hexdigest()

    def _authorize(self, tenant_id: str, identity_id: str, session_id: str) -> dict:
        row = self.uow.get_recovery_authorization_context(tenant_id, identity_id, session_id)
        if (
            not row
            or row["status"] != "ACTIVE"
            or row["membership_status"] != "ACTIVE"
            or row["authentication_strength"] != "PHISHING_RESISTANT"
            or not row["step_up_expires_at"]
            or datetime.fromisoformat(row["step_up_expires_at"]) <= _now()
        ):
            raise RecoveryError("RECOVERY_OPERATION_DENIED")
        policy = self.uow.get_recovery_policy(tenant_id)
        if policy and not bool(policy["recovery_codes_enabled"]):
            raise RecoveryError("RECOVERY_OPERATION_DENIED")
        return (
            dict(policy) if policy else {"recovery_code_count": 8, "recovery_code_expiry_days": 365}
        )

    def generate_codes(
        self, *, tenant_id: str, identity_id: str, session_id: str, count: int | None = None
    ) -> dict[str, object]:
        policy = self._authorize(tenant_id, identity_id, session_id)
        total = count or int(policy["recovery_code_count"])
        if not 1 <= total <= 20:
            raise RecoveryError("RECOVERY_OPERATION_DENIED")
        now, batch_id = _now(), _id()
        expires = now + timedelta(days=int(policy["recovery_code_expiry_days"]))
        codes = [
            f"{secrets.token_hex(5).upper()}-{secrets.token_hex(5).upper()}" for _ in range(total)
        ]
        with self.tracer.span("novaid.recovery_codes.generate", {"operation": "recovery.generate"}):
            with self.uow:
                self.uow.supersede_recovery_codes(tenant_id, identity_id, now=now.isoformat())
                self.uow.insert_recovery_code_batch(
                    batch_id,
                    tenant_id,
                    identity_id,
                    created_at=now.isoformat(),
                    expires_at=expires.isoformat(),
                )
                for code in codes:
                    self.uow.insert_recovery_code(
                        _id(),
                        batch_id,
                        tenant_id,
                        identity_id,
                        self._hash(tenant_id, identity_id, code),
                        created_at=now.isoformat(),
                        expires_at=expires.isoformat(),
                    )
        self.metrics.increment("novaid_recovery_codes_generated_total", outcome="success")
        return {
            "batch_id": batch_id,
            "codes": codes,
            "created_at": now.isoformat(),
            "expires_at": expires.isoformat(),
        }

    def consume_code(self, *, tenant_id: str, identity_id: str, code: str) -> str:
        digest, now = self._hash(tenant_id, identity_id, code), _now()
        with self.uow:
            row = self.uow.get_recovery_code_by_hash(tenant_id, identity_id, digest)
            if (
                not row
                or row["status"] != "ACTIVE"
                or datetime.fromisoformat(row["expires_at"]) <= now
            ):
                raise RecoveryError("RECOVERY_CODE_INVALID")
            if self.uow.consume_recovery_code(row["recovery_code_id"], now=now.isoformat()) != 1:
                raise RecoveryError("RECOVERY_CODE_INVALID")
        self.metrics.increment("novaid_recovery_codes_consumed_total", outcome="success")
        return str(row["recovery_code_id"])

    def revoke_all(self, *, tenant_id: str, identity_id: str, session_id: str) -> int:
        self._authorize(tenant_id, identity_id, session_id)
        now = _now().isoformat()
        with self.uow:
            result = self.uow.revoke_recovery_codes(tenant_id, identity_id, now=now)
            self.uow.revoke_recovery_code_batches(tenant_id, identity_id, now=now)
        return result

    def remaining(self, *, tenant_id: str, identity_id: str) -> int:
        return self.uow.count_active_recovery_codes(tenant_id, identity_id, now=_now().isoformat())


class TenantWebAuthnPolicyService:
    DEFAULT = {
        "enabled": True,
        "passkeys_enabled": True,
        "passwordless_enabled": True,
        "phishing_resistant_step_up_required": True,
        "user_verification": "required",
        "attestation": "none",
        "maximum_credentials": 10,
        "recovery_codes_enabled": True,
        "recovery_code_count": 8,
        "recovery_code_expiry_days": 365,
        "recovery_approval_count": 1,
        "recovery_requires_new_authenticator": True,
        "step_up_seconds": 300,
    }

    def __init__(self, uow, *, distributed_outbox=None) -> None:
        self.uow = uow
        self.distributed_outbox = distributed_outbox

    def set_policy(
        self,
        *,
        tenant_id: str,
        actor_identity_id: str,
        session_id: str,
        policy: dict[str, object],
        expected_version: int | None,
        reason: str,
    ) -> dict:
        if not reason.strip():
            raise RecoveryError("POLICY_CHANGE_DENIED")
        actor = self.uow.get_actor_recovery_context(tenant_id, actor_identity_id, session_id)
        if (
            not actor
            or actor["role"] not in {"ADMIN", "SECURITY_ADMIN"}
            or actor["authentication_strength"] != "PHISHING_RESISTANT"
            or not actor["step_up_expires_at"]
            or datetime.fromisoformat(actor["step_up_expires_at"]) <= _now()
        ):
            raise RecoveryError("POLICY_CHANGE_DENIED")
        merged = {**self.DEFAULT, **policy}
        if (
            merged["user_verification"] not in {"required", "preferred", "discouraged"}
            or merged["attestation"] not in {"none", "indirect", "direct", "enterprise"}
            or not 1 <= int(merged["maximum_credentials"]) <= 100
            or not 1 <= int(merged["recovery_code_count"]) <= 20
        ):
            raise RecoveryError("INVALID_WEBAUTHN_POLICY")
        prior = self.uow.get_recovery_policy(tenant_id)
        if prior and int(prior["version"]) != expected_version:
            raise RecoveryError("POLICY_VERSION_CONFLICT")
        version, now = (int(prior["version"]) + 1 if prior else 1), _now().isoformat()
        with self.uow:
            self.uow.replace_tenant_webauthn_policy(
                tenant_id,
                merged,
                updated_by=actor_identity_id,
                reason=reason,
                version=version,
                updated_at=now,
            )
            if self.distributed_outbox:
                self.distributed_outbox.create_event(
                    tenant_id=tenant_id,
                    event_type="TENANT_WEBAUTHN_POLICY_CREATED"
                    if prior is None
                    else "TENANT_WEBAUTHN_POLICY_UPDATED",
                    resource_type="TENANT_WEBAUTHN_POLICY",
                    resource_reference=tenant_id,
                    resource_version=version,
                    correlation_id="policy-update",
                    request_id="policy-update",
                    payload={"version": version},
                )
        return {**merged, "version": version}

    def get_policy(self, tenant_id: str) -> dict[str, object]:
        row = self.uow.get_recovery_policy(tenant_id)
        return dict(row) if row else {**self.DEFAULT, "version": 0}


class AccountRecoveryService:
    def __init__(self, uow, codes: RecoveryCodeService, *, outbox=None) -> None:
        self.uow, self.codes = uow, codes
        self.outbox = outbox or RevocationOutbox(uow)

    def request_recovery(
        self,
        *,
        tenant_id: str,
        identifier: str,
        recovery_method: str,
        correlation_id: str,
        request_id: str,
        device_reference: str | None = None,
        network_reference: str | None = None,
    ) -> dict[str, object]:
        identity = self.uow.get_active_identity_by_email(tenant_id, identifier.strip().lower())
        if not identity:
            return {"accepted": True}
        now, recovery_id = _now(), _id()
        recent = self.uow.get_recent_recovery_request(
            tenant_id, identity["identity_id"], since=(now - timedelta(minutes=1)).isoformat()
        )
        if recent:
            return {"accepted": True}
        with self.uow:
            self.uow.insert_recovery_request(
                recovery_id,
                tenant_id,
                identity["identity_id"],
                status="REQUESTED",
                recovery_method=recovery_method,
                requested_at=now.isoformat(),
                expires_at=(now + timedelta(minutes=30)).isoformat(),
                reason="USER_REQUEST",
                correlation_id=correlation_id,
                request_id=request_id,
                device_reference=device_reference,
                network_reference=network_reference,
            )
        return {"accepted": True, "recovery_request_id": recovery_id}

    def verify_recovery_code(
        self,
        *,
        tenant_id: str,
        recovery_request_id: str,
        code: str,
        correlation_id: str,
        request_id: str,
    ) -> None:
        recovery = self.uow.get_recovery_request(tenant_id, recovery_request_id)
        if not recovery or recovery["status"] != "REQUESTED":
            raise RecoveryError("ACCOUNT_RECOVERY_DENIED")
        self.codes.consume_code(tenant_id=tenant_id, identity_id=recovery["identity_id"], code=code)
        with self.uow:
            self.uow.mark_recovery_verified(recovery_request_id)
            self.uow.insert_recovery_evidence(
                _id(),
                recovery_request_id,
                tenant_id,
                recovery["identity_id"],
                method="RECOVERY_CODE",
                correlation_id=correlation_id,
                request_id=request_id,
                created_at=_now().isoformat(),
            )

    def approve(
        self, *, tenant_id: str, recovery_request_id: str, approver_identity_id: str, reason: str
    ) -> None:
        recovery = self.uow.get_recovery_request(tenant_id, recovery_request_id)
        member = self.uow.get_membership_role_status(tenant_id, approver_identity_id)
        if (
            not recovery
            or recovery["status"] != "VERIFIED"
            or recovery["identity_id"] == approver_identity_id
            or not member
            or member["status"] != "ACTIVE"
            or member["role"] not in {"ADMIN", "SECURITY_ADMIN"}
        ):
            raise RecoveryError("ACCOUNT_RECOVERY_DENIED")
        now = _now()
        with self.uow:
            self.uow.insert_recovery_approval(
                _id(),
                recovery_request_id,
                tenant_id,
                approver_identity_id,
                decision="APPROVED",
                reason=reason,
                created_at=now.isoformat(),
                expires_at=(now + timedelta(minutes=15)).isoformat(),
            )
            self.uow.bump_recovery_request_version(recovery_request_id)
            policy = self.uow.get_recovery_policy(tenant_id)
            required = int(policy["recovery_approval_count"]) if policy else 1
            approved = self.uow.count_active_recovery_approvals(
                tenant_id, recovery_request_id, now=now.isoformat()
            )
            if int(approved) >= required:
                self.uow.mark_recovery_approved(
                    recovery_request_id,
                    approved_at=now.isoformat(),
                    approved_by=approver_identity_id,
                )

    def reject(
        self, *, tenant_id: str, recovery_request_id: str, approver_identity_id: str, reason: str
    ) -> None:
        member = self.uow.get_membership_role_status(tenant_id, approver_identity_id)
        if (
            not member
            or member["status"] != "ACTIVE"
            or member["role"] not in {"ADMIN", "SECURITY_ADMIN"}
        ):
            raise RecoveryError("ACCOUNT_RECOVERY_DENIED")
        now = _now()
        with self.uow:
            if (
                self.uow.mark_recovery_rejected(
                    tenant_id,
                    recovery_request_id,
                    rejected_at=now.isoformat(),
                    reason=reason,
                )
                != 1
            ):
                raise RecoveryError("ACCOUNT_RECOVERY_DENIED")

    def cancel(self, *, tenant_id: str, recovery_request_id: str, identity_id: str) -> None:
        with self.uow:
            if (
                self.uow.mark_recovery_cancelled(
                    tenant_id,
                    identity_id,
                    recovery_request_id,
                    cancelled_at=_now().isoformat(),
                )
                != 1
            ):
                raise RecoveryError("ACCOUNT_RECOVERY_DENIED")

    def expire_stale(self, *, tenant_id: str, now: datetime | None = None) -> int:
        instant = now or _now()
        with self.uow:
            return self.uow.expire_recovery_requests(tenant_id, now=instant.isoformat())

    def complete(self, *, tenant_id: str, recovery_request_id: str) -> None:
        now = _now()
        with self.uow:
            row = self.uow.mark_recovery_completed(
                tenant_id, recovery_request_id, completed_at=now.isoformat()
            )
            if (
                not row
                or row["status"] != "APPROVED"
                or datetime.fromisoformat(row["expires_at"]) <= now
            ):
                raise RecoveryError("ACCOUNT_RECOVERY_DENIED")
            identity_id = row["identity_id"]
            self.uow.bump_identity_security_version(tenant_id, identity_id)
            self.uow.revoke_sessions_for_identity(tenant_id, identity_id, "ACCOUNT_RECOVERY")
            self.uow.revoke_refresh_families_for_identity(tenant_id, identity_id, "ACCOUNT_RECOVERY")
            self.uow.revoke_webauthn_credentials_for_identity(tenant_id, identity_id)
            self.uow.revoke_recovery_codes(tenant_id, identity_id, now=now.isoformat())
            self.outbox.enqueue(
                tenant_id=tenant_id,
                event_type="ACCOUNT_RECOVERY_COMPLETED",
                resource_type="IDENTITY",
                resource_id=identity_id,
                event_version=1,
                payload={"reason": "ACCOUNT_RECOVERY"},
            )
            self.outbox.enqueue(
                tenant_id=tenant_id,
                event_type="IDENTITY_SECURITY_VERSION_INCREMENTED",
                resource_type="IDENTITY",
                resource_id=identity_id,
                event_version=1,
                payload={"reason": "ACCOUNT_RECOVERY"},
            )
            self.outbox.enqueue(
                tenant_id=tenant_id,
                event_type="ALL_SESSIONS_REVOKED",
                resource_type="IDENTITY",
                resource_id=identity_id,
                event_version=1,
                payload={"reason": "ACCOUNT_RECOVERY"},
            )
            self.outbox.enqueue(
                tenant_id=tenant_id,
                event_type="TOKEN_FAMILY_REVOKED",
                resource_type="IDENTITY",
                resource_id=identity_id,
                event_version=1,
                payload={"reason": "ACCOUNT_RECOVERY"},
            )
            self.outbox.enqueue(
                tenant_id=tenant_id,
                event_type="RECOVERY_REENROLMENT_REQUIRED",
                resource_type="IDENTITY",
                resource_id=identity_id,
                event_version=1,
                payload={"reason": "ACCOUNT_RECOVERY"},
            )
