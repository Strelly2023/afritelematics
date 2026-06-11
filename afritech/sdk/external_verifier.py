from __future__ import annotations

from typing import Any

from afritech.crypto.public_chain_anchor import build_public_chain_anchor_receipt


class ExternalVerifierClient:
    def decode_architecture_proof_response(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("classification") != "CONTROLLED_PUBLIC_ARCHITECTURE_PROOF":
            raise ValueError("invalid architecture proof classification")
        proof = payload.get("proof")
        if not isinstance(proof, dict):
            raise ValueError("architecture proof payload missing proof")
        required = (
            "proof_id",
            "proof_hash",
            "anchor_commitment",
            "publication_envelope",
            "public_chain_receipt",
            "verification_packet",
            "registry_entry",
        )
        missing = [field for field in required if field not in proof]
        if missing:
            raise ValueError(f"architecture proof response missing fields: {missing}")
        return payload

    def verify_architecture_proof_locally(self, payload: dict[str, Any]) -> dict[str, Any]:
        decoded = self.decode_architecture_proof_response(payload)
        proof = decoded["proof"]
        receipt = build_public_chain_anchor_receipt(
            anchor_id=str(proof["anchor_commitment"]["anchor_id"]),
            publication_id=str(proof["publication_envelope"]["publication_id"]),
            commitment_hash=str(proof["anchor_commitment"]["commitment_hash"]),
            publication_hash=str(proof["publication_envelope"]["publication_hash"]),
            proof_hash=str(proof["proof_hash"]),
            chain_name="Public Architecture Proof Chain",
            network="papc-testnet",
        ).canonical_dict()
        matches = receipt == proof["public_chain_receipt"]
        return {
            "proof_id": proof["proof_id"],
            "verification_status": "VERIFIED" if matches else "REJECTED",
            "anchor_id": proof["anchor_commitment"]["anchor_id"],
            "chain_receipt_matches": matches,
            "authority_boundary": proof["authority_boundary"],
        }

    def decode_public_chain_receipt(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("classification") != "CONTROLLED_PUBLIC_CHAIN_RECEIPT":
            raise ValueError("invalid public chain receipt classification")
        if payload.get("status") != "READY":
            raise ValueError("public chain receipt not ready")
        if "chain_receipt" not in payload:
            raise ValueError("public chain receipt payload missing chain_receipt")
        return payload

    def decode_public_trust_dashboard(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("classification") != "PUBLIC_TRUST_DASHBOARD":
            raise ValueError("invalid public trust dashboard classification")
        if "integrity" not in payload or "chain" not in payload or "surfaces" not in payload:
            raise ValueError("public trust dashboard payload missing integrity, chain, or surfaces")
        return payload

    def decode_partner_demo_narrative(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("classification") != "PARTNER_LIVE_SYSTEM_INTEGRITY_DEMO":
            raise ValueError("invalid partner demo classification")
        if "walkthrough" not in payload or "proof" not in payload:
            raise ValueError("partner demo payload missing walkthrough or proof")
        return payload
