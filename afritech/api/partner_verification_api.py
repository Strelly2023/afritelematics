"""FastAPI partner verification surface for replay-backed external evidence."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from afritech.api.auth.jwt_device_auth import require_roles
from afritech.partner_verification import (
    PartnerVerificationStore,
    build_partner_verification_packet,
)


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64
HASH_E = "e" * 64


def build_partner_verification_router(
    store: PartnerVerificationStore | None = None,
) -> APIRouter:
    router = APIRouter(tags=["partner-verification"])
    verification_store = store or PartnerVerificationStore(
        packets=(
            build_partner_verification_packet(
                tenant_id="tenant-core",
                region_id="mel-ap-southeast-2",
                trace_hash=HASH_A,
                replay_hash=HASH_B,
                receipt_hash=HASH_C,
                authority_hash=HASH_D,
                execution_fingerprint=HASH_E,
                publication_target="public-ledger-test-anchor",
                external_reference="ledger-ref-demo-001",
            ),
        )
    )

    @router.post("/v1/partner/verify")
    def verify_partner(
        payload: dict[str, Any],
        _: object = Depends(require_roles("PARTNER", "OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            packet = build_partner_verification_packet(
                tenant_id=str(payload["tenant_id"]),
                region_id=str(payload["region_id"]),
                trace_hash=str(payload["trace_hash"]),
                replay_hash=str(payload["replay_hash"]),
                receipt_hash=str(payload["receipt_hash"]),
                authority_hash=str(payload["authority_hash"]),
                execution_fingerprint=str(payload["execution_fingerprint"]),
                publication_target=str(payload["publication_target"]),
                network=str(payload.get("network", "external-ledger-testnet")),
                publisher_id=str(payload.get("publisher_id", "afritech-anchor-publisher")),
                external_reference=(
                    None
                    if payload.get("external_reference") is None
                    else str(payload["external_reference"])
                ),
                expected_anchor_id=(
                    None
                    if payload.get("expected_anchor_id") is None
                    else str(payload["expected_anchor_id"])
                ),
                expected_commitment_hash=(
                    None
                    if payload.get("expected_commitment_hash") is None
                    else str(payload["expected_commitment_hash"])
                ),
                expected_publication_hash=(
                    None
                    if payload.get("expected_publication_hash") is None
                    else str(payload["expected_publication_hash"])
                ),
                expected_receipt_hash=(
                    None
                    if payload.get("expected_receipt_hash") is None
                    else str(payload["expected_receipt_hash"])
                ),
            )
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=f"missing field: {exc.args[0]}") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        verification_store.remember(packet)
        return packet.canonical_dict()

    @router.get("/v1/partner/anchors/{anchor_id}")
    def get_partner_anchor(
        anchor_id: str,
        _: object = Depends(require_roles("PARTNER", "OPERATOR", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        try:
            packet = verification_store.load(anchor_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="anchor not found") from exc
        return packet.canonical_dict()

    return router


__all__ = ["build_partner_verification_router"]
