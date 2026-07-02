"""Governed NovaRide App Store contract."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

NOVARIDE_APP_STORE_VERSION = "2026.07.0"

NOVARIDE_APP_STORE_CATEGORIES: tuple[dict[str, Any], ...] = (
    {
        "key": "mobility",
        "name": "Mobility",
        "examples": ("ride apps", "taxi services", "dispatch extensions"),
    },
    {
        "key": "logistics",
        "name": "Logistics",
        "examples": ("delivery", "courier", "fleet routing"),
    },
    {
        "key": "business",
        "name": "Business",
        "examples": ("fleet management", "staff transport", "expense workflows"),
    },
    {
        "key": "travel",
        "name": "Travel",
        "examples": ("airport transfers", "guest transport", "hotel partnerships"),
    },
    {
        "key": "ai_tools",
        "name": "AI Tools",
        "examples": ("pricing", "forecasting", "fraud detection"),
    },
    {
        "key": "finance",
        "name": "Finance",
        "examples": ("payments", "microcredit", "wallet tooling"),
    },
)

NOVARIDE_APP_STORE_APPS: tuple[dict[str, Any], ...] = (
    {
        "app_id": "quickdelivery",
        "name": "QuickDelivery",
        "developer": "LogiTech",
        "category": "logistics",
        "version": "1.0.0",
        "pricing": "subscription",
        "token_integration": True,
        "permissions": ("rides", "payments", "tracking"),
        "status": "verified",
        "summary": "Delivery orchestration built on NovaRide routing and proof rails.",
    },
    {
        "app_id": "ridesharepro",
        "name": "RideShare Pro",
        "developer": "MobilityWorks",
        "category": "mobility",
        "version": "2.3.1",
        "pricing": "transaction_fee",
        "token_integration": True,
        "permissions": ("rides", "driver_queue", "replay"),
        "status": "verified",
        "summary": "Marketplace rides and shared-trip orchestration for city operators.",
    },
    {
        "app_id": "fleetpulse",
        "name": "Fleet Pulse",
        "developer": "FleetOne",
        "category": "business",
        "version": "1.8.0",
        "pricing": "subscription",
        "token_integration": False,
        "permissions": ("fleet", "analytics", "reports"),
        "status": "sandbox_ready",
        "summary": "Fleet utilization, maintenance, and staff transport dashboards.",
    },
    {
        "app_id": "airportconnect",
        "name": "Airport Connect",
        "developer": "TravelGrid",
        "category": "travel",
        "version": "1.4.2",
        "pricing": "one_time",
        "token_integration": True,
        "permissions": ("rides", "booking", "notifications"),
        "status": "verified",
        "summary": "Airport pickup and guest transport workflows for venues and travel teams.",
    },
    {
        "app_id": "novaforecast",
        "name": "Nova Forecast",
        "developer": "NovaAI Labs",
        "category": "ai_tools",
        "version": "0.9.5",
        "pricing": "api_usage",
        "token_integration": True,
        "permissions": ("analytics", "pricing", "forecasting"),
        "status": "governed",
        "summary": "Demand, pricing, and supply prediction utility for protocol consumers.",
    },
    {
        "app_id": "novawallet-plus",
        "name": "NovaWallet Plus",
        "developer": "FinPort",
        "category": "finance",
        "version": "3.0.0",
        "pricing": "subscription",
        "token_integration": True,
        "permissions": ("payments", "wallet", "rewards"),
        "status": "verified",
        "summary": "Wallet, rewards, and payment tooling for NovaRide ecosystem users.",
    },
)

NOVARIDE_APP_STORE_PUBLISHING_PIPELINE: tuple[dict[str, Any], ...] = (
    {
        "step": "submit",
        "title": "Submit Manifest",
        "goal": "Receive app metadata, permissions, pricing, and version information.",
    },
    {
        "step": "scan",
        "title": "Security Scan",
        "goal": "Check app code, permissions, and declared integrations for policy violations.",
    },
    {
        "step": "contract",
        "title": "Contract Validation",
        "goal": "Verify supported API shapes, replay requirements, and compatibility bindings.",
    },
    {
        "step": "sandbox",
        "title": "Sandbox Execution",
        "goal": "Run the app against a bounded sandbox before any public listing.",
    },
    {
        "step": "publish",
        "title": "Publish Listing",
        "goal": "Expose the app in the governed store catalog.",
    },
)


def _normalize_manifest(manifest: Mapping[str, Any] | None) -> dict[str, Any]:
    if not manifest:
        return {}
    return {str(key): value for key, value in manifest.items()}


def novaride_app_store() -> dict[str, Any]:
    """Return the governed NovaRide App Store contract."""

    return {
        "platform": "NovaRide",
        "version": NOVARIDE_APP_STORE_VERSION,
        "classification": "governed_app_store_catalog",
        "status": "governed_beta",
        "categories": deepcopy(list(NOVARIDE_APP_STORE_CATEGORIES)),
        "apps": deepcopy(list(NOVARIDE_APP_STORE_APPS)),
        "publishing_pipeline": deepcopy(list(NOVARIDE_APP_STORE_PUBLISHING_PIPELINE)),
        "developer_flow": (
            "sign_up",
            "get_api_key",
            "build_app",
            "test_in_sandbox",
            "publish_to_app_store",
            "earn_revenue",
        ),
        "governance": {
            "authority": "NovaPower",
            "verification": "NovaTrust",
            "execution": "backend_only",
            "policy_gates": (
                "authentication",
                "rbac",
                "security_scan",
                "contract_validation",
                "sandbox_test",
                "policy_approval",
            ),
        },
        "monetization": {
            "revenue_streams": ("app_sales", "subscriptions", "transaction_fee", "api_usage", "token_economy"),
            "revenue_split": {"developer": "70%", "platform": "30%"},
            "token_payment": "NVT_supported",
        },
        "metrics": {
            "app_count": len(NOVARIDE_APP_STORE_APPS),
            "developer_count": 0,
            "city_count": 0,
            "new_apps_per_week": 0,
            "user_installs_growth": "0%",
        },
    }


def novaride_app_store_install_plan(manifest: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return a governed install plan for a manifest submission."""

    payload = _normalize_manifest(manifest)
    name = str(payload.get("name", "Unknown App"))
    permissions = list(payload.get("permissions", [])) if isinstance(payload.get("permissions"), list) else []
    return {
        "platform": "NovaRide",
        "view": "novaride_app_install_plan",
        "status": "policy_gated",
        "manifest": payload,
        "app": {
            "name": name,
            "version": str(payload.get("version", "0.0.0")),
            "developer": str(payload.get("developer", "unknown")),
            "permissions": permissions,
            "pricing": str(payload.get("pricing", "unknown")),
            "token_integration": bool(payload.get("token_integration", False)),
        },
        "validation": {
            "security_scan": "required",
            "contract_validation": "required",
            "sandbox_execution": "required",
            "policy_approval": "required",
        },
        "install_actions": (
            "register_listing",
            "provision_sandbox",
            "bind_permissions",
            "enable_usage_metering",
            "record_install_receipt",
        ),
    }


def novaride_app_store_publish_plan(manifest: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return a governed publish plan for a manifest submission."""

    payload = _normalize_manifest(manifest)
    return {
        "platform": "NovaRide",
        "view": "novaride_app_publish_plan",
        "status": "policy_gated",
        "manifest": payload,
        "publish_channels": ("app_store", "developer_marketplace"),
        "review_pipeline": deepcopy(list(NOVARIDE_APP_STORE_PUBLISHING_PIPELINE)),
        "approval_model": {
            "ai_security_scan": "required",
            "compliance_validation": "required",
            "dao_approval": "optional",
            "nova_power_approval": "required",
        },
        "monetization": {
            "developer_share": "70%",
            "platform_share": "30%",
            "token_payment": bool(payload.get("token_integration", False)),
        },
    }

