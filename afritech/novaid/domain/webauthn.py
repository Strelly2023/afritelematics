from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class WebAuthnCredentialStatus(StrEnum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"
    COMPROMISED = "COMPROMISED"
    REPLACED = "REPLACED"
    DELETED = "DELETED"


class WebAuthnChallengeStatus(StrEnum):
    PENDING = "PENDING"
    CONSUMED = "CONSUMED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    SUPERSEDED = "SUPERSEDED"
    ATTEMPTS_EXCEEDED = "ATTEMPTS_EXCEEDED"


@dataclass(frozen=True)
class WebAuthnCredential:
    credential_id: str
    tenant_id: str
    identity_id: str
    membership_id: str | None
    user_handle: bytes
    public_key_cose: bytes
    public_key_algorithm: int
    sign_count: int
    aaguid: str
    attestation_format: str
    attestation_type: str
    transports: tuple[str, ...] = ()
    backup_eligible: bool = False
    backup_state: bool = False
    discoverable: bool = False
    resident_key: bool = False
    user_verification: bool = False
    status: WebAuthnCredentialStatus = WebAuthnCredentialStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_used_at: datetime | None = None
    last_verified_at: datetime | None = None
    version: int = 1
    friendly_name: str | None = None
    device_reference: str | None = None
    provider_reference: str | None = None

    def __post_init__(self) -> None:
        if self.public_key_algorithm not in {-7, -8, -257}:
            raise ValueError("unsupported_cose_algorithm")
        if self.sign_count < 0:
            raise ValueError("negative_signature_counter")


@dataclass(frozen=True)
class AuthenticatorPolicy:
    rp_id: str
    rp_name: str
    origins: tuple[str, ...]
    require_user_verification: bool = True
    resident_key: str = "preferred"
    attestation: str = "none"
    allowed_algorithms: tuple[int, ...] = (-7, -8, -257)
    challenge_seconds: int = 300
    maximum_attempts: int = 5

    def __post_init__(self) -> None:
        if not self.rp_id or not self.origins or "*" in self.origins:
            raise ValueError("invalid_webauthn_relying_party")
        if any(
            not origin.startswith("https://") and not origin.startswith("http://localhost")
            for origin in self.origins
        ):
            raise ValueError("insecure_webauthn_origin")


@dataclass(frozen=True)
class PasskeyMetadata:
    discoverable: bool
    backup_eligible: bool
    backup_state: bool
    device_bound: bool
    synced: bool
