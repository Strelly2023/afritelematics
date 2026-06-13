"""Validate AfriPay security proof coverage."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from hashlib import sha256
import json
from importlib import import_module
from pathlib import Path

import django
from django.conf import settings

from afritech.afripay.security_audit import SecurityAuditStream


VALIDATOR_NAME = "AFRIPAY_SECURITY_VALIDATOR"


@dataclass(frozen=True)
class SecurityProofReport:
    key_rotation_verified: bool
    key_revocation_verified: bool
    rate_limiting_verified: bool
    security_audit_stream_verified: bool
    audit_logging_verified: bool
    audit_stream_hash: str
    mismatches: tuple[str, ...]

    @property
    def verified(self) -> bool:
        return not self.mismatches and len(self.audit_stream_hash) == 64

    def canonical_dict(self) -> dict[str, object]:
        return {
            "audit_stream_hash": self.audit_stream_hash,
            "audit_logging_verified": self.audit_logging_verified,
            "key_revocation_verified": self.key_revocation_verified,
            "key_rotation_verified": self.key_rotation_verified,
            "mismatches": list(self.mismatches),
            "rate_limiting_verified": self.rate_limiting_verified,
            "schema": "afritech.afripay.security_proof_report.v1",
            "security_audit_stream_verified": self.security_audit_stream_verified,
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def validate() -> SecurityProofReport:
    _bootstrap_django()
    models = _afripay_models()
    security = _afripay_security()

    stream = SecurityAuditStream()
    mismatches: list[str] = []

    key_rotation_verified = _verify_key_rotation(models, security, stream)
    if not key_rotation_verified:
        mismatches.append("oauth client key rotation proof failed")

    key_revocation_verified = _verify_key_revocation(models, security, stream)
    if not key_revocation_verified:
        mismatches.append("api key revocation proof failed")

    rate_limiting_verified = _verify_rate_limiting(security, stream)
    if not rate_limiting_verified:
        mismatches.append("rate limiting proof failed")

    audit_logging_verified = _verify_audit_logging(security, stream)
    if not audit_logging_verified:
        mismatches.append("audit logging proof failed")

    security_audit_stream_verified = stream.verify() and len(stream.root_hash()) == 64
    if not security_audit_stream_verified:
        mismatches.append("security audit stream is not internally consistent")

    report = SecurityProofReport(
        key_rotation_verified=key_rotation_verified,
        key_revocation_verified=key_revocation_verified,
        rate_limiting_verified=rate_limiting_verified,
        security_audit_stream_verified=security_audit_stream_verified,
        audit_logging_verified=audit_logging_verified,
        audit_stream_hash=stream.root_hash(),
        mismatches=tuple(mismatches),
    )
    if not report.verified:
        raise RuntimeError(", ".join(report.mismatches) or "security proof validation failed")
    return report


def _verify_key_rotation(models, security, stream: SecurityAuditStream) -> bool:
    client_secret_old = "security-validator-old"
    client, _ = models.OAuthClient.objects.update_or_create(
        client_id="afripay.security.validator.oauth",
        defaults={
            "name": "AfriPay Security Validator OAuth",
            "secret_hash": models.OAuthClient.hash_secret(client_secret_old),
            "scopes": ["payments:write", "monitoring:read"],
            "is_active": True,
            "failure_count": 0,
            "request_count": 0,
            "suspended_until": None,
            "expires_at": None,
        },
    )

    initial = security.verify_oauth_client_credentials(
        client.client_id,
        client_secret_old,
        scope="payments:write",
    )
    stream.append(
        "oauth_client_authenticated",
        actor=initial.client_id,
        details={"client_id": client.client_id, "mode": "initial"},
    )

    client_secret_new = "security-validator-new"
    client.secret_hash = models.OAuthClient.hash_secret(client_secret_new)
    client.save(update_fields=["secret_hash", "updated_at"])

    old_rejected = False
    try:
        security.verify_oauth_client_credentials(client.client_id, client_secret_old)
    except ValueError:
        old_rejected = True
    new_accepted = security.verify_oauth_client_credentials(client.client_id, client_secret_new)
    stream.append(
        "oauth_client_rotated",
        actor=new_accepted.client_id,
        details={"client_id": client.client_id, "rotation": "completed"},
    )
    return old_rejected and new_accepted.client_id == client.client_id


def _verify_key_revocation(models, security, stream: SecurityAuditStream) -> bool:
    service = security.APIKeyService()
    credential, raw_key = service.issue_key("security-validator-api-key", ["monitoring:read"])
    authenticated = service.authenticate(raw_key)
    credential.is_active = False
    credential.save(update_fields=["is_active", "updated_at"])

    revoked = False
    try:
        service.authenticate(raw_key)
    except ValueError:
        revoked = True
    stream.append(
        "api_key_revoked",
        actor=authenticated.subject,
        details={"key_id": credential.key_id, "status": "revoked"},
    )
    return revoked and authenticated.client_name == "security-validator-api-key"


def _verify_rate_limiting(security, stream: SecurityAuditStream) -> bool:
    limiter = security.AfriPayRateLimiter(window_seconds=60, max_requests=2)
    first = limiter.allow("security-validator")
    second = limiter.allow("security-validator")
    third = limiter.allow("security-validator")
    stream.append(
        "rate_limit_tripped",
        actor="security-validator",
        details={"allowed": [first, second, third], "max_requests": 2},
    )
    return first and second and not third


def _verify_audit_logging(security, stream: SecurityAuditStream) -> bool:
    alert = security.send_auth_alert(
        "AFRIPAY_SECURITY_VALIDATOR_AUDIT",
        {
            "validator": VALIDATOR_NAME,
            "stream_root": stream.root_hash(),
            "entries": len(stream.records),
        },
    )
    stream.append(
        "security_alert_emitted",
        actor="security-validator",
        details={"event_type": alert.get("event_type"), "alert_id": alert.get("id", "")},
    )
    return alert.get("event_type") == "AFRIPAY_SECURITY_VALIDATOR_AUDIT" and alert.get("severity") == "HIGH"


def _bootstrap_django() -> None:
    if settings.configured:
        return
    base_dir = Path(__file__).resolve().parents[2]
    django_app_dir = base_dir / "afriride_system" / "django_app"
    if str(base_dir) not in sys.path:
        sys.path.insert(0, str(base_dir))
    if str(django_app_dir) not in sys.path:
        sys.path.insert(0, str(django_app_dir))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "afriride_system.django_app.config.settings")
    django.setup()


def _afripay_models():
    return import_module("afriride_system.django_app.apps.afripay.models")


def _afripay_security():
    return import_module("afriride_system.django_app.apps.afripay.security")


def _canonical_hash(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def main() -> int:
    try:
        report = validate()
    except Exception as exc:  # noqa: BLE001
        print(f"{VALIDATOR_NAME}: FAILED: {exc}")
        return 1
    print(
        f"{VALIDATOR_NAME}: PASS "
        f"key_rotation={report.key_rotation_verified} "
        f"key_revocation={report.key_revocation_verified} "
        f"rate_limiting={report.rate_limiting_verified} "
        f"audit_stream_hash={report.audit_stream_hash} "
        f"report_hash={report.report_hash()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
