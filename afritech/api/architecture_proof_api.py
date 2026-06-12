"""Public architecture proof and partner demo endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder

from afritech.api.auth.jwt_device_auth import require_roles
from afritech.architecture.blockchain_anchor import (
    BlockchainAnchorStore,
    build_chain_promotion_plan,
    publish_architecture_anchor_contract_with_profile,
    publish_architecture_anchor_with_profile,
)
from afritech.architecture.integrity_proof import (
    build_architecture_integrity_proof,
    build_partner_demo_payload,
)
from afritech.ops_dashboard import build_system_integrity_dashboard


LOGGER = logging.getLogger(__name__)


def _json_object(payload: dict[str, Any]) -> dict[str, Any]:
    encoded = jsonable_encoder(payload)
    if not isinstance(encoded, dict):
        raise RuntimeError("architecture payload must encode to JSON object")
    return encoded


def _error_payload(exc: Exception) -> dict[str, Any]:
    return _json_object(
        {
            "status": "generation_failed",
            "classification": "CONTROLLED_PUBLIC_ARCHITECTURE_PROOF",
            "runtime_boundary_status": "UNKNOWN",
            "authority_boundary": (
                "architecture proof generation failed safely; replay and governed "
                "execution remain the authority"
            ),
            "proof": None,
            "error": {
                "code": "ARCHITECTURE_PROOF_GENERATION_FAILED",
                "type": type(exc).__name__,
                "message": str(exc),
            },
        }
    )


def _public_architecture_proof_payload() -> dict[str, Any]:
    proof = build_architecture_integrity_proof().canonical_dict()
    return _json_object(
        {
            "status": "generated",
            "classification": "CONTROLLED_PUBLIC_ARCHITECTURE_PROOF",
            "proof_id": proof.get("proof_id"),
            "runtime_boundary_status": proof.get("runtime_boundary_status"),
            "authority_boundary": proof.get("authority_boundary"),
            "proof": proof,
        }
    )


def _safe_proof_payload() -> dict[str, Any]:
    try:
        return _public_architecture_proof_payload()
    except Exception as exc:
        LOGGER.exception("architecture proof generation failed")
        return _error_payload(exc)


def _proof() -> dict[str, Any]:
    return build_architecture_integrity_proof().canonical_dict()


def build_architecture_proof_router() -> APIRouter:
    router = APIRouter(tags=["architecture-proof"])
    blockchain_store = BlockchainAnchorStore()

    @router.get("/public/architecture/health")
    def architecture_proof_health() -> dict[str, Any]:
        try:
            proof = _proof()
        except Exception as exc:
            LOGGER.exception("architecture proof health failed")
            return _error_payload(exc)

        return _json_object(
            {
                "status": "ready",
                "classification": "CONTROLLED_PUBLIC_ARCHITECTURE_PROOF",
                "runtime_boundary_status": proof.get("runtime_boundary_status"),
                "anchor_id": proof.get("anchor_commitment", {}).get("anchor_id"),
                "authority_boundary": proof.get("authority_boundary"),
            }
        )

    @router.get("/public/architecture/proof")
    def public_architecture_proof() -> dict[str, Any]:
        return _safe_proof_payload()

    @router.get("/public/architecture/chain/networks")
    def public_chain_networks() -> dict[str, Any]:
        proof = _proof()

        return _json_object(
            {
                "classification": "PUBLIC_CHAIN_PROMOTION_PLAN",
                "status": "READY",
                "anchor_id": proof.get("verification_packet", {}).get("anchor_id"),
                "promotion": build_chain_promotion_plan(),
                "authority_boundary": proof.get("authority_boundary"),
            }
        )

    @router.get("/public/architecture/chain/{anchor_id}")
    def public_chain_receipt(anchor_id: str) -> dict[str, Any]:
        proof = _proof()
        expected_anchor_id = proof.get("verification_packet", {}).get("anchor_id")

        if expected_anchor_id != anchor_id:
            return _json_object(
                {
                    "classification": "CONTROLLED_PUBLIC_CHAIN_RECEIPT",
                    "status": "NOT_FOUND",
                    "anchor_id": anchor_id,
                    "authority_boundary": proof.get("authority_boundary"),
                }
            )

        return _json_object(
            {
                "classification": "CONTROLLED_PUBLIC_CHAIN_RECEIPT",
                "status": "READY",
                "anchor_id": anchor_id,
                "chain_receipt": proof.get("public_chain_receipt", {}),
                "authority_boundary": proof.get("authority_boundary"),
            }
        )

    @router.post("/v1/architecture/anchor/blockchain")
    def publish_architecture_anchor(
        payload: dict[str, Any],
        _: object = Depends(require_roles("OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        proof = _proof()

        try:
            profile_name = str(payload.get("profile", "sepolia"))
            anchor_id = str(proof.get("verification_packet", {}).get("anchor_id"))
            publication_id = str(proof.get("publication_envelope", {}).get("publication_id"))
            mode = str(payload.get("mode", "raw_transaction")).strip().lower()

            if mode in {"contract", "smart_contract", "architecture_anchor"}:
                publication = publish_architecture_anchor_contract_with_profile(
                    anchor_id=anchor_id,
                    publication_id=publication_id,
                    proof_hash=str(proof.get("proof_hash")),
                    profile_name=profile_name,
                    require_live=True,
                )
            else:
                publication = publish_architecture_anchor_with_profile(
                    anchor_id=anchor_id,
                    publication_id=publication_id,
                    signed_tx_hex=str(payload["signed_tx_hex"]),
                    profile_name=profile_name,
                    rpc_url=payload.get("rpc_url"),
                    contract_address=str(
                        payload.get(
                            "contract_address",
                            "0x0000000000000000000000000000000000000000",
                        )
                    ),
                    chain_name=payload.get("chain_name"),
                    network=payload.get("network"),
                    chain_id=payload.get("chain_id"),
                    explorer_base_url=payload.get("explorer_base_url"),
                )

        except KeyError as exc:
            raise HTTPException(status_code=400, detail=f"missing field: {exc}") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        blockchain_store.remember(publication)

        return _json_object(
            {
                "classification": "BLOCKCHAIN_ARCHITECTURE_ANCHOR_PUBLICATION",
                "proof_id": proof.get("proof_id"),
                "anchor_id": proof.get("verification_packet", {}).get("anchor_id"),
                "profile": profile_name,
                "mode": getattr(publication, "anchor_mode", "raw_transaction"),
                "publication": publication.canonical_dict(),
                "authority_boundary": proof.get("authority_boundary"),
            }
        )

    @router.get("/public/trust/dashboard")
    def public_trust_dashboard() -> dict[str, Any]:
        proof = _proof()
        latest = blockchain_store.latest()
        public_chain_receipt = proof.get("public_chain_receipt", {})

        return _json_object(
            {
                "classification": "PUBLIC_TRUST_DASHBOARD",
                "status": "READY",
                "authority_boundary": proof.get("authority_boundary"),
                "headline": "AfriTech public trust dashboard",
                "network": public_chain_receipt.get("network", "papc-testnet"),
                "integrity": {
                    "runtime_boundary_status": proof.get("runtime_boundary_status"),
                    "proof_id": proof.get("proof_id"),
                    "anchor_id": proof.get("anchor_commitment", {}).get("anchor_id"),
                    "publication_id": proof.get("publication_envelope", {}).get("publication_id"),
                    "verification_status": proof.get("verification_packet", {}).get(
                        "verification_status"
                    ),
                },
                "chain": {
                    "deterministic_receipt": public_chain_receipt,
                    "live_publication": None if latest is None else latest.canonical_dict(),
                    "promotion": build_chain_promotion_plan(),
                },
                "distribution": {
                    "verifier_cli": "afritech-verify",
                    "partner_session_cli": "afritech-verify-session",
                },
                "surfaces": [
                    {"label": "Architecture proof", "path": "/public/architecture/proof"},
                    {
                        "label": "Chain receipt",
                        "path": (
                            "/public/architecture/chain/"
                            f"{proof.get('verification_packet', {}).get('anchor_id')}"
                        ),
                    },
                    {
                        "label": "Chain networks",
                        "path": "/public/architecture/chain/networks",
                    },
                    {
                        "label": "Public verification",
                        "path": (
                            "/public/verify/"
                            f"{proof.get('verification_packet', {}).get('anchor_id')}"
                        ),
                    },
                    {
                        "label": "System integrity demo",
                        "path": "/public/demo/system-integrity",
                    },
                ],
            }
        )

    @router.get("/public/demo/system-integrity")
    def public_demo() -> dict[str, Any]:
        return _json_object(build_partner_demo_payload())

    @router.get("/v1/system/integrity/dashboard")
    def system_dashboard(
        _: object = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "PARTNER")),
    ) -> dict[str, Any]:
        return _json_object(build_system_integrity_dashboard())

    return router


__all__ = ["build_architecture_proof_router"]
