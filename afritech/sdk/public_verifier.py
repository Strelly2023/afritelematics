from __future__ import annotations

from typing import Any


class PublicVerifierClient:
    def decode_public_verification(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("classification") != "CONTROLLED_PUBLIC_VERIFICATION":
            raise ValueError("invalid public verification classification")
        if "packet" not in payload or "registry_entry" not in payload:
            raise ValueError("public verification payload missing packet or registry entry")
        return payload

    def decode_public_registry(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("classification") != "CONTROLLED_PUBLIC_VERIFICATION":
            raise ValueError("invalid public registry classification")
        if "entries" not in payload:
            raise ValueError("public registry payload missing entries")
        return payload

    def decode_architecture_proof(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("classification") != "CONTROLLED_PUBLIC_ARCHITECTURE_PROOF":
            raise ValueError("invalid architecture proof classification")
        proof = payload.get("proof")
        if not isinstance(proof, dict):
            raise ValueError("architecture proof payload missing proof")
        for required in ("anchor_commitment", "publication_envelope", "verification_packet", "registry_entry"):
            if required not in proof:
                raise ValueError(f"architecture proof missing {required}")
        return payload

    def decode_system_integrity_demo(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("classification") != "PARTNER_LIVE_SYSTEM_INTEGRITY_DEMO":
            raise ValueError("invalid system integrity demo classification")
        if "walkthrough" not in payload or "proof" not in payload:
            raise ValueError("system integrity demo payload missing walkthrough or proof")
        return payload
