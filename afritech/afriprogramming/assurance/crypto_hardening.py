from __future__ import annotations

from hashlib import sha256
from typing import Any

from afritech.afriprogramming.assurance.pki import PKIService
from afritech.afriprogramming.persistence import PlatformStore, get_platform_store


def _hash_chain(chain: list[dict[str, Any]]) -> str:
    import json

    return sha256(json.dumps(chain, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


class CryptoStorageHardeningService:
    """HSM/KMS-style crypto hardening with certificate-chain support."""

    def __init__(self, repository: PlatformStore | None = None, pki_service: PKIService | None = None) -> None:
        self.repository = repository or get_platform_store()
        self.pki = pki_service or PKIService(self.repository)

    def available_backends(self, organization_id: str | None = None, key_family: str | None = None) -> dict[str, Any]:
        return {
            "organization_id": organization_id,
            "key_family": key_family,
            "backends": self.repository.list_crypto_backends(
                organization_id=organization_id,
                key_family=key_family,
            ),
            "keys": self.pki.list_keys(organization_id=organization_id, key_family=key_family),
        }

    def register_backend(
        self,
        *,
        organization_id: str,
        key_family: str,
        backend_name: str,
        provider_ref: str,
        key_arn: str | None = None,
        hardware_bound: bool = False,
    ) -> dict[str, Any]:
        current_key = self.pki.current_key(organization_id=organization_id, key_family=key_family)
        chain = self.issue_certificate_chain(
            organization_id=organization_id,
            key_family=key_family,
            subject=backend_name,
            issuer="NovaProgramming PKI",
        )
        return self.repository.register_crypto_backend(
            organization_id=organization_id,
            key_family=key_family,
            backend_name=backend_name,
            provider_ref=provider_ref,
            key_arn=key_arn or current_key["key_id"],
            hardware_bound=hardware_bound,
            certificate_chain=chain["chain"],
            attestation={
                "key_id": current_key["key_id"],
                "key_version": current_key["key_version"],
                "chain_hash": chain["chain_hash"],
                "provider_ref": provider_ref,
            },
        )

    def issue_certificate_chain(
        self,
        *,
        organization_id: str,
        key_family: str,
        subject: str,
        issuer: str,
    ) -> dict[str, Any]:
        current = self.pki.current_key(organization_id=organization_id, key_family=key_family)
        root = {
            "subject": issuer,
            "issuer": issuer,
            "key_id": current["key_id"],
            "key_version": current["key_version"],
            "public_key": current["public_key"],
        }
        intermediate = {
            "subject": f"{issuer} Intermediate",
            "issuer": issuer,
            "key_id": current["key_id"],
            "key_version": current["key_version"],
            "public_key": current["public_key"],
        }
        leaf = {
            "subject": subject,
            "issuer": intermediate["subject"],
            "key_id": current["key_id"],
            "key_version": current["key_version"],
            "public_key": current["public_key"],
        }
        chain = [root, intermediate, leaf]
        chain_hash = _hash_chain(chain)
        self.repository.record_certificate_chain(
            organization_id=organization_id,
            key_id=current["key_id"],
            subject=subject,
            issuer=issuer,
            chain=chain,
        )
        return {
            "organization_id": organization_id,
            "key_family": key_family,
            "chain": chain,
            "chain_hash": chain_hash,
            "certificate_authority": issuer,
        }

    def certificate_chains(self, organization_id: str | None = None) -> list[dict[str, Any]]:
        return self.repository.list_certificate_chains(organization_id=organization_id)

    def verify_certificate_chain(self, organization_id: str | None = None) -> dict[str, Any]:
        return {
            "organization_id": organization_id,
            "valid": self.repository.verify_certificate_chain(organization_id=organization_id),
            "chains": self.certificate_chains(organization_id=organization_id),
        }

    def status(self, organization_id: str | None = None, key_family: str | None = None) -> dict[str, Any]:
        return {
            "organization_id": organization_id,
            "key_family": key_family,
            "backends": self.repository.list_crypto_backends(
                organization_id=organization_id,
                key_family=key_family,
            ),
            "certificate_chains": self.certificate_chains(organization_id=organization_id),
            "certificate_valid": self.repository.verify_certificate_chain(organization_id=organization_id),
        }


__all__ = ["CryptoStorageHardeningService"]
