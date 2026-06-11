"""Controlled public verification and registry lookup endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from afritech.architecture.integrity_proof import build_architecture_integrity_proof
from afritech.partner_registry import PartnerRegistryStore
from afritech.partner_verification import PartnerVerificationStore
from afritech.trust_network import TrustRegistryStore


def build_public_verification_router(
    *,
    verification_store: PartnerVerificationStore,
    registry_store: TrustRegistryStore,
    partner_store: PartnerRegistryStore,
) -> APIRouter:
    router = APIRouter(tags=["public-verification"])

    @router.get("/public/verify/health")
    def public_verify_health() -> dict[str, Any]:
        return {
            "status": "ready",
            "classification": "CONTROLLED_PUBLIC_VERIFICATION",
            "authority_boundary": "public_lookup_is_registry_and_packet_read_only",
        }

    @router.get("/public/registry")
    def public_registry() -> dict[str, Any]:
        proof = build_architecture_integrity_proof().canonical_dict()
        entries = [entry.canonical_dict() for entry in registry_store.list_entries()]
        entries.append(proof["registry_entry"])
        return {
            "classification": "CONTROLLED_PUBLIC_VERIFICATION",
            "entries": entries,
            "count": len(entries),
            "authority_boundary": "public_lookup_is_registry_and_packet_read_only",
        }

    @router.get("/public/verify/{anchor_id}")
    def public_verify(anchor_id: str) -> dict[str, Any]:
        proof = build_architecture_integrity_proof().canonical_dict()
        if proof["verification_packet"]["anchor_id"] == anchor_id:
            return {
                "classification": "CONTROLLED_PUBLIC_VERIFICATION",
                "authority_boundary": "trace_and_replay_remain_truth_public_surface_reads_exports_only",
                "packet": proof["verification_packet"],
                "registry_entry": proof["registry_entry"],
            }
        try:
            packet = verification_store.load(anchor_id)
            registry_entry = registry_store.load(anchor_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="anchor not found") from exc
        return {
            "classification": "CONTROLLED_PUBLIC_VERIFICATION",
            "authority_boundary": "trace_and_replay_remain_truth_public_surface_reads_exports_only",
            "packet": packet.canonical_dict(),
            "registry_entry": registry_entry.canonical_dict(),
        }

    @router.get("/public/partners/registry")
    def public_partner_registry() -> dict[str, Any]:
        partners = [
            entry.canonical_dict()
            for entry in partner_store.list_entries()
            if entry.public_endpoint_enabled or entry.trust_registry_enabled
        ]
        return {
            "classification": "CONTROLLED_PUBLIC_PARTNER_REGISTRY",
            "partners": partners,
            "count": len(partners),
            "authority_boundary": "partner_registry_indexes_adoption_only",
        }

    return router


__all__ = ["build_public_verification_router"]
