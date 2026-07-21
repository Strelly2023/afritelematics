from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
import hashlib
import hmac

import pytest

from afritech.novaid.application.recovery import (
    AccountRecoveryService,
    RecoveryCodeService,
    RecoveryError,
)


class _Outbox:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def enqueue(self, **kwargs) -> None:
        self.events.append(kwargs)


class _RecoveryUow:
    def __init__(self) -> None:
        self.requests: dict[str, dict[str, object]] = {}
        self.codes: dict[str, dict[str, object]] = {}
        self.approvals: list[dict[str, object]] = []
        self.evidence: list[dict[str, object]] = []
        self.identity_versions: list[tuple[str, str]] = []
        self.revocations: list[tuple[str, str, str]] = []
        self.memberships = {
            ("tenant-1", "admin-1"): {"status": "ACTIVE", "role": "ADMIN"},
        }
        self.policy = {
            "recovery_codes_enabled": True,
            "recovery_code_count": 3,
            "recovery_code_expiry_days": 30,
            "recovery_approval_count": 1,
            "recovery_requires_new_authenticator": True,
            "step_up_seconds": 300,
        }
        self.calls = defaultdict(int)

    def __enter__(self) -> "_RecoveryUow":
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        return False

    def get_active_identity_by_email(self, tenant_id: str, email: str):
        return {"identity_id": "identity-1"} if email == "user@example.com" else None

    def get_recent_recovery_request(self, tenant_id: str, identity_id: str, since: str):
        return None

    def insert_recovery_request(self, recovery_request_id: str, tenant_id: str, identity_id: str, **kwargs):
        self.requests[recovery_request_id] = {
            "recovery_request_id": recovery_request_id,
            "tenant_id": tenant_id,
            "identity_id": identity_id,
            "status": kwargs["status"],
            "recovery_method": kwargs["recovery_method"],
            "requested_at": kwargs["requested_at"],
            "expires_at": kwargs["expires_at"],
            "approved_at": None,
            "approved_by": None,
            "completed_at": None,
            "rejected_at": None,
            "cancelled_at": None,
            "version": 1,
        }

    def get_recovery_request(self, tenant_id: str, recovery_request_id: str):
        row = self.requests.get(recovery_request_id)
        if row and row["tenant_id"] == tenant_id:
            return row
        return None

    def mark_recovery_verified(self, recovery_request_id: str) -> int:
        row = self.requests.get(recovery_request_id)
        if not row or row["status"] != "REQUESTED":
            return 0
        row["status"] = "VERIFIED"
        row["version"] += 1
        return 1

    def insert_recovery_evidence(self, *args, **kwargs) -> None:
        self.evidence.append({"args": args, "kwargs": kwargs})

    def get_membership_role_status(self, tenant_id: str, identity_id: str):
        return self.memberships.get((tenant_id, identity_id))

    def insert_recovery_approval(self, *args, **kwargs) -> None:
        self.approvals.append({"args": args, "kwargs": kwargs})

    def bump_recovery_request_version(self, recovery_request_id: str) -> int:
        row = self.requests.get(recovery_request_id)
        if not row:
            return 0
        row["version"] += 1
        return 1

    def count_active_recovery_approvals(self, tenant_id: str, recovery_request_id: str, *, now: str) -> int:
        return len([item for item in self.approvals if item["kwargs"]["decision"] == "APPROVED"])

    def mark_recovery_approved(self, recovery_request_id: str, *, approved_at: str, approved_by: str):
        row = self.requests.get(recovery_request_id)
        if not row or row["status"] != "VERIFIED":
            return 0
        row["status"] = "APPROVED"
        row["approved_at"] = approved_at
        row["approved_by"] = approved_by
        row["version"] += 1
        return 1

    def mark_recovery_rejected(self, tenant_id: str, recovery_request_id: str, *, rejected_at: str, reason: str):
        row = self.requests.get(recovery_request_id)
        if not row or row["tenant_id"] != tenant_id or row["status"] == "COMPLETED":
            return 0
        row["status"] = "REJECTED"
        row["rejected_at"] = rejected_at
        row["reason"] = reason
        row["version"] += 1
        return 1

    def mark_recovery_cancelled(self, tenant_id: str, identity_id: str, recovery_request_id: str, *, cancelled_at: str):
        row = self.requests.get(recovery_request_id)
        if not row or row["tenant_id"] != tenant_id or row["identity_id"] != identity_id:
            return 0
        row["status"] = "CANCELLED"
        row["cancelled_at"] = cancelled_at
        row["version"] += 1
        return 1

    def expire_recovery_requests(self, tenant_id: str, *, now: str) -> int:
        expired = 0
        for row in self.requests.values():
            if row["tenant_id"] == tenant_id and row["status"] == "REQUESTED":
                row["status"] = "EXPIRED"
                expired += 1
        return expired

    def mark_recovery_completed(self, tenant_id: str, recovery_request_id: str, *, completed_at: str):
        row = self.requests.get(recovery_request_id)
        if not row or row["tenant_id"] != tenant_id:
            return None
        return row

    def bump_identity_security_version(self, tenant_id: str, identity_id: str) -> None:
        self.identity_versions.append((tenant_id, identity_id))

    def revoke_sessions_for_identity(self, tenant_id: str, identity_id: str, reason: str) -> int:
        self.revocations.append((tenant_id, identity_id, reason))
        return 1

    def revoke_refresh_families_for_identity(self, tenant_id: str, identity_id: str, reason: str) -> int:
        self.revocations.append((tenant_id, identity_id, f"refresh:{reason}"))
        return 1

    def revoke_webauthn_credentials_for_identity(self, tenant_id: str, identity_id: str) -> int:
        self.revocations.append((tenant_id, identity_id, "webauthn"))
        return 1

    def revoke_recovery_codes(self, tenant_id: str, identity_id: str, *, now: str) -> int:
        self.revocations.append((tenant_id, identity_id, "recovery_codes"))
        return 1

    def get_recovery_authorization_context(self, tenant_id: str, identity_id: str, session_id: str):
        return {
            "status": "ACTIVE",
            "membership_status": "ACTIVE",
            "authentication_strength": "PHISHING_RESISTANT",
            "step_up_expires_at": (datetime.now(UTC) + timedelta(minutes=5)).isoformat(),
        }

    def get_recovery_policy(self, tenant_id: str):
        return self.policy

    def supersede_recovery_codes(self, tenant_id: str, identity_id: str, *, now: str) -> None:
        self.calls["supersede_recovery_codes"] += 1

    def insert_recovery_code_batch(self, *args, **kwargs) -> None:
        self.calls["insert_recovery_code_batch"] += 1

    def insert_recovery_code(self, recovery_code_id: str, batch_id: str, tenant_id: str, identity_id: str, code_hash: str, *, created_at: str, expires_at: str) -> None:
        self.codes[code_hash] = {
            "recovery_code_id": recovery_code_id,
            "status": "ACTIVE",
            "expires_at": expires_at,
        }

    def get_recovery_code_by_hash(self, tenant_id: str, identity_id: str, code_hash: str):
        return self.codes.get(code_hash)

    def consume_recovery_code(self, recovery_code_id: str, *, now: str) -> int:
        for row in self.codes.values():
            if row["recovery_code_id"] == recovery_code_id and row["status"] == "ACTIVE":
                row["status"] = "USED"
                return 1
        return 0

    def revoke_recovery_code_batches(self, tenant_id: str, identity_id: str, *, now: str) -> None:
        self.calls["revoke_recovery_code_batches"] += 1

    def count_active_recovery_codes(self, tenant_id: str, identity_id: str, *, now: str) -> int:
        return sum(1 for row in self.codes.values() if row["status"] == "ACTIVE")


