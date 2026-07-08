"""Controlled pilot access, device, and payment guardrails."""

from __future__ import annotations

import json
import hashlib
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Header, HTTPException

from afriride_system.api.auth import JWT, AuthClaims


class ControlledPilotError(RuntimeError):
    """Raised when a controlled-pilot boundary is violated."""


@dataclass(frozen=True)
class ControlledPilotConfig:
    environment: str
    pilot_enabled: bool
    public_launch_allowed: bool
    general_availability_allowed: bool
    unrestricted_signup_allowed: bool
    approved_users_only: bool
    approved_devices_only: bool
    approved_operators_only: bool
    payment_mode: str
    live_payments_enabled: bool
    real_charging_enabled: bool
    external_payouts_enabled: bool
    pilot_payment_approval_required: bool
    apk_distribution: str


@dataclass(frozen=True)
class PilotRegistry:
    pilot_id: str
    status: str
    approved_participants_only: bool
    roles_overlap_allowed: bool
    approved_users_only: bool
    approved_devices_only: bool
    approved_operators_only: bool
    approved_users: tuple[str, ...]
    approved_riders: tuple[str, ...]
    approved_devices: tuple[str, ...]
    approved_drivers: tuple[str, ...]
    approved_operators: tuple[str, ...]
    approved_agents: tuple[str, ...]
    approved_merchants: tuple[str, ...]
    approved_businesses: tuple[str, ...]
    approved_employees: tuple[str, ...]
    approved_test_locations: tuple[str, ...]
    payment_mode: str
    real_payments_approved: bool
    public_launch_allowed: bool


_AUDIT_LOG: list[dict[str, Any]] = []
_DEVICE_BINDINGS: dict[str, str] = {}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def load_controlled_pilot_config() -> ControlledPilotConfig:
    payload = json.loads((_repo_root() / "config" / "controlled_pilot.json").read_text(encoding="utf-8"))
    return ControlledPilotConfig(
        environment=str(payload["environment"]),
        pilot_enabled=bool(payload["pilot_enabled"]),
        public_launch_allowed=bool(payload["public_launch_allowed"]),
        general_availability_allowed=bool(payload["general_availability_allowed"]),
        unrestricted_signup_allowed=bool(payload["unrestricted_signup_allowed"]),
        approved_users_only=bool(payload["approved_users_only"]),
        approved_devices_only=bool(payload["approved_devices_only"]),
        approved_operators_only=bool(payload["approved_operators_only"]),
        payment_mode=str(payload["payment_mode"]),
        live_payments_enabled=bool(payload["live_payments_enabled"]),
        real_charging_enabled=bool(payload["real_charging_enabled"]),
        external_payouts_enabled=bool(payload["external_payouts_enabled"]),
        pilot_payment_approval_required=bool(payload["pilot_payment_approval_required"]),
        apk_distribution=str(payload["apk_distribution"]),
    )


@lru_cache(maxsize=1)
def load_pilot_registry() -> PilotRegistry:
    payload = json.loads((_repo_root() / "docs" / "pilot" / "approved_pilot_registry.json").read_text(encoding="utf-8"))
    return PilotRegistry(
        pilot_id=str(payload["pilot_id"]),
        status=str(payload["status"]),
        approved_participants_only=bool(payload["approved_participants_only"]),
        roles_overlap_allowed=bool(payload["roles_overlap_allowed"]),
        approved_users_only=bool(payload["approved_users_only"]),
        approved_devices_only=bool(payload["approved_devices_only"]),
        approved_operators_only=bool(payload["approved_operators_only"]),
        approved_users=tuple(payload.get("approved_users", [])),
        approved_riders=tuple(payload.get("approved_riders", [])),
        approved_devices=tuple(payload.get("approved_devices", [])),
        approved_drivers=tuple(payload.get("approved_drivers", [])),
        approved_operators=tuple(payload.get("approved_operators", [])),
        approved_agents=tuple(payload.get("approved_agents", [])),
        approved_merchants=tuple(payload.get("approved_merchants", [])),
        approved_businesses=tuple(payload.get("approved_businesses", [])),
        approved_employees=tuple(payload.get("approved_employees", [])),
        approved_test_locations=tuple(payload.get("approved_test_locations", [])),
        payment_mode=str(payload["payment_mode"]),
        real_payments_approved=bool(payload["real_payments_approved"]),
        public_launch_allowed=bool(payload["public_launch_allowed"]),
    )


