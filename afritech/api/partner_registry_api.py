"""Partner registry and onboarding API surfaces."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from afritech.api.auth.jwt_device_auth import require_roles
from afritech.partner_registry import (
    PartnerRegistryStore,
    build_partner_registry_entry,
    seed_partner_registry,
)


def build_partner_registry_router(
    store: PartnerRegistryStore | None = None,
) -> APIRouter:
    router = APIRouter(tags=["partner-registry"])
    registry_store = store or PartnerRegistryStore(seed_partner_registry())

    @router.get("/v1/partners/registry")
    def list_partner_registry(
        _: object = Depends(require_roles("OPERATOR", "VERIFIER", "PARTNER", "OBSERVER")),
    ) -> dict[str, Any]:
        return {"partners": [entry.canonical_dict() for entry in registry_store.list_entries()]}

    @router.post("/v1/partners/registry/register")
    def register_partner(
        payload: dict[str, Any],
        _: object = Depends(require_roles("OPERATOR", "PARTNER")),
    ) -> dict[str, Any]:
        try:
            entry = build_partner_registry_entry(
                partner_id=str(payload["partner_id"]),
                organization=str(payload["organization"]),
                sector=str(payload["sector"]),
                region_id=str(payload["region_id"]),
                integration_stage=str(payload.get("integration_stage", "discovery")),
                verifier_sdk_status=str(payload.get("verifier_sdk_status", "planned")),
                public_endpoint_enabled=bool(payload.get("public_endpoint_enabled", False)),
                trust_registry_enabled=bool(payload.get("trust_registry_enabled", False)),
                evidence_anchor_count=int(payload.get("evidence_anchor_count", 0)),
                status=str(payload.get("status", "DISCOVERY")),
            )
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=f"missing field: {exc.args[0]}") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        registry_store.register(entry)
        return entry.canonical_dict()

    @router.post("/v1/partners/registry/{partner_id}/onboard")
    def advance_partner_onboarding(
        partner_id: str,
        payload: dict[str, Any],
        _: object = Depends(require_roles("OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            entry = registry_store.advance(
                partner_id,
                status=str(payload["status"]),
                integration_stage=(
                    None if payload.get("integration_stage") is None else str(payload["integration_stage"])
                ),
                verifier_sdk_status=(
                    None
                    if payload.get("verifier_sdk_status") is None
                    else str(payload["verifier_sdk_status"])
                ),
                public_endpoint_enabled=payload.get("public_endpoint_enabled"),
                trust_registry_enabled=payload.get("trust_registry_enabled"),
                evidence_anchor_count=payload.get("evidence_anchor_count"),
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc.args[0])) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return entry.canonical_dict()

    return router


__all__ = ["build_partner_registry_router"]
