"""Partner governance API surfaces for onboarding, approval, SLA, and billing."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from afritech.api.auth.jwt_device_auth import require_roles
from afritech.partner_governance import (
    PartnerGovernanceStore,
    build_partner_governance_record,
    seed_partner_governance_registry,
)


def build_partner_governance_router(
    store: PartnerGovernanceStore | None = None,
) -> APIRouter:
    router = APIRouter(tags=["partner-governance"])
    governance_store = store or PartnerGovernanceStore(seed_partner_governance_registry())

    @router.get("/v1/trust/orgs")
    def list_organizations(
        _: object = Depends(require_roles("OPERATOR", "VERIFIER", "PARTNER", "OBSERVER")),
    ) -> dict[str, Any]:
        return {"organizations": [entry.canonical_dict() for entry in governance_store.list_entries()]}

    @router.post("/v1/trust/orgs/register")
    def register_organization(
        payload: dict[str, Any],
        _: object = Depends(require_roles("OPERATOR", "PARTNER")),
    ) -> dict[str, Any]:
        try:
            org_id = str(payload.get("org_id") or payload.get("partner_id") or "").strip()
            if not org_id:
                org_id = f"org-{uuid4().hex[:10]}"
            entry = build_partner_governance_record(
                org_id=org_id,
                organization=str(payload["organization"]),
                country=str(payload["country"]),
                business_type=str(payload["business_type"]),
                contact_email=str(payload["contact_email"]),
                registration_number=(
                    None if payload.get("registration_number") is None else str(payload["registration_number"])
                ),
                website=None if payload.get("website") is None else str(payload["website"]),
                status=str(payload.get("status", "pending")),
                approval_state=str(payload.get("approval_state", "pending")),
                activation_state=str(payload.get("activation_state", "inactive")),
                trust_level=str(payload.get("trust_level", "sandbox")),
                sla_plan=str(payload.get("sla_plan", "sandbox")),
                permissions=payload.get("permissions"),
                keys=payload.get("keys"),
                active_key_id=(
                    None if payload.get("active_key_id") is None else str(payload["active_key_id"])
                ),
                usage=payload.get("usage"),
                trust_score=(
                    None if payload.get("trust_score") is None else int(payload["trust_score"])
                ),
                risk_score=None if payload.get("risk_score") is None else int(payload["risk_score"]),
                reviewer_id=None if payload.get("reviewer_id") is None else str(payload["reviewer_id"]),
                review_notes=None if payload.get("review_notes") is None else str(payload["review_notes"]),
                reviewed_at=None if payload.get("reviewed_at") is None else str(payload["reviewed_at"]),
                approved_at=None if payload.get("approved_at") is None else str(payload["approved_at"]),
                activated_at=None if payload.get("activated_at") is None else str(payload["activated_at"]),
                rejected_at=None if payload.get("rejected_at") is None else str(payload["rejected_at"]),
                rejection_reason=(
                    None if payload.get("rejection_reason") is None else str(payload["rejection_reason"])
                ),
            )
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=f"missing field: {exc.args[0]}") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        governance_store.register(entry)
        return entry.canonical_dict()

    @router.get("/v1/trust/orgs/{org_id}")
    def get_organization(
        org_id: str,
        _: object = Depends(require_roles("OPERATOR", "VERIFIER", "PARTNER", "OBSERVER")),
    ) -> dict[str, Any]:
        try:
            return governance_store.load(org_id).canonical_dict()
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="organization not found") from exc

    @router.post("/v1/trust/orgs/{org_id}/review")
    def review_organization(
        org_id: str,
        payload: dict[str, Any],
        _: object = Depends(require_roles("OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            record = governance_store.review(
                org_id,
                reviewer_id=None if payload.get("reviewer_id") is None else str(payload["reviewer_id"]),
                review_notes=None if payload.get("review_notes") is None else str(payload["review_notes"]),
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="organization not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return record.canonical_dict()

    @router.post("/v1/trust/orgs/{org_id}/approve")
    def approve_organization(
        org_id: str,
        payload: dict[str, Any],
        _: object = Depends(require_roles("OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            record = governance_store.approve(
                org_id,
                reviewer_id=None if payload.get("reviewer_id") is None else str(payload["reviewer_id"]),
                trust_level=None if payload.get("trust_level") is None else str(payload["trust_level"]),
                sla_plan=None if payload.get("sla_plan") is None else str(payload["sla_plan"]),
                permissions=payload.get("permissions"),
                key_id=None if payload.get("key_id") is None else str(payload["key_id"]),
                public_key=None if payload.get("public_key") is None else str(payload["public_key"]),
                key_usage=payload.get("key_usage"),
                review_notes=None if payload.get("review_notes") is None else str(payload["review_notes"]),
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="organization not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return record.canonical_dict()

    @router.post("/v1/trust/orgs/{org_id}/activate")
    def activate_organization(
        org_id: str,
        payload: dict[str, Any],
        _: object = Depends(require_roles("OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            record = governance_store.activate(
                org_id,
                reviewer_id=None if payload.get("reviewer_id") is None else str(payload["reviewer_id"]),
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="organization not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return record.canonical_dict()

    @router.post("/v1/trust/orgs/{org_id}/reject")
    def reject_organization(
        org_id: str,
        payload: dict[str, Any],
        _: object = Depends(require_roles("OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            record = governance_store.reject(
                org_id,
                reviewer_id=None if payload.get("reviewer_id") is None else str(payload["reviewer_id"]),
                rejection_reason=(
                    None if payload.get("rejection_reason") is None else str(payload["rejection_reason"])
                ),
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="organization not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return record.canonical_dict()

    @router.get("/v1/trust/orgs/{org_id}/usage")
    def get_organization_usage(
        org_id: str,
        _: object = Depends(require_roles("OPERATOR", "VERIFIER", "PARTNER", "OBSERVER")),
    ) -> dict[str, Any]:
        try:
            return governance_store.usage_snapshot(org_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="organization not found") from exc

    @router.post("/v1/trust/orgs/{org_id}/usage")
    def record_organization_usage(
        org_id: str,
        payload: dict[str, Any],
        _: object = Depends(require_roles("OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            record = governance_store.record_usage(
                org_id,
                api_calls=int(payload.get("api_calls", 0)),
                signatures=int(payload.get("signatures", 0)),
                requests=int(payload.get("requests", 0)),
                transactions=int(payload.get("transactions", 0)),
                errors=int(payload.get("errors", 0)),
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="organization not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return record.canonical_dict()

    @router.get("/v1/trust/orgs/{org_id}/limits")
    def get_organization_limits(
        org_id: str,
        _: object = Depends(require_roles("OPERATOR", "VERIFIER", "PARTNER", "OBSERVER")),
    ) -> dict[str, Any]:
        try:
            return governance_store.limit_snapshot(org_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="organization not found") from exc

    @router.get("/v1/trust/orgs/{org_id}/keys")
    def get_organization_keys(
        org_id: str,
        _: object = Depends(require_roles("OPERATOR", "VERIFIER", "PARTNER", "OBSERVER")),
    ) -> dict[str, Any]:
        try:
            return governance_store.key_snapshot(org_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="organization not found") from exc

    @router.get("/v1/trust/orgs/{org_id}/billing")
    def get_organization_billing(
        org_id: str,
        _: object = Depends(require_roles("OPERATOR", "VERIFIER", "PARTNER", "OBSERVER")),
    ) -> dict[str, Any]:
        try:
            record = governance_store.load(org_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="organization not found") from exc
        return {
            "org_id": record.org_id,
            "status": record.status,
            "billing": record.billing,
            "sla_state": record.sla_state,
            "enforcement_state": record.enforcement_state,
        }

    @router.get("/v1/trust/orgs/{org_id}/sla")
    def get_organization_sla(
        org_id: str,
        _: object = Depends(require_roles("OPERATOR", "VERIFIER", "PARTNER", "OBSERVER")),
    ) -> dict[str, Any]:
        try:
            record = governance_store.load(org_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="organization not found") from exc
        return {
            "org_id": record.org_id,
            "status": record.status,
            "approval_state": record.approval_state,
            "activation_state": record.activation_state,
            "trust_level": record.trust_level,
            "sla_plan": record.sla_plan,
            "usage": dict(record.usage),
            "limits": record.limits,
            "sla_state": record.sla_state,
            "enforcement_state": record.enforcement_state,
        }

    return router


__all__ = ["build_partner_governance_router"]
