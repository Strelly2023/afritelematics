"""Tenant-scoped, durable mobile-device attestation authority."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from collections.abc import Callable
from typing import Any, Protocol
from urllib.request import Request, urlopen
from uuid import uuid4


class DeviceAttestationError(ValueError):
    pass


@dataclass(frozen=True)
class AttestationContext:
    tenant_id: str
    subject_id: str
    device_id: str
    provider: str
    request_id: str
    correlation_id: str


@dataclass(frozen=True)
class AttestationChallenge:
    challenge_id: str
    nonce: str
    expires_at: datetime
    provider: str
    cloud_project_number: str | None = None


@dataclass(frozen=True)
class VerifiedDeviceAttestation:
    tenant_id: str
    subject_id: str
    device_id: str
    provider: str
    challenge_id: str
    request_id: str
    correlation_id: str
    verdicts: tuple[str, ...]
    verified_at: datetime
    trusted: bool = True


class AttestationVerifier(Protocol):
    def verify(self, *, provider: str, token: str, nonce: str, device_id: str) -> tuple[str, ...]: ...


class ProductionAttestationVerifier:
    """Strict boundary to the server-side Play Integrity/App Attest verifier."""

    def __init__(self) -> None:
        self.package_name = os.environ.get(
            "AFRIRIDE_PLAY_INTEGRITY_PACKAGE_NAME", "com.novatech.novaride.driver"
        )
        self.signer_digest = os.environ.get("AFRIRIDE_PLAY_INTEGRITY_SIGNER_SHA256", "").strip()

    def verify(self, *, provider: str, token: str, nonce: str, device_id: str) -> tuple[str, ...]:
        url_key = (
            "AFRIRIDE_PLAY_INTEGRITY_VERIFIER_URL"
            if provider == "PLAY_INTEGRITY"
            else "AFRIRIDE_APP_ATTEST_VERIFIER_URL"
        )
        endpoint = os.environ.get(url_key, "").strip()
        if not endpoint.startswith("https://"):
            raise DeviceAttestationError("attestation_verifier_not_configured")
        if provider == "PLAY_INTEGRITY" and not self.signer_digest:
            raise DeviceAttestationError("play_integrity_signer_not_configured")
        body = json.dumps({
            "token": token, "nonce": nonce, "device_id": device_id,
            "provider": provider, "expected_package_name": self.package_name,
            "expected_signer_sha256": self.signer_digest,
        }).encode()
        request = Request(endpoint, data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=5) as response:  # noqa: S310 - configured HTTPS authority
                result = json.loads(response.read())
        except Exception as exc:
            raise DeviceAttestationError("attestation_verifier_unavailable") from exc
        if not isinstance(result, dict) or result.get("trusted") is not True:
            raise DeviceAttestationError(str(result.get("reason", "device_integrity_failed")))
        if result.get("nonce") != nonce or result.get("device_id") != device_id:
            raise DeviceAttestationError("attestation_response_binding_mismatch")
        if provider == "PLAY_INTEGRITY":
            if result.get("package_name") != self.package_name:
                raise DeviceAttestationError("play_integrity_package_mismatch")
            if not hmac.compare_digest(str(result.get("signer_sha256", "")), self.signer_digest):
                raise DeviceAttestationError("play_integrity_signer_mismatch")
        timestamp = result.get("timestamp_millis")
        if not isinstance(timestamp, (int, float)) or abs(datetime.now(timezone.utc).timestamp() * 1000 - timestamp) > 120_000:
            raise DeviceAttestationError("attestation_timestamp_invalid")
        verdicts = result.get("verdicts")
        if not isinstance(verdicts, list) or not verdicts or not all(isinstance(item, str) for item in verdicts):
            raise DeviceAttestationError("attestation_verdict_invalid")
        return tuple(verdicts)


class DeviceAttestationAuthority:
    def __init__(self, uow_provider: Callable[[], Any], verifier: AttestationVerifier, *, ttl_seconds: int = 120) -> None:
        self.uow_provider, self.verifier, self.ttl_seconds = uow_provider, verifier, ttl_seconds

    @staticmethod
    def _provider(value: str) -> str:
        provider = value.strip().upper()
        aliases = {"ANDROID": "PLAY_INTEGRITY", "IOS": "APP_ATTEST"}
        provider = aliases.get(provider, provider)
        if provider not in {"PLAY_INTEGRITY", "APP_ATTEST"}:
            raise DeviceAttestationError("unsupported_attestation_provider")
        return provider

    def create_challenge(self, context: AttestationContext) -> AttestationChallenge:
        if not all((context.tenant_id, context.subject_id, context.device_id, context.request_id, context.correlation_id)):
            raise DeviceAttestationError("attestation_context_incomplete")
        now, nonce = datetime.now(timezone.utc), secrets.token_urlsafe(32)
        challenge_id, provider = str(uuid4()), self._provider(context.provider)
        expires_at = now + timedelta(seconds=self.ttl_seconds)
        uow = self.uow_provider()
        with uow:
            uow.device_attestations.create(
                (challenge_id, context.tenant_id, context.subject_id, context.device_id, provider,
                 hashlib.sha256(nonce.encode()).hexdigest(), context.request_id, context.correlation_id,
                 now, expires_at, None, "ISSUED"),
            )
        return AttestationChallenge(challenge_id, nonce, expires_at, provider,
            os.environ.get("AFRIRIDE_PLAY_CLOUD_PROJECT_NUMBER") or None)

    def verify(self, context: AttestationContext, *, challenge_id: str, nonce: str, token: str) -> VerifiedDeviceAttestation:
        provider, now = self._provider(context.provider), datetime.now(timezone.utc)
        # Consumption commits before the remote call: every verification attempt is single-use,
        # including provider rejection and network failure.
        uow = self.uow_provider()
        with uow:
            row = uow.device_attestations.lock(challenge_id, context.tenant_id)
            if row is None:
                raise DeviceAttestationError("attestation_challenge_missing")
            get = lambda key: row[key]
            if get("status") != "ISSUED": raise DeviceAttestationError("attestation_challenge_replayed")
            if any(str(get(k)) != str(v) for k, v in (("subject_id", context.subject_id), ("device_id", context.device_id), ("provider", provider), ("correlation_id", context.correlation_id))):
                raise DeviceAttestationError("attestation_scope_mismatch")
            expires = datetime.fromisoformat(str(get("expires_at")))
            if expires.tzinfo is None: expires = expires.replace(tzinfo=timezone.utc)
            if expires <= now: raise DeviceAttestationError("attestation_challenge_expired")
            if not hmac.compare_digest(str(get("nonce_hash")), hashlib.sha256(nonce.encode()).hexdigest()):
                raise DeviceAttestationError("attestation_nonce_mismatch")
            if uow.device_attestations.consume(challenge_id, context.tenant_id, now) != 1:
                raise DeviceAttestationError("attestation_challenge_replayed")
        verdicts = self.verifier.verify(provider=provider, token=token, nonce=nonce, device_id=context.device_id)
        verified_at = datetime.now(timezone.utc)
        with self.uow_provider() as uow:
            if uow.device_attestations.mark_trusted(
                challenge_id, context.tenant_id, verified_at, json.dumps(verdicts)
            ) != 1:
                raise DeviceAttestationError("attestation_result_persistence_failed")
        return VerifiedDeviceAttestation(context.tenant_id, context.subject_id, context.device_id,
            provider, challenge_id, context.request_id, context.correlation_id, verdicts, verified_at)


class PersistedDeviceTrustSignalResolver:
    """NovaTrust signal source backed only by server-verified durable evidence."""

    def __init__(self, uow_provider: Callable[[], Any]) -> None:
        self.uow_provider = uow_provider

    def __call__(self, request: Any) -> Any:
        from .novatrust_identity_risk import (
            DeviceTrustResult,
            NovaTrustIdentityRiskSignals,
            ScreeningResult,
        )
        trust = DeviceTrustResult.UNVERIFIED
        if request.device_id:
            with self.uow_provider() as uow:
                row = uow.device_attestations.latest_status(
                    request.tenant_id, request.subject_id, request.device_id
                )
            if row is not None:
                trust = {
                    "VERIFIED": DeviceTrustResult.TRUSTED,
                    "INTEGRITY_FAILED": DeviceTrustResult.INTEGRITY_FAILED,
                }.get(str(row["verification_status"]), DeviceTrustResult.UNVERIFIED)
        return NovaTrustIdentityRiskSignals(
            tenant_id=request.tenant_id, subject_id=request.subject_id,
            authentication_risk=Decimal("0"), device_trust=trust,
            identity_compromised=False, screening=ScreeningResult.NOT_CONFIGURED,
            provenance="verified_device_attestation_repository",
        )
