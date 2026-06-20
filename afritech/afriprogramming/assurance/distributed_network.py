from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from afritech.afriprogramming.assurance.pki import PKIService
from afritech.afriprogramming.persistence import PlatformStore, get_platform_store
from afritech.trust_federation import (
    build_federated_trust_certificate,
    verify_federated_trust_certificate,
)


def _hash_payload(payload: dict[str, Any]) -> str:
    import json

    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True)
class FederationPeer:
    node_id: str
    organization_id: str
    peer_organization_id: str
    jurisdiction: str
    role: str
    public_key_id: str
    endpoint: str
    trust_level: str
    status: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "organization_id": self.organization_id,
            "peer_organization_id": self.peer_organization_id,
            "jurisdiction": self.jurisdiction,
            "role": self.role,
            "public_key_id": self.public_key_id,
            "endpoint": self.endpoint,
            "trust_level": self.trust_level,
            "status": self.status,
        }


class DistributedTrustNetworkService:
    """Distributed trust network and cross-org federation helper."""

    def __init__(
        self,
        repository: PlatformStore | None = None,
        pki_service: PKIService | None = None,
    ) -> None:
        self.repository = repository or get_platform_store()
        self.pki_service = pki_service or PKIService(self.repository)

    def register_peer(
        self,
        *,
        organization_id: str,
        peer_organization_id: str,
        jurisdiction: str,
        role: str,
        public_key_id: str,
        endpoint: str,
        trust_level: str = "TRUSTED",
        status: str = "active",
    ) -> dict[str, Any]:
        return self.repository.store_federation_node(
            organization_id=organization_id,
            peer_organization_id=peer_organization_id,
            jurisdiction=jurisdiction,
            role=role,
            public_key_id=public_key_id,
            endpoint=endpoint,
            trust_level=trust_level,
            status=status,
        )

    def peers(self, organization_id: str | None = None) -> list[dict[str, Any]]:
        return self.repository.list_federation_nodes(organization_id=organization_id)

    def federation_certificate(self, *, quorum: int = 2) -> dict[str, Any]:
        certificate = build_federated_trust_certificate(quorum=quorum)
        return {
            "certificate": certificate.canonical_dict(),
            "verification": verify_federated_trust_certificate(certificate),
        }

    def issue_claim(
        self,
        *,
        organization_id: str,
        peer_organization_id: str,
        claim_type: str,
        payload: dict[str, Any],
        key_family: str = "federation",
        public_key_id: str | None = None,
    ) -> dict[str, Any]:
        signed = self.pki_service.sign(
            organization_id=organization_id,
            payload=payload,
            key_family=key_family,
        )
        claim_hash = _hash_payload(payload)
        record = self.repository.store_federation_claim(
            organization_id=organization_id,
            peer_organization_id=peer_organization_id,
            claim_type=claim_type,
            claim_hash=claim_hash,
            proof_hash=str(payload.get("proof_hash", claim_hash)),
            audit_hash=str(payload.get("audit_hash", claim_hash)),
            receipt_hash=str(payload.get("receipt_hash", claim_hash)),
            certification_hash=str(payload.get("certification_hash", claim_hash)),
            signature=signed["signature"],
            public_key_id=public_key_id or signed["key_id"],
            valid=True,
            payload=payload,
        )
        record = {
            **record,
            "key_family": key_family,
            "public_key": signed["public_key"],
        }
        self.repository.store_federation_event(
            organization_id=organization_id,
            peer_organization_id=peer_organization_id,
            event_type="federation.claim.issued",
            details=record,
        )
        return record

    def verify_claim(self, claim: dict[str, Any]) -> dict[str, Any]:
        payload = claim.get("payload") if isinstance(claim.get("payload"), dict) else None
        signature = str(claim.get("signature", ""))
        public_key = str(claim.get("public_key") or claim.get("public_key_id") or "")
        if public_key and len(public_key) < 32:
            key_family = str(claim.get("key_family") or "federation")
            key_id = public_key
            for key in self.pki_service.list_keys(
                organization_id=str(claim.get("organization_id", "")) or None,
                key_family=key_family,
                limit=1000,
            ):
                if key["key_id"] == key_id:
                    public_key = str(key["public_key"])
                    break
        if not payload or not signature or not public_key:
            return {"valid": False, "reason": "payload, signature and public_key required"}
        verified = self.pki_service.verify(
            public_key=public_key,
            payload=payload,
            signature=signature,
        )
        return {
            "valid": verified,
            "organization_id": claim.get("organization_id"),
            "peer_organization_id": claim.get("peer_organization_id"),
            "claim_hash": claim.get("claim_hash") or _hash_payload(payload),
        }

    def events(self, organization_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        return self.repository.list_federation_events(organization_id=organization_id, limit=limit)

    def claims(self, organization_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        return self.repository.list_federation_claims(organization_id=organization_id, limit=limit)


__all__ = ["DistributedTrustNetworkService", "FederationPeer"]
