"""Phase 0 SaaS foundation guards."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from afritech.guards.guard_core import GuardResult


PHASE0_REQUIRED_TABLES: tuple[str, ...] = (
    "organizations",
    "organization_profiles",
    "accounts",
    "subscriptions",
    "catalog_features",
    "feature_flags",
    "audit_events",
    "notifications",
    "integrations",
)

PHASE0_REQUIRED_CONTROLS: tuple[str, ...] = (
    "multi_tenant_registry",
    "subscription_entitlements",
    "feature_catalog",
    "feature_flags",
    "audit_logging",
    "notification_outbox",
    "integration_registry",
    "backend_only_provider_access",
)


def validate_phase0_status(payload: Mapping[str, Any]) -> GuardResult:
    if not isinstance(payload, Mapping):
        return GuardResult(False, "PHASE0_STATUS_INVALID")

    if payload.get("platform") != "NovaRide Phase 0":
        return GuardResult(False, "PHASE0_PLATFORM_MISMATCH")

    if payload.get("read_only") is not True:
        return GuardResult(False, "PHASE0_READ_ONLY_REQUIRED")

    if payload.get("creates_authority") is not False:
        return GuardResult(False, "PHASE0_AUTHORITY_BOUNDARY_BROKEN")

    tables = payload.get("required_tables", ())
    if not isinstance(tables, (list, tuple)):
        return GuardResult(False, "PHASE0_REQUIRED_TABLES_INVALID")
    missing_tables = [table for table in PHASE0_REQUIRED_TABLES if table not in tables]
    if missing_tables:
        return GuardResult(False, "PHASE0_REQUIRED_TABLES_MISSING")

    controls = payload.get("required_controls", ())
    if not isinstance(controls, (list, tuple)):
        return GuardResult(False, "PHASE0_REQUIRED_CONTROLS_INVALID")
    missing_controls = [control for control in PHASE0_REQUIRED_CONTROLS if control not in controls]
    if missing_controls:
        return GuardResult(False, "PHASE0_REQUIRED_CONTROLS_MISSING")

    readiness = payload.get("readiness", {})
    if not isinstance(readiness, Mapping):
        return GuardResult(False, "PHASE0_READINESS_INVALID")
    if not all(bool(readiness.get(control, False)) for control in PHASE0_REQUIRED_CONTROLS):
        return GuardResult(False, "PHASE0_READINESS_INCOMPLETE")

    if payload.get("ready") is not True:
        return GuardResult(False, "PHASE0_READY_FLAG_FALSE")

    return GuardResult(True)


__all__ = [
    "PHASE0_REQUIRED_CONTROLS",
    "PHASE0_REQUIRED_TABLES",
    "validate_phase0_status",
]
