"""Partner trust governance, onboarding, and SLA registry for NovaRide."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


ALLOWED_LIFECYCLE_STATES = frozenset({"pending", "reviewing", "approved", "active", "rejected"})
ALLOWED_TRUST_LEVELS = frozenset({"sandbox", "verified", "enterprise", "regulator"})
ALLOWED_SLA_PLANS = frozenset({"sandbox", "growth", "enterprise"})

SLA_PLANS: dict[str, dict[str, Any]] = {
    "sandbox": {
        "requests_per_min": 100,
        "requests_per_day": 5_000,
        "signatures_per_day": 1_000,
        "price_per_api_call_aud": 0.0,
        "price_per_signature_aud": 0.0,
        "support_tier": "community",
    },
    "growth": {
        "requests_per_min": 1_000,
        "requests_per_day": 100_000,
        "signatures_per_day": 50_000,
        "price_per_api_call_aud": 0.00015,
        "price_per_signature_aud": 0.001,
        "support_tier": "standard",
    },
    "enterprise": {
        "requests_per_min": None,
        "requests_per_day": None,
        "signatures_per_day": None,
        "price_per_api_call_aud": 0.00008,
        "price_per_signature_aud": 0.0005,
        "support_tier": "priority",
    },
}


def _json_ready(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _normalize_usage(usage: dict[str, int] | None) -> dict[str, int]:
    normalized = {
        "api_calls": 0,
        "signatures": 0,
        "requests": 0,
        "transactions": 0,
        "errors": 0,
    }
    for key, value in (usage or {}).items():
        normalized[str(key)] = int(value)
    normalized["requests"] = int(
        normalized["requests"] or normalized["api_calls"] or normalized["transactions"]
    )
    return normalized


def _build_limits(sla_plan: str) -> dict[str, Any]:
    plan = SLA_PLANS.get(sla_plan)
    if plan is None:
        raise ValueError("invalid_sla_plan")
    return {
        "plan": sla_plan,
        "requests_per_min": plan["requests_per_min"],
        "requests_per_day": plan["requests_per_day"],
        "signatures_per_day": plan["signatures_per_day"],
        "support_tier": plan["support_tier"],
    }


def _build_billing(usage: dict[str, int], sla_plan: str) -> dict[str, Any]:
    plan = SLA_PLANS[sla_plan]
    api_cost = usage["api_calls"] * float(plan["price_per_api_call_aud"])
    signature_cost = usage["signatures"] * float(plan["price_per_signature_aud"])
    total = round(api_cost + signature_cost, 6)
    return {
        "currency": "AUD",
        "plan": sla_plan,
        "price_per_api_call_aud": plan["price_per_api_call_aud"],
        "price_per_signature_aud": plan["price_per_signature_aud"],
        "estimated_cost_aud": total,
        "line_items": {
            "api_calls": round(api_cost, 6),
            "signatures": round(signature_cost, 6),
        },
    }


def _evaluate_sla_status(
    usage: dict[str, int],
    limits: dict[str, Any],
) -> tuple[str, str]:
    breached = False
    warning = False
    if limits.get("requests_per_day") is not None:
        quota = int(limits["requests_per_day"])
        if usage["requests"] > quota:
            breached = True
        elif usage["requests"] >= int(quota * 0.8):
            warning = True
    if limits.get("signatures_per_day") is not None:
        quota = int(limits["signatures_per_day"])
        if usage["signatures"] > quota:
            breached = True
        elif usage["signatures"] >= int(quota * 0.8):
            warning = True
    if breached:
        return "breached", "throttled"
    if warning:
        return "warning", "enabled"
    return "healthy", "enabled"


def _normalize_permissions(permissions: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    return tuple(sorted({str(permission) for permission in (permissions or ()) if str(permission).strip()}))


def _normalize_keys(keys: tuple[dict[str, Any], ...] | list[dict[str, Any]] | None) -> tuple[dict[str, Any], ...]:
    normalized: list[dict[str, Any]] = []
    for key in keys or ():
        if not isinstance(key, dict):
            continue
        key_id = str(key.get("key_id") or "").strip()
        public_key = str(key.get("public_key") or "").strip()
        if not key_id or not public_key:
            continue
        normalized.append(
            {
                "key_id": key_id,
                "public_key": public_key,
                "status": str(key.get("status", "active")).strip().lower() or "active",
                "usage": tuple(str(item) for item in (key.get("usage") or ())),
            }
        )
    return tuple(sorted(normalized, key=lambda item: item["key_id"]))


@dataclass(frozen=True)
class PartnerGovernanceRecord:
    org_id: str
    organization: str
    country: str
    business_type: str
    registration_number: str | None
    website: str | None
    contact_email: str
    status: str
    approval_state: str
    activation_state: str
    trust_level: str
    sla_plan: str
    permissions: tuple[str, ...]
    keys: tuple[dict[str, Any], ...]
    active_key_id: str | None
    usage: dict[str, int]
    limits: dict[str, Any]
    billing: dict[str, Any]
    trust_score: int
    risk_score: int
    sla_state: str
    enforcement_state: str
    created_at: str
    reviewed_at: str | None
    approved_at: str | None
    activated_at: str | None
    rejected_at: str | None
    rejection_reason: str | None
    reviewer_id: str | None
    review_notes: str | None
    authority_boundary: str = "partner_governance_indexes_adoption_only"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema": "afritech.partner_governance_record.v1",
            "org_id": self.org_id,
            "organization": self.organization,
            "country": self.country,
            "business_type": self.business_type,
            "registration_number": self.registration_number,
            "website": self.website,
            "contact_email": self.contact_email,
            "status": self.status,
            "approval_state": self.approval_state,
            "activation_state": self.activation_state,
            "trust_level": self.trust_level,
            "sla_plan": self.sla_plan,
            "permissions": list(self.permissions),
            "keys": _json_ready(self.keys),
            "active_key_id": self.active_key_id,
            "usage": dict(self.usage),
            "limits": _json_ready(self.limits),
            "billing": _json_ready(self.billing),
            "trust_score": self.trust_score,
            "risk_score": self.risk_score,
            "sla_state": self.sla_state,
            "enforcement_state": self.enforcement_state,
            "created_at": self.created_at,
            "reviewed_at": self.reviewed_at,
            "approved_at": self.approved_at,
            "activated_at": self.activated_at,
            "rejected_at": self.rejected_at,
            "rejection_reason": self.rejection_reason,
            "reviewer_id": self.reviewer_id,
            "review_notes": self.review_notes,
            "sla": {
                "plan": self.sla_plan,
                "limits": _json_ready(self.limits),
                "state": self.sla_state,
            },
            "authority_boundary": self.authority_boundary,
        }


class PartnerGovernanceStore:
    """In-memory partner trust-governance registry."""

    def __init__(self, entries: tuple[PartnerGovernanceRecord, ...] = ()) -> None:
        self._entries = {entry.org_id: entry for entry in entries}

    def register(self, entry: PartnerGovernanceRecord) -> None:
        self._entries[entry.org_id] = entry

    def list_entries(self) -> tuple[PartnerGovernanceRecord, ...]:
        return tuple(sorted(self._entries.values(), key=lambda entry: entry.org_id))

    def load(self, org_id: str) -> PartnerGovernanceRecord:
        if org_id not in self._entries:
            raise KeyError(org_id)
        return self._entries[org_id]

    def _replace(self, org_id: str, **changes: Any) -> PartnerGovernanceRecord:
        updated = replace(self.load(org_id), **changes)
        self.register(updated)
        return updated

    def review(
        self,
        org_id: str,
        *,
        reviewer_id: str | None = None,
        review_notes: str | None = None,
    ) -> PartnerGovernanceRecord:
        current = self.load(org_id)
        if current.status == "rejected":
            raise ValueError("partner_review_rejected")
        return self._replace(
            org_id,
            status="reviewing",
            approval_state="reviewing",
            review_notes=review_notes or current.review_notes,
            reviewer_id=reviewer_id or current.reviewer_id,
            reviewed_at=_now(),
        )

    def approve(
        self,
        org_id: str,
        *,
        reviewer_id: str | None = None,
        trust_level: str | None = None,
        sla_plan: str | None = None,
        permissions: tuple[str, ...] | list[str] | None = None,
        key_id: str | None = None,
        public_key: str | None = None,
        key_usage: tuple[str, ...] | list[str] | None = None,
        review_notes: str | None = None,
    ) -> PartnerGovernanceRecord:
        current = self.load(org_id)
        resolved_trust_level = trust_level or current.trust_level
        if resolved_trust_level not in ALLOWED_TRUST_LEVELS:
            raise ValueError("invalid_trust_level")
        resolved_sla_plan = sla_plan or current.sla_plan
        if resolved_sla_plan not in ALLOWED_SLA_PLANS:
            raise ValueError("invalid_sla_plan")
        resolved_permissions = _normalize_permissions(permissions) or current.permissions
        resolved_keys = current.keys
        if key_id or public_key:
            if not key_id or not public_key:
                raise ValueError("partner_key_requires_key_id_and_public_key")
            resolved_key = {
                "key_id": str(key_id),
                "public_key": str(public_key),
                "status": "active",
                "usage": tuple(str(item) for item in (key_usage or ("contract_signing", "webhooks"))),
            }
            resolved_keys = tuple(
                key for key in current.keys if key["key_id"] != resolved_key["key_id"]
            ) + (resolved_key,)
        if not resolved_keys:
            raise ValueError("partner_key_required")
        active_key_id = next(
            (str(key["key_id"]) for key in resolved_keys if str(key.get("status", "active")) == "active"),
            str(resolved_keys[0]["key_id"]),
        )
        usage = _normalize_usage(current.usage)
        limits = _build_limits(resolved_sla_plan)
        billing = _build_billing(usage, resolved_sla_plan)
        trust_score = max(0, min(100, 60 + (10 if resolved_trust_level != "sandbox" else 0) + len(resolved_keys) * 5))
        sla_state, enforcement_state = _evaluate_sla_status(usage, limits)
        return self._replace(
            org_id,
            status="approved",
            approval_state="approved",
            activation_state="inactive",
            trust_level=resolved_trust_level,
            sla_plan=resolved_sla_plan,
            permissions=resolved_permissions,
            keys=resolved_keys,
            active_key_id=active_key_id,
            usage=usage,
            limits=limits,
            billing=billing,
            trust_score=trust_score,
            risk_score=max(0, 100 - trust_score),
            sla_state=sla_state,
            enforcement_state=enforcement_state,
            reviewer_id=reviewer_id or current.reviewer_id,
            review_notes=review_notes or current.review_notes,
            reviewed_at=current.reviewed_at or _now(),
            approved_at=_now(),
            rejected_at=None,
            rejection_reason=None,
        )

    def activate(self, org_id: str, *, reviewer_id: str | None = None) -> PartnerGovernanceRecord:
        current = self.load(org_id)
        if current.approval_state != "approved":
            raise ValueError("partner_must_be_approved_before_activation")
        return self._replace(
            org_id,
            status="active",
            activation_state="active",
            activated_at=_now(),
            reviewer_id=reviewer_id or current.reviewer_id,
        )

    def reject(
        self,
        org_id: str,
        *,
        reviewer_id: str | None = None,
        rejection_reason: str | None = None,
    ) -> PartnerGovernanceRecord:
        current = self.load(org_id)
        return self._replace(
            org_id,
            status="rejected",
            approval_state="rejected",
            activation_state="suspended",
            rejected_at=_now(),
            rejection_reason=rejection_reason or "rejected_by_governance",
            reviewer_id=reviewer_id or current.reviewer_id,
        )

    def record_usage(
        self,
        org_id: str,
        *,
        api_calls: int = 0,
        signatures: int = 0,
        requests: int = 0,
        transactions: int = 0,
        errors: int = 0,
    ) -> PartnerGovernanceRecord:
        current = self.load(org_id)
        usage = _normalize_usage(current.usage)
        usage["api_calls"] += int(api_calls)
        usage["signatures"] += int(signatures)
        usage["requests"] += int(requests)
        usage["transactions"] += int(transactions)
        usage["errors"] += int(errors)
        billing = _build_billing(usage, current.sla_plan)
        sla_state, enforcement_state = _evaluate_sla_status(usage, current.limits)
        return self._replace(
            org_id,
            usage=usage,
            billing=billing,
            sla_state=sla_state,
            enforcement_state=enforcement_state,
        )

    def usage_snapshot(self, org_id: str) -> dict[str, Any]:
        record = self.load(org_id)
        return {
            "org_id": record.org_id,
            "status": record.status,
            "sla_state": record.sla_state,
            "enforcement_state": record.enforcement_state,
            "usage": dict(record.usage),
            "limits": _json_ready(record.limits),
            "billing": _json_ready(record.billing),
            "trust_level": record.trust_level,
            "sla_plan": record.sla_plan,
            "active_key_id": record.active_key_id,
        }

    def limit_snapshot(self, org_id: str) -> dict[str, Any]:
        record = self.load(org_id)
        return {
            "org_id": record.org_id,
            "sla_plan": record.sla_plan,
            "limits": _json_ready(record.limits),
            "permissions": list(record.permissions),
            "trust_level": record.trust_level,
            "sla_state": record.sla_state,
            "enforcement_state": record.enforcement_state,
        }

    def key_snapshot(self, org_id: str) -> dict[str, Any]:
        record = self.load(org_id)
        return {
            "org_id": record.org_id,
            "active_key_id": record.active_key_id,
            "keys": _json_ready(record.keys),
        }


def build_partner_governance_record(
    *,
    org_id: str,
    organization: str,
    country: str,
    business_type: str,
    contact_email: str,
    registration_number: str | None = None,
    website: str | None = None,
    status: str = "pending",
    approval_state: str = "pending",
    activation_state: str = "inactive",
    trust_level: str = "sandbox",
    sla_plan: str = "sandbox",
    permissions: tuple[str, ...] | list[str] | None = None,
    keys: tuple[dict[str, Any], ...] | list[dict[str, Any]] | None = None,
    active_key_id: str | None = None,
    usage: dict[str, int] | None = None,
    trust_score: int | None = None,
    risk_score: int | None = None,
    reviewer_id: str | None = None,
    review_notes: str | None = None,
    reviewed_at: str | None = None,
    approved_at: str | None = None,
    activated_at: str | None = None,
    rejected_at: str | None = None,
    rejection_reason: str | None = None,
) -> PartnerGovernanceRecord:
    if not org_id.strip():
        raise ValueError("org_id required")
    if not organization.strip():
        raise ValueError("organization required")
    if not contact_email.strip():
        raise ValueError("contact_email required")
    if status not in ALLOWED_LIFECYCLE_STATES:
        raise ValueError("invalid_partner_status")
    if approval_state not in ALLOWED_LIFECYCLE_STATES:
        raise ValueError("invalid_partner_approval_state")
    if activation_state not in {"inactive", "active", "suspended"}:
        raise ValueError("invalid_partner_activation_state")
    if trust_level not in ALLOWED_TRUST_LEVELS:
        raise ValueError("invalid_trust_level")
    if sla_plan not in ALLOWED_SLA_PLANS:
        raise ValueError("invalid_sla_plan")
    normalized_permissions = _normalize_permissions(permissions)
    normalized_keys = _normalize_keys(keys)
    normalized_usage = _normalize_usage(usage)
    limits = _build_limits(sla_plan)
    billing = _build_billing(normalized_usage, sla_plan)
    score = trust_score if trust_score is not None else 50 + len(normalized_keys) * 5
    sla_state, enforcement_state = _evaluate_sla_status(normalized_usage, limits)
    return PartnerGovernanceRecord(
        org_id=org_id,
        organization=organization,
        country=country,
        business_type=business_type,
        registration_number=registration_number,
        website=website,
        contact_email=contact_email,
        status=status,
        approval_state=approval_state,
        activation_state=activation_state,
        trust_level=trust_level,
        sla_plan=sla_plan,
        permissions=normalized_permissions,
        keys=normalized_keys,
        active_key_id=active_key_id
        or next((str(key["key_id"]) for key in normalized_keys if key["status"] == "active"), None),
        usage=normalized_usage,
        limits=limits,
        billing=billing,
        trust_score=score,
        risk_score=risk_score if risk_score is not None else max(0, 100 - score),
        sla_state=sla_state,
        enforcement_state=enforcement_state,
        created_at=_now(),
        reviewed_at=reviewed_at,
        approved_at=approved_at,
        activated_at=activated_at,
        rejected_at=rejected_at,
        rejection_reason=rejection_reason,
        reviewer_id=reviewer_id,
        review_notes=review_notes,
    )


def seed_partner_governance_registry() -> tuple[PartnerGovernanceRecord, ...]:
    return (
        build_partner_governance_record(
            org_id="partner-city-ops",
            organization="City Mobility Operations",
            country="AU",
            business_type="government",
            registration_number="GOV-NSW-88412",
            website="https://cityops.example",
            contact_email="ops@cityops.example",
            status="active",
            approval_state="approved",
            activation_state="active",
            trust_level="enterprise",
            sla_plan="enterprise",
            permissions=("sign_contract", "read_logs", "view_billing", "publish_webhooks"),
            keys=(
                {
                    "key_id": "cityops-key-01",
                    "public_key": "Y2l0eS1vcHMtcHViLWtleQ==",
                    "status": "active",
                    "usage": ("contract_signing", "webhooks"),
                },
            ),
            active_key_id="cityops-key-01",
            usage={"api_calls": 124_500, "signatures": 8_220, "requests": 124_500, "transactions": 0, "errors": 12},
            reviewer_id="gov-reviewer-1",
            reviewed_at="2026-06-20T00:00:00+00:00",
            approved_at="2026-06-22T00:00:00+00:00",
            activated_at="2026-06-23T00:00:00+00:00",
            review_notes="Public-sector rollout with enterprise trust posture.",
        ),
        build_partner_governance_record(
            org_id="partner-insure-1",
            organization="Trusted Claims Network",
            country="ZA",
            business_type="insurance",
            registration_number="REG-ZA-99182",
            website="https://claims.example",
            contact_email="platform@claims.example",
            status="reviewing",
            approval_state="reviewing",
            activation_state="inactive",
            trust_level="sandbox",
            sla_plan="growth",
            permissions=("read_logs", "view_billing"),
            keys=(
                {
                    "key_id": "claims-key-01",
                    "public_key": "Y2xhaW1zLXAtdWJsaWMta2V5",
                    "status": "active",
                    "usage": ("contract_signing",),
                },
            ),
            active_key_id="claims-key-01",
            usage={"api_calls": 31_200, "signatures": 1_200, "requests": 31_200, "transactions": 640, "errors": 4},
            reviewer_id="verifier-7",
            reviewed_at="2026-06-24T00:00:00+00:00",
            review_notes="Key registration completed, waiting on proof of SLA acceptance.",
        ),
        build_partner_governance_record(
            org_id="partner-bank-1",
            organization="Evidence Banking Group",
            country="KE",
            business_type="finance",
            registration_number="REG-KE-77812",
            website="https://bank.example",
            contact_email="integrations@bank.example",
            status="pending",
            approval_state="pending",
            activation_state="inactive",
            trust_level="sandbox",
            sla_plan="sandbox",
            permissions=("read_logs",),
            keys=(),
            usage={"api_calls": 0, "signatures": 0, "requests": 0, "transactions": 0, "errors": 0},
        ),
    )


__all__ = [
    "ALLOWED_LIFECYCLE_STATES",
    "ALLOWED_SLA_PLANS",
    "ALLOWED_TRUST_LEVELS",
    "PartnerGovernanceRecord",
    "PartnerGovernanceStore",
    "SLA_PLANS",
    "build_partner_governance_record",
    "seed_partner_governance_registry",
]
