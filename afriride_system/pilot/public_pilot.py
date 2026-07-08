"""Public pilot access, geography, limits, and payment guardrails."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from afriride_system.api.auth import AuthClaims, claims_from_request


class PublicPilotError(RuntimeError):
    """Raised when a public-pilot boundary is violated."""


@dataclass(frozen=True)
class PublicPilotConfig:
    environment: str
    public_users_allowed: bool
    selected_external_users_allowed: bool
    pilot_transaction_limits_enabled: bool
    pilot_geography_restricted: bool
    pilot_monitoring_required: bool
    incident_response_required: bool
    rollback_required: bool
    support_required: bool
    production_credentials_allowed: bool
    ga_enabled: bool
    general_availability_allowed: bool
    unrestricted_signup_allowed: bool
    payment_mode: str
    max_transaction_amount_aud: int
    daily_transaction_limit_aud: int
    monthly_transaction_limit_aud: int
    identity_mode: str
    apk_distribution: str
    prr_required: bool
    production_real_payment_mode: str


@dataclass(frozen=True)
class PublicPilotApproval:
    public_pilot_approved: bool
    approval_id: str | None
    approved_by: str | None
    approved_at: str | None
    scope: str
    approved_regions: tuple[str, ...]
    approved_user_limit: int
    limited_real_payments_approved: bool
    real_identity_onboarding_approved: bool
    real_ride_requests_approved: bool
    public_pilot_live_payment_approved: bool
    max_transaction_amount_aud: int
    daily_transaction_limit_aud: int
    monthly_transaction_limit_aud: int
    ga_enabled: bool
    production_readiness_review_required: bool
    rollback_plan_approved: bool
    incident_response_approved: bool
    support_operations_approved: bool
    monitoring_verified: bool
    compliance_verified: bool
    approved_users: tuple[str, ...]
    approved_devices: tuple[str, ...]
    approved_drivers: tuple[str, ...]
    approved_operators: tuple[str, ...]
    approved_agents: tuple[str, ...]
    approved_merchants: tuple[str, ...]
    approved_businesses: tuple[str, ...]


_AUDIT_LOG: list[dict[str, Any]] = []
_DEVICE_BINDINGS: dict[str, str] = {}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


PUBLIC_PILOT_CONFIG_PATH = _repo_root() / "config" / "public_pilot.json"
PUBLIC_PILOT_APPROVAL_PATH = _repo_root() / "docs" / "public_pilot" / "PUBLIC_PILOT_APPROVAL.json"


@lru_cache(maxsize=1)
def load_public_pilot_config() -> PublicPilotConfig:
    payload = json.loads(PUBLIC_PILOT_CONFIG_PATH.read_text(encoding="utf-8"))
    return PublicPilotConfig(
        environment=str(payload["environment"]),
        public_users_allowed=bool(payload["public_users_allowed"]),
        selected_external_users_allowed=bool(payload["selected_external_users_allowed"]),
        pilot_transaction_limits_enabled=bool(payload["pilot_transaction_limits_enabled"]),
        pilot_geography_restricted=bool(payload["pilot_geography_restricted"]),
        pilot_monitoring_required=bool(payload["pilot_monitoring_required"]),
        incident_response_required=bool(payload["incident_response_required"]),
        rollback_required=bool(payload["rollback_required"]),
        support_required=bool(payload["support_required"]),
        production_credentials_allowed=bool(payload["production_credentials_allowed"]),
        ga_enabled=bool(payload["ga_enabled"]),
        general_availability_allowed=bool(payload["general_availability_allowed"]),
        unrestricted_signup_allowed=bool(payload["unrestricted_signup_allowed"]),
        payment_mode=str(payload["payment_mode"]),
        max_transaction_amount_aud=int(payload["max_transaction_amount_aud"]),
        daily_transaction_limit_aud=int(payload["daily_transaction_limit_aud"]),
        monthly_transaction_limit_aud=int(payload["monthly_transaction_limit_aud"]),
        identity_mode=str(payload["identity_mode"]),
        apk_distribution=str(payload["apk_distribution"]),
        prr_required=bool(payload["prr_required"]),
        production_real_payment_mode=str(payload["production_real_payment_mode"]),
    )


@lru_cache(maxsize=1)
def load_public_pilot_approval() -> PublicPilotApproval:
    payload = json.loads(PUBLIC_PILOT_APPROVAL_PATH.read_text(encoding="utf-8"))
    return PublicPilotApproval(
        public_pilot_approved=bool(payload["public_pilot_approved"]),
        approval_id=payload.get("approval_id"),
        approved_by=payload.get("approved_by"),
        approved_at=payload.get("approved_at"),
        scope=str(payload["scope"]),
        approved_regions=tuple(payload.get("approved_regions", [])),
        approved_user_limit=int(payload["approved_user_limit"]),
        limited_real_payments_approved=bool(payload["limited_real_payments_approved"]),
        real_identity_onboarding_approved=bool(payload["real_identity_onboarding_approved"]),
        real_ride_requests_approved=bool(payload["real_ride_requests_approved"]),
        public_pilot_live_payment_approved=bool(payload.get("public_pilot_live_payment_approved", False)),
        max_transaction_amount_aud=int(payload["max_transaction_amount_aud"]),
        daily_transaction_limit_aud=int(payload["daily_transaction_limit_aud"]),
        monthly_transaction_limit_aud=int(payload["monthly_transaction_limit_aud"]),
        ga_enabled=bool(payload["ga_enabled"]),
        production_readiness_review_required=bool(payload["production_readiness_review_required"]),
        rollback_plan_approved=bool(payload["rollback_plan_approved"]),
        incident_response_approved=bool(payload["incident_response_approved"]),
        support_operations_approved=bool(payload["support_operations_approved"]),
        monitoring_verified=bool(payload["monitoring_verified"]),
        compliance_verified=bool(payload["compliance_verified"]),
        approved_users=tuple(payload.get("approved_users", [])),
        approved_devices=tuple(payload.get("approved_devices", [])),
        approved_drivers=tuple(payload.get("approved_drivers", [])),
        approved_operators=tuple(payload.get("approved_operators", [])),
        approved_agents=tuple(payload.get("approved_agents", [])),
        approved_merchants=tuple(payload.get("approved_merchants", [])),
        approved_businesses=tuple(payload.get("approved_businesses", [])),
    )


def ensure_public_pilot_mode() -> PublicPilotConfig:
    config = load_public_pilot_config()
    if config.environment != "PUBLIC_PILOT":
        raise PublicPilotError("public_pilot_required")
    if config.ga_enabled or config.general_availability_allowed:
        raise PublicPilotError("ga_must_remain_disabled")
    if config.unrestricted_signup_allowed:
        raise PublicPilotError("unrestricted_signup_blocked")
    return config


def _approval_allows_real_payments() -> bool:
    approval = load_public_pilot_approval()
    return bool(
        approval.public_pilot_approved
        and approval.scope == "PUBLIC_PILOT_ONLY"
        and approval.public_pilot_live_payment_approved
        and approval.limited_real_payments_approved
    )


def _approval_allows_real_identity() -> bool:
    approval = load_public_pilot_approval()
    return bool(approval.public_pilot_approved and approval.real_identity_onboarding_approved)


def _approval_allows_real_rides() -> bool:
    approval = load_public_pilot_approval()
    return bool(approval.public_pilot_approved and approval.real_ride_requests_approved)


def _subject_allowed(claims: AuthClaims, surface: str) -> bool:
    approval = load_public_pilot_approval()
    subject = claims.sub
    role = claims.role.upper()
    surface = surface.lower()
    if surface in {"rider", "consumer", "personal"}:
        return role == "CUSTOMER" and subject in approval.approved_users
    if surface == "driver":
        return role == "DRIVER" and subject in approval.approved_drivers
    if surface == "operator":
        return role in {"OPERATOR", "FLEET_OWNER"} and subject in approval.approved_operators
    if surface == "agent":
        return role in {"DISPATCHER", "OPERATOR"} and subject in approval.approved_agents
    if surface == "merchant":
        return role in {"CLIENT", "SUPPLIER"} and subject in approval.approved_merchants
    if surface == "business":
        return role in {"CLIENT", "FLEET_OWNER"} and subject in approval.approved_businesses
    if surface == "identity":
        return role in {"VERIFIER", "PARTNER", "ADMIN", "OBSERVER", "OPERATOR"}
    return False


def _device_allowed(subject: str) -> bool:
    approval = load_public_pilot_approval()
    bound = _DEVICE_BINDINGS.get(subject)
    return bound in approval.approved_devices


def _region_allowed(region: str) -> bool:
    config = ensure_public_pilot_mode()
    if not config.pilot_geography_restricted:
        return True
    approval = load_public_pilot_approval()
    return region in approval.approved_regions


def record_event(
    *,
    actor: str,
    role: str,
    device: str,
    action: str,
    result: str,
    environment: str | None = None,
    region: str | None = None,
) -> None:
    config = ensure_public_pilot_mode()
    _AUDIT_LOG.append(
        {
            "timestamp": datetime.now(UTC).isoformat(),
            "actor": actor,
            "role": role,
            "device": device,
            "action": action,
            "result": result,
            "environment": environment or config.environment,
            "region": region,
        }
    )


def audit_log() -> list[dict[str, Any]]:
    return list(_AUDIT_LOG)


def reset_runtime_state() -> None:
    _AUDIT_LOG.clear()
    _DEVICE_BINDINGS.clear()
    load_public_pilot_config.cache_clear()
    load_public_pilot_approval.cache_clear()


def bind_device(subject: str, device_id: str) -> dict[str, Any]:
    config = ensure_public_pilot_mode()
    approval = load_public_pilot_approval()
    if subject not in (
        approval.approved_users
        + approval.approved_drivers
        + approval.approved_operators
        + approval.approved_agents
        + approval.approved_merchants
        + approval.approved_businesses
    ):
        raise PublicPilotError("subject_not_approved")
    if device_id not in approval.approved_devices:
        raise PublicPilotError("device_not_approved")
    _DEVICE_BINDINGS[subject] = device_id
    record_event(actor=subject, role="DEVICE", device=device_id, action="bind_device", result="bound", environment=config.environment)
    return {"status": "bound", "subject": subject, "device_id": device_id, "environment": config.environment}


def revoke_device(device_id: str) -> dict[str, Any]:
    config = ensure_public_pilot_mode()
    revoked = False
    for subject, bound_device in list(_DEVICE_BINDINGS.items()):
        if bound_device == device_id:
            del _DEVICE_BINDINGS[subject]
            revoked = True
            record_event(actor=subject, role="DEVICE", device=device_id, action="revoke_device", result="revoked", environment=config.environment)
    return {"status": "revoked" if revoked else "not_found", "device_id": device_id, "revoked": revoked, "environment": config.environment}


def check_access(claims: AuthClaims, device_id: str, surface: str, region: str) -> dict[str, Any]:
    config = ensure_public_pilot_mode()
    approval = load_public_pilot_approval()
    if claims.sub not in (
        approval.approved_users
        + approval.approved_drivers
        + approval.approved_operators
        + approval.approved_agents
        + approval.approved_merchants
        + approval.approved_businesses
    ):
        result = {"allowed": False, "reason": "user_not_approved"}
    elif not _device_allowed(claims.sub):
        result = {"allowed": False, "reason": "device_not_approved"}
    elif not _region_allowed(region):
        result = {"allowed": False, "reason": "region_not_approved"}
    elif not _subject_allowed(claims, surface):
        result = {"allowed": False, "reason": "role_not_authorized"}
    else:
        result = {"allowed": True, "reason": "approved"}
    record_event(
        actor=claims.sub,
        role=claims.role,
        device=device_id,
        action=f"access_check:{surface}",
        result=str(result["reason"]),
        environment=config.environment,
        region=region,
    )
    return {
        "environment": config.environment,
        "surface": surface,
        "region": region,
        "user_id": claims.sub,
        "role": claims.role,
        "device_id": device_id,
        **result,
    }


def public_pilot_payment_allowed() -> bool:
    return _approval_allows_real_payments()


def public_pilot_payment_guard(
    *,
    provider: str,
    method: str,
    amount_aud: int,
    real_payment: bool = False,
    payout: bool = False,
    production_credentials_present: bool = False,
    region: str = "Melbourne",
) -> None:
    config = ensure_public_pilot_mode()
    if not _region_allowed(region):
        raise PublicPilotError("region_not_approved")
    if amount_aud <= 0:
        raise PublicPilotError("invalid_amount")
    if amount_aud > config.max_transaction_amount_aud:
        raise PublicPilotError("transaction_limit_exceeded")
    approval = load_public_pilot_approval()
    if config.pilot_transaction_limits_enabled:
        if amount_aud > approval.max_transaction_amount_aud:
            raise PublicPilotError("approval_limit_exceeded")
        if config.payment_mode != "PILOT_REAL_LIMITED":
            raise PublicPilotError("invalid_public_pilot_payment_mode")
    if provider.startswith("live_"):
        if not public_pilot_payment_allowed():
            raise PublicPilotError("live_provider_requires_public_pilot_approval")
    if production_credentials_present and not config.production_credentials_allowed:
        raise PublicPilotError("production_credentials_rejected")
    if real_payment or payout:
        if not public_pilot_payment_allowed():
            raise PublicPilotError("public_pilot_real_payments_blocked")
    if method not in {"card", "wallet", "cash", "regional", "split", "qr"}:
        raise PublicPilotError("unsupported_public_pilot_payment_method")


def public_pilot_release_guard() -> dict[str, Any]:
    config = ensure_public_pilot_mode()
    approval = load_public_pilot_approval()
    if config.ga_enabled or config.general_availability_allowed:
        raise PublicPilotError("ga_must_remain_disabled")
    if approval.ga_enabled:
        raise PublicPilotError("approval_claims_ga_enabled")
    if not config.prr_required or not approval.production_readiness_review_required:
        raise PublicPilotError("prr_required")
    return {
        "environment": config.environment,
        "ga_enabled": config.ga_enabled,
        "general_availability_allowed": config.general_availability_allowed,
        "unrestricted_signup_allowed": config.unrestricted_signup_allowed,
        "pilot_transaction_limits_enabled": config.pilot_transaction_limits_enabled,
        "pilot_geography_restricted": config.pilot_geography_restricted,
        "pilot_monitoring_required": config.pilot_monitoring_required,
        "incident_response_required": config.incident_response_required,
        "rollback_required": config.rollback_required,
        "support_required": config.support_required,
        "ready_for_prr": bool(
            approval.public_pilot_approved
            and approval.limited_real_payments_approved
            and approval.real_identity_onboarding_approved
            and approval.real_ride_requests_approved
            and approval.monitoring_verified
            and approval.compliance_verified
            and approval.rollback_plan_approved
            and approval.incident_response_approved
            and approval.support_operations_approved
        ),
        "approval": asdict(approval),
    }


def mark_public_pilot_payment(payload: dict[str, Any]) -> dict[str, Any]:
    config = ensure_public_pilot_mode()
    return {
        **payload,
        "public_pilot": True,
        "simulated_payment": False,
        "public_pilot_environment": asdict(config),
        "public_pilot_approval": asdict(load_public_pilot_approval()),
    }


def reconciliation_report(*, recorded_aud: int, ledger_aud: int, transactions: int) -> dict[str, Any]:
    config = ensure_public_pilot_mode()
    balanced = recorded_aud == ledger_aud
    return {
        "environment": config.environment,
        "recorded_aud": recorded_aud,
        "ledger_aud": ledger_aud,
        "transactions": transactions,
        "balanced": balanced,
        "status": "reconciled" if balanced else "reconciliation_needed",
    }


def build_public_pilot_router() -> APIRouter:
    router = APIRouter(prefix="/v1/public-pilot", tags=["public-pilot"])

    def _claims(request: Request) -> AuthClaims:
        claims = claims_from_request(request)
        if claims is None:
            raise HTTPException(status_code=401, detail="bearer token required")
        return claims

    @router.get("/registry")
    def registry(request: Request) -> dict[str, Any]:
        claims = _claims(request)
        report = public_pilot_release_guard()
        return {
            "claims": {"user_id": claims.sub, "role": claims.role},
            "config": report["approval"],
            "environment": report["environment"],
        }

    @router.post("/access/check")
    def access_check(payload: dict[str, Any], request: Request) -> dict[str, Any]:
        claims = _claims(request)
        device_id = str(payload.get("device_id", "")).strip()
        region = str(payload.get("region", "")).strip() or "Melbourne"
        surface = str(payload.get("surface", "")).strip() or "rider"
        if not device_id:
            raise HTTPException(status_code=400, detail="device_id required")
        return check_access(claims, device_id, surface, region)

    @router.post("/limits/check")
    def limits_check(payload: dict[str, Any], request: Request) -> dict[str, Any]:
        _claims(request)
        try:
            public_pilot_payment_guard(
                provider=str(payload.get("provider", "wallet")),
                method=str(payload.get("method", "wallet")),
                amount_aud=int(payload.get("amount_aud", 0)),
                real_payment=bool(payload.get("real_payment", False)),
                payout=bool(payload.get("payout", False)),
                production_credentials_present=bool(payload.get("production_credentials_present", False)),
                region=str(payload.get("region", "Melbourne")),
            )
        except PublicPilotError as exc:
            return {"allowed": False, "reason": str(exc)}
        return {"allowed": True, "reason": "approved", "mode": load_public_pilot_config().payment_mode}

    @router.post("/reconciliation")
    def reconciliation(payload: dict[str, Any], request: Request) -> dict[str, Any]:
        _claims(request)
        return reconciliation_report(
            recorded_aud=int(payload.get("recorded_aud", 0)),
            ledger_aud=int(payload.get("ledger_aud", 0)),
            transactions=int(payload.get("transactions", 0)),
        )

    @router.get("/geography")
    def geography(request: Request) -> dict[str, Any]:
        _claims(request)
        config = ensure_public_pilot_mode()
        approval = load_public_pilot_approval()
        return {
            "environment": config.environment,
            "restricted": config.pilot_geography_restricted,
            "approved_regions": list(approval.approved_regions),
            "blocked_regions": ["unsupported"],
        }

    @router.get("/release/status")
    def release_status(request: Request) -> dict[str, Any]:
        _claims(request)
        return public_pilot_release_guard()

    return router
