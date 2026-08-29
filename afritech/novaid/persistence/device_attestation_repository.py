"""Persistence boundary for device-attestation and activation state."""

from __future__ import annotations

from typing import Any


class DeviceAttestationRepository:
    def __init__(self, connection: Any, *, postgres: bool = False) -> None:
        self.connection, self.postgres = connection, postgres

    def create(self, values: tuple[Any, ...]) -> None:
        self.connection.execute(
            "INSERT INTO novaid_device_attestation_challenges("
            "challenge_id,tenant_id,subject_id,device_id,provider,nonce_hash,request_id,"
            "correlation_id,issued_at,expires_at,consumed_at,status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            values,
        )

    def lock(self, challenge_id: str, tenant_id: str):
        suffix = " FOR UPDATE" if self.postgres else ""
        return self.connection.execute(
            "SELECT * FROM novaid_device_attestation_challenges WHERE challenge_id=? AND tenant_id=?" + suffix,
            (challenge_id, tenant_id),
        ).fetchone()

    def consume(self, challenge_id: str, tenant_id: str, consumed_at: Any) -> int:
        return self.connection.execute(
            "UPDATE novaid_device_attestation_challenges SET status='CONSUMED',consumed_at=? "
            "WHERE challenge_id=? AND tenant_id=? AND status='ISSUED'",
            (consumed_at, challenge_id, tenant_id),
        ).rowcount

    def mark_trusted(self, challenge_id: str, tenant_id: str, verified_at: Any, verdicts: str) -> int:
        return self.connection.execute(
            "UPDATE novaid_device_attestation_challenges SET verification_status='VERIFIED',"
            "verified_at=?,verdicts=? WHERE challenge_id=? AND tenant_id=? AND status='CONSUMED'",
            (verified_at, verdicts, challenge_id, tenant_id),
        ).rowcount

    def latest_status(self, tenant_id: str, subject_id: str, device_id: str):
        return self.connection.execute(
            "SELECT verification_status FROM novaid_device_attestation_challenges "
            "WHERE tenant_id=? AND subject_id=? AND device_id=? ORDER BY verified_at DESC LIMIT 1",
            (tenant_id, subject_id, device_id),
        ).fetchone()

    def evidence(self, tenant_id: str, challenge_id: str):
        return self.connection.execute(
            "SELECT verification_status,subject_id,device_id FROM novaid_device_attestation_challenges "
            "WHERE tenant_id=? AND challenge_id=?", (tenant_id, challenge_id),
        ).fetchone()


class DeviceAttestationSessionRepository:
    def __init__(self, connection: Any, *, postgres: bool = False) -> None:
        self.connection, self.postgres = connection, postgres

    def mark_pending(self, tenant_id: str, session_id: str, device_id: str) -> int:
        return self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='PENDING_DEVICE_ATTESTATION',"
            "device_reference=?,authentication_strength='PASSWORD_OTP',authentication_methods=?,"
            "pending_mfa_expires_at=NULL WHERE tenant_id=? AND session_id=? AND status='PENDING_MFA'",
            (device_id, '["PASSWORD","OTP"]', tenant_id, session_id),
        ).rowcount

    def identity_security_version(self, tenant_id: str, identity_id: str):
        return self.connection.execute(
            "SELECT security_version FROM novaid_identities WHERE tenant_id=? AND identity_id=?",
            (tenant_id, identity_id),
        ).fetchone()

    def lock(self, tenant_id: str, session_id: str):
        suffix = " FOR UPDATE" if self.postgres else ""
        return self.connection.execute(
            "SELECT identity_id,membership_id,status,device_reference FROM novaid_authentication_sessions "
            "WHERE tenant_id=? AND session_id=?" + suffix, (tenant_id, session_id),
        ).fetchone()

    def activate(self, tenant_id: str, session_id: str, now: Any, idle_expires_at: Any) -> int:
        return self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='ACTIVE',authenticated_at=?,last_seen_at=?,"
            "idle_expires_at=?,version=version+1 WHERE tenant_id=? AND session_id=? "
            "AND status='PENDING_DEVICE_ATTESTATION'",
            (now, now, idle_expires_at, tenant_id, session_id),
        ).rowcount

    def provisional_context(self, tenant_id: str, session_id: str):
        return self.connection.execute(
            "SELECT s.status,s.identity_id,s.membership_id,s.device_reference,s.security_version,"
            "i.security_version identity_security_version FROM novaid_authentication_sessions s "
            "JOIN novaid_identities i ON i.identity_id=s.identity_id AND i.tenant_id=s.tenant_id "
            "WHERE s.tenant_id=? AND s.session_id=?", (tenant_id, session_id),
        ).fetchone()