def pilot_payment_approval() -> dict[str, Any] | None:
    path = _repo_root() / "docs" / "pilot" / "PILOT_PAYMENT_APPROVAL.json"
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {"real_payments_approved", "approval_id", "approved_by", "approved_at", "scope", "max_transaction_amount", "max_daily_volume", "approved_payment_provider", "rollback_plan"}
    if not required.issubset(payload):
        raise ControlledPilotError("invalid_pilot_payment_approval_file")
    if payload.get("scope") != "CONTROLLED_PILOT_ONLY":
        raise ControlledPilotError("invalid_pilot_payment_scope")
    if not bool(payload.get("real_payments_approved")):
        raise ControlledPilotError("pilot_payment_approval_not_granted")
    return payload


def ensure_controlled_pilot_mode() -> ControlledPilotConfig:
    config = load_controlled_pilot_config()
    if config.environment != "CONTROLLED_PILOT" or not config.pilot_enabled:
        raise ControlledPilotError("controlled_pilot_required")
    return config


def _subject_allowed(claims: AuthClaims, surface: str) -> bool:
    registry = load_pilot_registry()
    user_allowed = _subject_registered(claims.sub)
    device_allowed = _device_allowed(claims.sub)
    if not user_allowed or not device_allowed:
        return False
    surface = surface.lower()
    role = claims.role.upper()
    if surface in {"rider", "consumer", "personal"}:
        return role == "CUSTOMER" or claims.sub in registry.approved_users
    if surface == "driver":
        return role == "DRIVER" and claims.sub in registry.approved_drivers
    if surface == "operator":
        return role in {"OPERATOR", "FLEET_OWNER"} and claims.sub in registry.approved_operators
    if surface == "agent":
        return role in {"DISPATCHER", "OPERATOR"} and claims.sub in registry.approved_agents
    if surface == "merchant":
        return role in {"CLIENT", "SUPPLIER"} and claims.sub in registry.approved_merchants
    if surface == "business":
        return role in {"CLIENT", "FLEET_OWNER"} and claims.sub in registry.approved_businesses
    if surface == "identity":
        return role in {"VERIFIER", "PARTNER", "ADMIN", "OBSERVER"}
    return False


def _subject_registered(subject: str) -> bool:
    registry = load_pilot_registry()
    approved_groups = (
        registry.approved_users,
        registry.approved_riders,
        registry.approved_drivers,
        registry.approved_operators,
        registry.approved_agents,
        registry.approved_merchants,
        registry.approved_businesses,
        registry.approved_employees,
    )
    return any(subject in group for group in approved_groups)


def _device_allowed(subject: str) -> bool:
    registry = load_pilot_registry()
    bound = _DEVICE_BINDINGS.get(subject)
    return bound in registry.approved_devices


def record_event(*, actor: str, role: str, device: str, action: str, result: str, environment: str | None = None) -> None:
    config = ensure_controlled_pilot_mode()
    _AUDIT_LOG.append(
        {
            "timestamp": datetime.now(UTC).isoformat(),
            "actor": actor,
            "role": role,
            "device": device,
            "action": action,
            "result": result,
            "environment": environment or config.environment,
        }
    )


def audit_log() -> list[dict[str, Any]]:
    return list(_AUDIT_LOG)