def _service() -> tuple[_RecoveryUow, _Outbox, AccountRecoveryService, RecoveryCodeService]:
    uow = _RecoveryUow()
    outbox = _Outbox()
    pepper = b"x" * 32
    codes = RecoveryCodeService(uow, pepper=pepper)
    service = AccountRecoveryService(uow, codes, outbox=outbox)
    return uow, outbox, service, codes


def test_recovery_lifecycle_emits_outbox_for_each_transition() -> None:
    uow, outbox, service, _codes = _service()

    request = service.request_recovery(
        tenant_id="tenant-1",
        identifier="user@example.com",
        recovery_method="forgotten_password",
        correlation_id="corr-1",
        request_id="req-1",
    )
    recovery_request_id = str(request["recovery_request_id"])
    code = "ABCDE-12345"
    digest = hmac.new(b"x" * 32, b"recovery:tenant-1:identity-1:ABCDE-12345", hashlib.sha256).hexdigest()
    uow.codes[digest] = {
        "recovery_code_id": "code-1",
        "status": "ACTIVE",
        "expires_at": (datetime.now(UTC) + timedelta(minutes=10)).isoformat(),
    }

    service.verify_recovery_code(
        tenant_id="tenant-1",
        recovery_request_id=recovery_request_id,
        code=code,
        correlation_id="corr-2",
        request_id="req-2",
    )
    service.approve(
        tenant_id="tenant-1",
        recovery_request_id=recovery_request_id,
        approver_identity_id="admin-1",
        reason="verified",
    )
    service.complete(tenant_id="tenant-1", recovery_request_id=recovery_request_id)

    event_types = [event["event_type"] for event in outbox.events]
    assert event_types[:4] == [
        "ACCOUNT_RECOVERY_REQUESTED",
        "ACCOUNT_RECOVERY_VERIFIED",
        "ACCOUNT_RECOVERY_APPROVED",
        "ACCOUNT_RECOVERY_COMPLETED",
    ]
    assert "ALL_SESSIONS_REVOKED" in event_types
    assert "TOKEN_FAMILY_REVOKED" in event_types
    assert "RECOVERY_REENROLMENT_REQUIRED" in event_types
    assert uow.identity_versions == [("tenant-1", "identity-1")]
    assert uow.revocations


def test_recovery_reject_and_cancel_emit_outbox_and_block_invalid_completion() -> None:
    uow, outbox, service, _codes = _service()

    request = service.request_recovery(
        tenant_id="tenant-1",
        identifier="user@example.com",
        recovery_method="lost_device",
        correlation_id="corr-3",
        request_id="req-3",
    )
    recovery_request_id = str(request["recovery_request_id"])

    service.reject(
        tenant_id="tenant-1",
        recovery_request_id=recovery_request_id,
        approver_identity_id="admin-1",
        reason="risk",
    )
    assert uow.requests[recovery_request_id]["status"] == "REJECTED"
    assert any(event["event_type"] == "ACCOUNT_RECOVERY_REJECTED" for event in outbox.events)

    with pytest.raises(RecoveryError, match="ACCOUNT_RECOVERY_DENIED"):
        service.complete(tenant_id="tenant-1", recovery_request_id=recovery_request_id)

    next_request = service.request_recovery(
        tenant_id="tenant-1",
        identifier="user@example.com",
        recovery_method="lost_passkey",
        correlation_id="corr-4",
        request_id="req-4",
    )
    next_id = str(next_request["recovery_request_id"])
    service.cancel(tenant_id="tenant-1", recovery_request_id=next_id, identity_id="identity-1")
    assert uow.requests[next_id]["status"] == "CANCELLED"
    assert any(event["event_type"] == "ACCOUNT_RECOVERY_CANCELLED" for event in outbox.events)
