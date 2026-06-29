"""Partner certification API surfaces for the NovaRide ecosystem registry."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from afritech.api.auth.jwt_device_auth import require_roles
from afritech.partner_certification import (
    PartnerCertificationStore,
    seed_partner_certification_registry,
)
from afritech.partner_registry import PartnerRegistryStore, seed_partner_registry


def build_partner_certification_router(
    store: PartnerCertificationStore | None = None,
    partner_registry_store: PartnerRegistryStore | None = None,
) -> APIRouter:
    router = APIRouter(tags=["partner-certification"])
    certification_store = store or PartnerCertificationStore(seed_partner_certification_registry())
    registry_store = partner_registry_store or PartnerRegistryStore(seed_partner_registry())

    @router.get("/v1/partners/certifications")
    def list_partner_certifications(
        _: object = Depends(require_roles("OPERATOR", "VERIFIER", "PARTNER", "OBSERVER")),
    ) -> dict[str, Any]:
        return {"certifications": [entry.canonical_dict() for entry in certification_store.list_entries()]}

    @router.post("/v1/partners/{partner_id}/certify")
    def certify_partner(
        partner_id: str,
        payload: dict[str, Any],
        _: object = Depends(require_roles("OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            registry_store.load(partner_id)
            record = certification_store.certify(
                partner_id,
                supported_versions=tuple(str(version) for version in payload.get("supported_versions", ())),
                capabilities=tuple(str(capability) for capability in payload.get("capabilities", ())),
                sdk_language=(
                    None if payload.get("sdk_language") is None else str(payload["sdk_language"])
                ),
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="partner not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return record.canonical_dict()

    @router.get("/v1/partners/{partner_id}/certificate")
    def get_partner_certificate(
        partner_id: str,
        _: object = Depends(require_roles("OPERATOR", "VERIFIER", "PARTNER", "OBSERVER")),
    ) -> dict[str, Any]:
        try:
            record = certification_store.load(partner_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="certificate not found") from exc
        return record.canonical_dict()

    @router.get("/v1/partners/{partner_id}/verification")
    def get_partner_verification(
        partner_id: str,
        _: object = Depends(require_roles("OPERATOR", "VERIFIER", "PARTNER", "OBSERVER")),
    ) -> dict[str, Any]:
        try:
            record = certification_store.load(partner_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="verification not found") from exc
        return {
            "partner_id": partner_id,
            "certificate_id": record.certificate_id,
            "status": record.status,
            "verification": dict(record.verification),
            "supported_versions": list(record.supported_versions),
            "capabilities": list(record.capabilities),
            "sdk_language": record.sdk_language,
        }

    return router


__all__ = ["build_partner_certification_router"]