def bind_device(subject: str, device_id: str) -> dict[str, Any]:
    config = ensure_controlled_pilot_mode()
    registry = load_pilot_registry()
    if (
        subject not in registry.approved_users
        and subject not in registry.approved_riders
        and subject not in registry.approved_drivers
        and subject not in registry.approved_operators
        and subject not in registry.approved_agents
        and subject not in registry.approved_merchants
        and subject not in registry.approved_businesses
        and subject not in registry.approved_employees
    ):
        raise ControlledPilotError("subject_not_approved")
    if device_id not in registry.approved_devices:
        raise ControlledPilotError("device_not_approved")
    _DEVICE_BINDINGS[subject] = device_id
    record_event(actor=subject, role="DEVICE", device=device_id, action="bind_device", result="bound", environment=config.environment)
    return {"status": "bound", "subject": subject, "device_id": device_id, "environment": config.environment}


def revoke_device(device_id: str) -> dict[str, Any]:
    config = ensure_controlled_pilot_mode()
    revoked = False
    for subject, bound_device in list(_DEVICE_BINDINGS.items()):
        if bound_device == device_id:
            del _DEVICE_BINDINGS[subject]
            revoked = True
            record_event(actor=subject, role="DEVICE", device=device_id, action="revoke_device", result="revoked", environment=config.environment)
    return {"status": "revoked" if revoked else "not_found", "device_id": device_id, "revoked": revoked, "environment": config.environment}


def check_access(claims: AuthClaims, device_id: str, surface: str) -> dict[str, Any]:
    config = ensure_controlled_pilot_mode()
    registry = load_pilot_registry()
    if config.public_launch_allowed or config.general_availability_allowed or config.unrestricted_signup_allowed:
        raise ControlledPilotError("pilot_release_guard_failed")
    if (
        claims.sub not in registry.approved_users
        and claims.sub not in registry.approved_riders
        and claims.sub not in registry.approved_drivers
        and claims.sub not in registry.approved_operators
        and claims.sub not in registry.approved_agents
        and claims.sub not in registry.approved_merchants
        and claims.sub not in registry.approved_businesses
        and claims.sub not in registry.approved_employees
    ):
        result = {"allowed": False, "reason": "user_not_approved"}
    elif device_id not in registry.approved_devices or _DEVICE_BINDINGS.get(claims.sub) != device_id:
        result = {"allowed": False, "reason": "device_not_approved"}
    elif not _subject_allowed(claims, surface):
        result = {"allowed": False, "reason": "role_not_authorized"}
    else:
        result = {"allowed": True, "reason": "approved"}
    record_event(actor=claims.sub, role=claims.role, device=device_id, action=f"access_check:{surface}", result=str(result["reason"]), environment=config.environment)
    return {
        "environment": config.environment,
        "pilot_id": registry.pilot_id,
        "surface": surface,
        "user_id": claims.sub,
        "role": claims.role,
        "device_id": device_id,
        **result,
    }


def controlled_pilot_payment_allowed() -> bool:
    approval = pilot_payment_approval()
    return bool(approval and approval.get("real_payments_approved"))


def controlled_pilot_payment_guard(*, provider: str, method: str, real_payment: bool = False, payout: bool = False, production_credentials_present: bool = False) -> None:
    config = ensure_controlled_pilot_mode()
    if config.live_payments_enabled or config.real_charging_enabled or config.external_payouts_enabled:
        raise ControlledPilotError("live_payment_disabled_in_controlled_pilot")
    if production_credentials_present:
        raise ControlledPilotError("production_credentials_rejected")
    if provider.startswith("live_"):
        raise ControlledPilotError("live_provider_rejected")
    if payout or real_payment:
        if not controlled_pilot_payment_allowed():
            raise ControlledPilotError("controlled_pilot_real_payments_blocked")
    if method not in {"card", "wallet", "cash", "regional", "split"}:
        raise ControlledPilotError("unsupported_controlled_pilot_payment_method")


