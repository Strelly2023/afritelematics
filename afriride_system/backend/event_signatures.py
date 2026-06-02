"""Signature support for AfriRide event ledgers."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


class EventSignatureError(RuntimeError):
    """Raised when event signature registration or validation fails."""


@dataclass(frozen=True)
class LegalIdentityBinding:
    full_name: str
    license_id: str
    jurisdiction: str
    verified: bool
    verification_method: str
    legal_acknowledgement: bool
    terms_version: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "full_name": self.full_name,
            "license_id": self.license_id,
            "jurisdiction": self.jurisdiction,
            "verified": self.verified,
            "verification_method": self.verification_method,
            "legal_acknowledgement": self.legal_acknowledgement,
            "terms_version": self.terms_version,
        }


@dataclass(frozen=True)
class RegisteredSigner:
    signer_id: str
    public_key_id: str
    public_key_pem: str
    device_id: str | None = None
    status: str = "ACTIVE"
    created_at: str | None = None
    expires_at: str | None = None
    revoked: bool = False
    revoked_reason: str | None = None
    identity: LegalIdentityBinding | None = None

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "signer_id": self.signer_id,
            "public_key_id": self.public_key_id,
            "device_id": self.device_id,
            "status": self.status,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "revoked": self.revoked,
            "revoked_reason": self.revoked_reason,
            "identity_bound": self.identity is not None,
        }


class SignerRegistry:
    """In-memory signer registry for bounded test and pilot validation."""

    def __init__(self, signers: tuple[RegisteredSigner, ...] = ()) -> None:
        self._signers = {
            (signer.signer_id, signer.public_key_id): signer
            for signer in signers
        }

    def register(self, signer: RegisteredSigner) -> None:
        self._signers[(signer.signer_id, signer.public_key_id)] = signer

    def require(self, signer_id: str, public_key_id: str) -> RegisteredSigner:
        signer = self._signers.get((signer_id, public_key_id))
        if signer is None:
            raise EventSignatureError(f"unknown signer key: {signer_id}/{public_key_id}")
        return signer


class EventSigner:
    """Create and verify RSA-PSS signatures over event hashes."""

    @staticmethod
    def generate_private_key() -> rsa.RSAPrivateKey:
        return rsa.generate_private_key(public_exponent=65537, key_size=2048)

    @staticmethod
    def public_key_pem(private_key: rsa.RSAPrivateKey) -> str:
        public_key = private_key.public_key()
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

    def sign_hash(self, event_hash: str, private_key: rsa.RSAPrivateKey) -> str:
        signature = private_key.sign(
            event_hash.encode("utf-8"),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode("ascii")

    def verify_hash(
        self,
        *,
        event_hash: str,
        signature: str,
        public_key_pem: str,
    ) -> None:
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode("utf-8")
        )
        try:
            public_key.verify(
                base64.b64decode(signature.encode("ascii")),
                event_hash.encode("utf-8"),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
        except (InvalidSignature, ValueError) as exc:
            raise EventSignatureError("invalid event signature") from exc


class EventSignatureValidator:
    """Validate event hash signatures against a registered signer key."""

    def __init__(
        self,
        registry: SignerRegistry,
        signer: EventSigner | None = None,
    ) -> None:
        self.registry = registry
        self.signer = signer or EventSigner()

    def validate_event(self, event: dict[str, Any]) -> None:
        signer_id = _require_string(event, "signer_id")
        public_key_id = _require_string(event, "public_key_id")
        signature = _require_string(event, "signature")
        event_hash = _require_string(event, "hash")
        registered = self.registry.require(signer_id, public_key_id)
        self._validate_key_lifecycle(registered, event)
        self._validate_identity_binding(registered, event)

        device_id = event.get("device_id")
        if registered.device_id is not None and device_id != registered.device_id:
            raise EventSignatureError(f"device mismatch for signer: {signer_id}")

        self.signer.verify_hash(
            event_hash=event_hash,
            signature=signature,
            public_key_pem=registered.public_key_pem,
        )

    def _validate_key_lifecycle(
        self,
        registered: RegisteredSigner,
        event: dict[str, Any],
    ) -> None:
        if registered.status != "ACTIVE":
            raise EventSignatureError(
                f"inactive signer key: {registered.signer_id}/{registered.public_key_id}"
            )
        if registered.revoked:
            raise EventSignatureError(
                f"revoked signer key: {registered.signer_id}/{registered.public_key_id}"
            )
        if registered.expires_at is None:
            return

        event_time = _parse_time(_require_string(event, "timestamp"))
        expires_at = _parse_time(registered.expires_at)
        if event_time > expires_at:
            raise EventSignatureError(
                f"expired signer key: {registered.signer_id}/{registered.public_key_id}"
            )

    def _validate_identity_binding(
        self,
        registered: RegisteredSigner,
        event: dict[str, Any],
    ) -> None:
        if registered.identity is None:
            return
        if not registered.identity.verified:
            raise EventSignatureError(f"unverified legal identity: {registered.signer_id}")
        if not registered.identity.legal_acknowledgement:
            raise EventSignatureError(
                f"missing legal acknowledgement: {registered.signer_id}"
            )
        if event.get("terms_version") != registered.identity.terms_version:
            raise EventSignatureError(f"terms version mismatch: {registered.signer_id}")


def _require_string(event: dict[str, Any], key: str) -> str:
    value = event.get(key)
    if not isinstance(value, str) or not value.strip():
        raise EventSignatureError(f"missing {key}")
    return value


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
