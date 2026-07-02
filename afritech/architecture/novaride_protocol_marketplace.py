"""Governed NovaRide protocol marketplace contract."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

NOVARIDE_PROTOCOL_MARKETPLACE_VERSION = "2026.07.0"

NOVARIDE_PROTOCOL_MARKETPLACE_STOREFRONTS: tuple[dict[str, Any], ...] = (
    {
        "key": "app_store",
        "name": "NovaRide App Store",
        "audience": "customers, drivers, operators, partners",
        "status": "catalog_ready",
        "purpose": "Publish governed NovaRide experiences and partner-built apps.",
        "listing_types": ("first_party_app", "partner_app", "trusted_integration"),
    },
    {
        "key": "developer_marketplace",
        "name": "NovaRide Developer Marketplace",
        "audience": "developers, integrators, startups",
        "status": "sandbox_ready",
        "purpose": "Publish SDKs, webhooks, sample apps, and integration packages.",
        "listing_types": ("sdk", "webhook", "sample_app", "integration"),
    },
    {
        "key": "trust_marketplace",
        "name": "NovaRide Trust Marketplace",
        "audience": "auditors, regulators, enterprise verifiers",
        "status": "governed",
        "purpose": "Publish verification, replay, and proof surfaces.",
        "listing_types": ("verification_surface", "replay_view", "audit_export"),
    },
    {
        "key": "partner_marketplace",
        "name": "NovaRide Partner Marketplace",
        "audience": "fleet owners, businesses, venues, logistics partners",
        "status": "partner_ready",
        "purpose": "Publish partner-facing portals and controlled integrations.",
        "listing_types": ("partner_portal", "b2b_widget", "bulk_integration"),
    },
)

NOVARIDE_PROTOCOL_MARKETPLACE_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "listing_id": "novaride-passenger",
        "name": "NovaRide Passenger / Rider App",
        "surface_type": "application",
        "role": "CUSTOMER",
        "platforms": ("Android", "iOS", "Web"),
        "status": "first_party",
        "publish_channel": "app_store",
        "purpose": "Ride booking, trip tracking, receipts, support, and replay verification.",
    },
    {
        "listing_id": "novaride-driver",
        "name": "NovaRide Driver",
        "surface_type": "application",
        "role": "DRIVER",
        "platforms": ("Android", "iOS"),
        "status": "first_party",
        "publish_channel": "app_store",
        "purpose": "Ride queue, navigation, earnings, safety, and inspection evidence.",
    },
    {
        "listing_id": "novaride-developer",
        "name": "NovaRide Developer Portal",
        "surface_type": "portal",
        "role": "DEVELOPER",
        "platforms": ("Web",),
        "status": "first_party",
        "publish_channel": "developer_marketplace",
        "purpose": "API keys, sandbox, webhooks, docs, SDK downloads, and usage analytics.",
    },
    {
        "listing_id": "novaride-partner",
        "name": "NovaRide Partner Portal",
        "surface_type": "portal",
        "role": "PARTNER",
        "platforms": ("Web",),
        "status": "first_party",
        "publish_channel": "partner_marketplace",
        "purpose": "Fleet, venue, travel, and logistics integrations.",
    },
    {
        "listing_id": "novaride-trust",
        "name": "NovaRide Trust Portal",
        "surface_type": "portal",
        "role": "OPERATOR",
        "platforms": ("Web",),
        "status": "governed",
        "publish_channel": "trust_marketplace",
        "purpose": "Public verification, replay evidence, and audit exports.",
    },
    {
        "listing_id": "novaride-sdk-registry",
        "name": "NovaRide SDK Registry",
        "surface_type": "package_registry",
        "role": "DEVELOPER",
        "platforms": ("Python", "TypeScript", "Kotlin", "Swift", "Go"),
        "status": "catalog_ready",
        "publish_channel": "developer_marketplace",
        "purpose": "Generated clients and contract bindings for published protocol surfaces.",
    },
    {
        "listing_id": "novaride-ai-services",
        "name": "NovaRide AI Services",
        "surface_type": "service_catalog",
        "role": "DEVELOPER",
        "platforms": ("API",),
        "status": "governed",
        "publish_channel": "developer_marketplace",
        "purpose": "Demand forecast, pricing recommendations, and fraud detection surfaces.",
    },
)

NOVARIDE_PROTOCOL_MARKETPLACE_PUBLISHING_PIPELINE: tuple[dict[str, Any], ...] = (
    {
        "step": "submit",
        "title": "Submit Listing",
        "goal": "Capture app, SDK, or integration metadata in the developer portal.",
    },
    {
        "step": "sandbox",
        "title": "Sandbox Validation",
        "goal": "Exercise the listing in an isolated tenant and controlled replay environment.",
    },
    {
        "step": "trust_review",
        "title": "Trust and Security Review",
        "goal": "Verify signatures, replay coverage, and authority boundaries.",
    },
    {
        "step": "compatibility_review",
        "title": "Compatibility Review",
        "goal": "Confirm OpenAPI and contract compatibility with supported protocol versions.",
    },
    {
        "step": "publish",
        "title": "Publish Listing",
        "goal": "Expose the listing through the governed app store and protocol marketplace.",
    },
)


def novaride_protocol_marketplace() -> dict[str, Any]:
    """Return the governed NovaRide protocol marketplace contract."""

    return {
        "platform": "NovaRide",
        "protocol_version": NOVARIDE_PROTOCOL_MARKETPLACE_VERSION,
        "classification": "governed_protocol_marketplace_catalog",
        "status": "governed_beta",
        "storefronts": deepcopy(list(NOVARIDE_PROTOCOL_MARKETPLACE_STOREFRONTS)),
        "catalog": deepcopy(list(NOVARIDE_PROTOCOL_MARKETPLACE_CATALOG)),
        "publishing_pipeline": deepcopy(list(NOVARIDE_PROTOCOL_MARKETPLACE_PUBLISHING_PIPELINE)),
        "developer_program": {
            "api_keys": True,
            "sandbox": "required",
            "webhooks": True,
            "documentation": True,
            "sdk_registry": True,
            "trust_review": "required",
            "compatibility_review": "required",
            "usage_analytics": True,
        },
        "governance": {
            "authority": "NovaPower",
            "verification": "NovaTrust",
            "execution": "backend_only",
            "policy_gates": (
                "authentication",
                "rbac",
                "signature_verification",
                "replay_validation",
                "compatibility_check",
            ),
        },
        "economics": {
            "revenue_share_model": "policy_gated",
            "listing_fee": "optional",
            "developer_rewards": "usage_based",
            "treasury_split": ("developer", "platform", "reserve"),
        },
        "metrics": {
            "storefront_count": len(NOVARIDE_PROTOCOL_MARKETPLACE_STOREFRONTS),
            "catalog_count": len(NOVARIDE_PROTOCOL_MARKETPLACE_CATALOG),
            "publishing_step_count": len(NOVARIDE_PROTOCOL_MARKETPLACE_PUBLISHING_PIPELINE),
        },
    }