def mark_controlled_pilot_payment(payload: dict[str, Any]) -> dict[str, Any]:
    config = ensure_controlled_pilot_mode()
    return {
        **payload,
        "controlled_pilot": True,
        "simulated_payment": True,
        "payment_mode": config.payment_mode,
        "controlled_pilot_environment": asdict(config),
    }


def build_controlled_pilot_router() -> APIRouter:
    router = APIRouter(prefix="/v1/pilot", tags=["controlled-pilot"])

    @router.get("/registry")
    def registry(authorization: str | None = Header(default=None, alias="Authorization")) -> dict[str, Any]:
        claims = _require_token(authorization)
        config = ensure_controlled_pilot_mode()
        record_event(actor=claims.sub, role=claims.role, device=_device_for_subject(claims.sub), action="registry", result="ok", environment=config.environment)
        return {"config": asdict(config), "registry": asdict(load_pilot_registry()), "audit_count": len(_AUDIT_LOG)}

    @router.post("/access/check")
    def access_check(payload: dict[str, Any], authorization: str | None = Header(default=None, alias="Authorization")) -> dict[str, Any]:
        claims = _require_token(authorization)
        device_id = str(payload.get("device_id", "")).strip()
        surface = str(payload.get("surface", payload.get("role", ""))).strip() or "consumer"
        if not device_id:
            raise HTTPException(status_code=400, detail="device_id required")
        return check_access(claims, device_id, surface)

    @router.post("/devices/bind")
    def device_bind(payload: dict[str, Any], authorization: str | None = Header(default=None, alias="Authorization")) -> dict[str, Any]:
        claims = _require_token(authorization)
        device_id = str(payload.get("device_id", "")).strip()
        if not device_id:
            raise HTTPException(status_code=400, detail="device_id required")
        try:
            return bind_device(claims.sub, device_id)
        except ControlledPilotError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @router.post("/devices/revoke")
    def device_revoke(payload: dict[str, Any], authorization: str | None = Header(default=None, alias="Authorization")) -> dict[str, Any]:
        _require_token(authorization)
        device_id = str(payload.get("device_id", "")).strip()
        if not device_id:
            raise HTTPException(status_code=400, detail="device_id required")
        return revoke_device(device_id)

    @router.post("/support/tickets")
    def support_tickets(payload: dict[str, Any], authorization: str | None = Header(default=None, alias="Authorization")) -> dict[str, Any]:
        claims = _require_token(authorization)
        ticket_id = f"cp-ticket-{hashlib.sha256(f'{claims.sub}:{payload}'.encode()).hexdigest()[:12]}"
        record_event(actor=claims.sub, role=claims.role, device=_device_for_subject(claims.sub), action="support_ticket", result="created")
        return {"status": "created", "ticket_id": ticket_id, "environment": "CONTROLLED_PILOT"}

    @router.post("/safety/sos")
    def sos(payload: dict[str, Any], authorization: str | None = Header(default=None, alias="Authorization")) -> dict[str, Any]:
        claims = _require_token(authorization)
        record_event(actor=claims.sub, role=claims.role, device=_device_for_subject(claims.sub), action="sos", result="created")
        return {"status": "incident_created", "incident": {"type": "pilot_sos", "payload": payload, "environment": "CONTROLLED_PILOT"}}

    @router.get("/audit")
    def audit(authorization: str | None = Header(default=None, alias="Authorization")) -> dict[str, Any]:
        claims = _require_token(authorization)
        return {"environment": "CONTROLLED_PILOT", "items": audit_log(), "requested_by": claims.sub}

    return router


def _require_token(authorization: str | None) -> AuthClaims:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="bearer token required")
    try:
        return JWT.verify_token(authorization[len("Bearer ") :])
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def _device_for_subject(subject: str) -> str:
    return _DEVICE_BINDINGS.get(subject, "unbound")
