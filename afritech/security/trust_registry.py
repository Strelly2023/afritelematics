"""Governed signer trust registry with revocation checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class TrustedSigner:
    signer_id: str
    public_key: str
    roles: tuple[str, ...]
    status: str = "TRUSTED"

    def canonical_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TrustRegistry:
    signers: tuple[TrustedSigner, ...]
    revoked_keys: tuple[str, ...] = ()

    def signer_by_id(self, signer_id: str) -> TrustedSigner | None:
        for signer in self.signers:
            if signer.signer_id == signer_id:
                return signer
        return None

    def signer_by_key(self, public_key: str) -> TrustedSigner | None:
        for signer in self.signers:
            if signer.public_key == public_key:
                return signer
        return None

    def is_revoked(self, public_key: str) -> bool:
        return public_key in self.revoked_keys

    def canonical_dict(self) -> dict[str, object]:
        return {
            "schema": "afritech.trust_registry.v1",
            "signers": [signer.canonical_dict() for signer in self.signers],
            "revoked_keys": self.revoked_keys,
        }


def build_default_trust_registry(core_public_key: str) -> TrustRegistry:
    return TrustRegistry(
        signers=(
            TrustedSigner(
                signer_id="AFRITECH_CORE",
                public_key=core_public_key,
                roles=("CORE", "REGISTRY_SIGNER", "VALIDATOR"),
            ),
        )
    )


def signer_authorized(payload: dict[str, object], registry: TrustRegistry | None = None) -> bool:
    signature = payload.get("signature")
    if not isinstance(signature, dict):
        return False
    signer_id = signature.get("signer_id")
    public_key = signature.get("public_key")
    if not isinstance(signer_id, str) or not isinstance(public_key, str):
        return False

    resolved_registry = registry or build_default_trust_registry(public_key)
    signer = resolved_registry.signer_by_id(signer_id)
    return (
        signer is not None
        and signer.public_key == public_key
        and signer.status == "TRUSTED"
        and "REGISTRY_SIGNER" in signer.roles
        and not resolved_registry.is_revoked(public_key)
    )


__all__ = [
    "TrustRegistry",
    "TrustedSigner",
    "build_default_trust_registry",
    "signer_authorized",
]
