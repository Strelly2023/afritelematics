"""NovaRide next-generation universal mobility platform contract.

This module keeps the Rider, Driver, Operator, backend, and frontend target
architecture in one deterministic manifest so API routes, documentation, and
tests can depend on the same source of truth.
"""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from typing import Any


NOVARIDE_NEXT_GENERATION_VERSION = "2026.07.next-generation"
NOVARIDE_NEXT_GENERATION_STATUS = "runtime_capabilities_complete_release_candidate"

GLOBAL_MARKETS: tuple[str, ...] = (
    "Africa",
    "Australia",
    "USA",
    "Canada",
    "Europe",
    "United Kingdom",
    "India",
    "Middle East",
    "Asia-Pacific",
    "Global",
)

MOBILE_MONEY_METHODS: tuple[str, ...] = (
    "M-Pesa",
    "MTN Mobile Money",
    "Airtel Money",
    "Orange Money",
    "EcoCash",
    "Vodacom M-Pesa",
    "Onafriq corridors",
)

GLOBAL_PAYMENT_METHODS: tuple[str, ...] = (
    "Credit card",
    "Debit card",
    "Visa",
    "Mastercard",
    "American Express",
    "Apple Pay",
    "Google Pay",
    "Samsung Wallet",
    "Bank transfer",
    "Instant bank payments",
    "UPI",
    "QR payments",
    "Cash",
    "NovaPay Wallet",
    "Corporate billing",
)

SUPPORTED_CURRENCIES: tuple[str, ...] = (
    "USD",
    "EUR",
    "GBP",
    "AUD",
    "CAD",
    "INR",
    "KES",
    "UGX",
    "TZS",
    "ZAR",
    "RWF",
    "BWP",
    "NAD",
    "ZMW",
    "GHS",
    "XOF",
    "EGP",
    "MAD",
    "NGN",
    "CDF",
    "BIF",
)

SUPPORTED_LANGUAGES: tuple[str, ...] = (
    "English",
    "French",
    "Swahili",
    "isiZulu",
    "Afrikaans",
    "Setswana",
    "Sesotho",
    "Xhosa",
    "Tsonga",
    "Lingala",
    "Arabic",
    "Portuguese",
    "Amharic",
    "Hindi",
    "Bengali",
    "Punjabi",
    "Tamil",
    "Spanish",
    "German",
    "Italian",
    "Dutch",
    "Turkish",
    "Chinese",
    "Japanese",
    "Korean",
)

DRIVER_MODULES: tuple[str, ...] = (
    "NovaID Identity",
    "Driver Workspace",
    "Ride Operations",
    "Navigation",
    "Payments",
    "Wallet",
    "Fleet",
    "Delivery",
    "Business",
    "Safety",
    "Emergency",
    "AI Copilot",
    "Compliance",
    "Offline Engine",
    "Vehicle Hub",
    "Rewards",
    "Support",
    "Analytics",
    "Marketplace",
    "Diagnostics",
    "Accessibility",
    "Settings",
)

DRIVER_SERVICES: tuple[dict[str, Any], ...] = (
    {
        "category": "Ride Hailing",
        "services": ("Economy", "Premium", "XL", "Taxi", "Luxury", "Accessible rides", "Airport transfers"),
    },
    {
        "category": "African Transport",
        "services": ("Boda Boda", "Tuk Tuk", "Minibus", "Shared taxi"),
    },
    {
        "category": "Delivery",
        "services": ("Food", "Grocery", "Pharmacy", "Courier", "Retail", "Documents"),
    },
    {
        "category": "Logistics",
        "services": ("Vans", "Trucks", "Fleet", "Business deliveries"),
    },
)

DRIVER_API_SURFACE: tuple[str, ...] = (
    "POST /v1/drivers/onboarding",
    "GET /v1/drivers/me",
    "GET /v1/drivers/me/eligibility",
    "POST /v1/driver/shifts/start",
    "POST /v1/driver/shifts/pause",
    "POST /v1/driver/shifts/resume",
    "POST /v1/driver/shifts/end",
    "GET /v1/driver/{driver_id}/availability",
    "PUT /v1/driver/{driver_id}/availability",
    "GET /v1/driver/{driver_id}/ride-queue",
    "GET /v1/driver/offers/{offer_id}",
    "POST /v1/driver/offers/{offer_id}/accept",
    "POST /v1/driver/offers/{offer_id}/decline",
    "POST /v1/driver/offers/{offer_id}/bid",
    "POST /v1/driver/trips/{trip_id}/arrive",
    "POST /v1/driver/trips/{trip_id}/verify-passenger",
    "POST /v1/driver/trips/{trip_id}/start",
    "POST /v1/driver/trips/{trip_id}/location",
    "POST /v1/driver/trips/{trip_id}/complete",
    "POST /v1/driver/emergency",
    "POST /v1/driver/incidents",
    "POST /v1/driver/offline/sync",
    "GET /v1/driver/earnings",
    "GET /v1/driver/diagnostics",
)

RIDER_NAVIGATION: tuple[str, ...] = ("Home", "Trips", "Wallet", "Safety", "Account")
RIDER_SECONDARY_SERVICES: tuple[str, ...] = (
    "Delivery",
    "Business",
    "Family",
    "Subscriptions",
    "Rewards",
    "Support",
    "Accessibility",
)

RIDER_SERVICES: tuple[dict[str, Any], ...] = (
    {
        "category": "Ride-Hailing",
        "services": (
            "Economy",
            "Standard",
            "Premium",
            "Luxury",
            "XL",
            "Taxi",
            "Shared ride",
            "Women-preferred ride where lawful",
            "Senior ride",
            "Accessible ride",
            "Medical transport",
            "Airport transfer",
            "Long-distance ride",
            "Corporate ride",
        ),
    },
    {
        "category": "African Mobility",
        "services": (
            "Boda Boda",
            "Motorcycle taxi",
            "Tuk-tuk",
            "Minibus",
            "Shared taxi",
            "Community shuttle",
            "Rural transport",
            "Intercity mobility",
        ),
    },
    {
        "category": "Delivery",
        "services": ("Food", "Grocery", "Pharmacy", "Parcel", "Documents", "Retail goods", "Business delivery"),
    },
    {
        "category": "Public and Multi-Modal Transport",
        "services": ("Bus", "Train", "Metro", "Ferry", "Tram", "Bicycle", "Scooter", "Park-and-ride", "Walking connections"),
    },
)

RIDER_API_SURFACE: tuple[str, ...] = (
    "POST /v1/riders/onboarding",
    "GET /v1/riders/me",
    "PATCH /v1/riders/me",
    "POST /v1/rider/journeys/search",
    "POST /v1/rider/fares/quote",
    "POST /v1/rider/bookings",
    "GET /v1/rider/bookings/{booking_id}",
    "POST /v1/rider/bookings/{booking_id}/cancel",
    "GET /v1/rider/trips/{trip_id}",
    "GET /v1/rider/trips/{trip_id}/tracking",
    "POST /v1/rider/trips/{trip_id}/share",
    "POST /v1/rider/trips/{trip_id}/emergency",
    "POST /v1/rider/trips/{trip_id}/rate",
    "GET /v1/rider/payment-methods",
    "POST /v1/rider/payment-intents",
    "GET /v1/rider/receipts/{trip_id}",
    "POST /v1/rider/support/cases",
    "GET /v1/rider/support/cases/{case_id}",
)

OPERATOR_NAVIGATION: tuple[str, ...] = (
    "Command Center",
    "Live Map",
    "Trips",
    "Drivers",
    "Riders",
    "Dispatch",
    "Safety",
    "Incidents",
    "Support",
    "Payments",
    "Fleets",
    "Vehicles",
    "Regions",
    "Compliance",
    "Fraud",
    "Observability",
    "Evidence",
    "Reports",
    "Administration",
)

OPERATOR_API_SURFACE: tuple[str, ...] = (
    "GET /v1/operator/command-center",
    "GET /v1/operator/live-map",
    "GET /v1/operator/trips",
    "GET /v1/operator/trips/{trip_id}",
    "POST /v1/operator/trips/{trip_id}/reassign",
    "POST /v1/operator/trips/{trip_id}/cancel",
    "POST /v1/operator/trips/{trip_id}/recovery-ride",
    "GET /v1/operator/drivers/{driver_id}",
    "POST /v1/operator/drivers/{driver_id}/dispatch-hold",
    "POST /v1/operator/drivers/{driver_id}/reinstate-request",
    "GET /v1/operator/riders/{rider_id}",
    "GET /v1/operator/incidents",
    "POST /v1/operator/incidents",
    "PATCH /v1/operator/incidents/{incident_id}",
    "GET /v1/operator/emergencies",
    "POST /v1/operator/emergencies/{emergency_id}/acknowledge",
    "POST /v1/operator/emergencies/{emergency_id}/escalate",
    "POST /v1/operator/emergencies/{emergency_id}/resolve",
    "GET /v1/operator/fleets",
    "GET /v1/operator/compliance/exceptions",
    "GET /v1/operator/payment-exceptions",
    "GET /v1/operator/observability",
)

CORE_BACKEND_COMPONENTS: tuple[str, ...] = (
    "Booking Engine",
    "Trip Engine",
    "Dispatch Engine",
    "Matching Engine",
    "Driver Supply Engine",
    "Pricing Engine",
    "Marketplace Engine",
    "Geography Engine",
    "Route Engine",
    "Safety Engine",
    "Fraud Engine",
    "Fleet Engine",
    "Scheduling Engine",
    "Notification Engine",
    "Policy Engine",
    "Resilience and Sync Layer",
    "Evidence Adapter",
    "Payment Adapter",
    "Identity Adapter",
    "Event Fabric",
    "Operational Read Models",
)

MOBILITY_EVENTS: tuple[str, ...] = (
    "BookingCreated",
    "FareQuoted",
    "DriverSearchStarted",
    "DriverOfferCreated",
    "DriverOfferAccepted",
    "DriverAssigned",
    "DriverArrived",
    "PickupVerified",
    "TripStarted",
    "TripLocationUpdated",
    "TripCompleted",
    "PaymentRequested",
    "PaymentConfirmed",
    "EmergencyActivated",
    "IncidentCreated",
    "OperatorInterventionRecorded",
    "TripEvidenceFinalized",
)

FRONTEND_APPS: tuple[str, ...] = (
    "novaride-rider",
    "novaride-driver",
    "novaride-operator",
    "novaride-fleet",
    "novaride-support",
    "novaride-inspector",
    "novaride-executive",
    "novaride-public-web",
)

FRONTEND_PACKAGES: tuple[str, ...] = (
    "novaride-design-system",
    "novaride-api-sdk",
    "novaride-domain-types",
    "novaride-auth",
    "novaride-maps",
    "novaride-offline",
    "novaride-safety",
    "novaride-payments-ui",
    "novaride-notifications",
    "novaride-localization",
    "novaride-accessibility",
    "novaride-observability",
    "novaride-feature-flags",
    "novaride-testkit",
)

REGIONAL_ADAPTATION: tuple[dict[str, Any], ...] = (
    {
        "region": "Africa",
        "capabilities": (
            "mobile_money",
            "cash",
            "offline_mode",
            "ussd_sms_fallback",
            "motorcycle_tuk_tuk_minibus",
            "landmark_addresses",
            "low_data_operation",
            "multi_language_support",
        ),
    },
    {
        "region": "Australia",
        "capabilities": (
            "GST_receipts",
            "accessibility_transport",
            "airport_pickup_rules",
            "state_transport_compliance",
            "card_and_digital_wallets",
            "family_and_business_profiles",
        ),
    },
    {
        "region": "USA and Canada",
        "capabilities": (
            "tipping",
            "state_province_rules",
            "ADA_accessibility",
            "airport_permits",
            "corporate_travel",
            "card_and_digital_wallets",
        ),
    },
    {
        "region": "India",
        "capabilities": (
            "UPI",
            "cash",
            "auto_rickshaw",
            "lawful_bike_taxi",
            "local_languages",
            "landmark_navigation",
            "shared_mobility",
        ),
    },
    {
        "region": "Europe and United Kingdom",
        "capabilities": (
            "GDPR_controls",
            "strong_consent",
            "VAT_receipts",
            "multi_country_travel",
            "rail_public_transport",
            "low_emission_zones",
            "local_taxi_regulation",
        ),
    },
)

OMNI_CHANNEL_BOOKING: tuple[str, ...] = (
    "mobile_app",
    "web_app",
    "call_center",
    "whatsapp",
    "ussd",
    "sms",
    "partner_portal",
    "corporate_portal",
    "agent_assisted_booking",
    "operator_assisted_booking",
)

HYBRID_PAYMENT_FLOW: tuple[str, ...] = (
    "request_ride",
    "select_available_payment_methods",
    "authorize_card_wallet_mobile_money_cash_corporate_or_split",
    "ride",
    "settlement",
    "novapay_reconciliation",
)

RESILIENCE_COMPONENTS: tuple[str, ...] = (
    "Connectivity Manager",
    "Offline Queue",
    "Sync Engine",
    "Conflict Resolver",
    "Provider Router",
    "Retry Manager",
    "Circuit Breaker",
    "Failover Controller",
    "Recovery Coordinator",
    "State Reconciler",
    "Health Monitor",
    "Evidence Recorder",
)

SERVICE_AVAILABILITY_TARGETS: tuple[dict[str, Any], ...] = (
    {"service": "Emergency/SOS", "availability": "99.999%", "rto": "5 minutes", "rpo": "near zero"},
    {"service": "Active trip tracking", "availability": "99.99%", "rto": "5 minutes", "rpo": "near zero"},
    {"service": "Ride booking", "availability": "99.95%", "rto": "15 minutes", "rpo": "under 1 minute"},
    {"service": "Driver dispatch", "availability": "99.95%", "rto": "15 minutes", "rpo": "under 1 minute"},
    {"service": "Payment orchestration", "availability": "99.95%", "rto": "30 minutes", "rpo": "near zero"},
    {"service": "Support tools", "availability": "99.9%", "rto": "1 hour", "rpo": "15 minutes"},
    {"service": "Analytics", "availability": "99.5%", "rto": "4 hours", "rpo": "1 hour"},
)

DEGRADATION_RULES: tuple[dict[str, str], ...] = (
    {"if": "live_map_unavailable", "then": "show_last_known_location_and_eta_text"},
    {"if": "card_provider_unavailable", "then": "offer_mobile_money_wallet_or_cash"},
    {"if": "push_notifications_unavailable", "then": "use_sms_or_whatsapp"},
    {"if": "ai_recommendations_unavailable", "then": "use_deterministic_dispatch_rules"},
    {"if": "analytics_unavailable", "then": "core_ride_booking_continues"},
    {"if": "knowledge_service_unavailable", "then": "cached_runbooks_remain_accessible"},
)

COUNTRY_EXPANSION_PROFILES: tuple[dict[str, Any], ...] = (
    {
        "phase": 1,
        "countries": ("Australia", "South Africa", "Kenya", "Uganda", "Tanzania"),
        "profile_fields": ("currencies", "tax_rules", "payment_providers", "emergency_numbers", "languages", "fare_regulations", "driver_licensing", "insurance_rules"),
    },
    {
        "phase": 2,
        "countries": ("Rwanda", "Zambia", "Botswana", "Namibia", "Zimbabwe"),
        "profile_fields": ("currencies", "mobile_money", "data_residency", "accessibility_rules", "regional_dispatch_rules"),
    },
    {
        "phase": 3,
        "countries": ("Nigeria", "Ghana", "Cote d'Ivoire", "Senegal", "Egypt", "Morocco"),
        "profile_fields": ("currencies", "tax_rules", "payment_providers", "emergency_numbers", "languages", "fare_regulations", "driver_licensing", "insurance_rules"),
    },
)

MATURITY_TARGETS: tuple[dict[str, Any], ...] = (
    {"domain": "Driver Experience", "target_score": 10},
    {"domain": "African Market Readiness", "target_score": 10},
    {"domain": "USA Readiness", "target_score": 10},
    {"domain": "Australia Readiness", "target_score": 10},
    {"domain": "India Readiness", "target_score": 10},
    {"domain": "Europe Readiness", "target_score": 10},
    {"domain": "Offline Capability", "target_score": 10},
    {"domain": "Safety & Emergency", "target_score": 10},
    {"domain": "Payments & Wallet", "target_score": 10},
    {"domain": "Fleet & Logistics", "target_score": 10},
    {"domain": "AI & Automation", "target_score": 10},
    {"domain": "Enterprise Governance", "target_score": 10},
    {"domain": "Scalability", "target_score": 10},
)


def _copy(value: Any) -> Any:
    return deepcopy(value)


def build_driver_platform() -> dict[str, Any]:
    return {
        "name": "NovaRide Driver",
        "positioning": "Universal Mobility Operations Platform",
        "markets": list(GLOBAL_MARKETS),
        "modules": list(DRIVER_MODULES),
        "services": _copy(DRIVER_SERVICES),
        "identity": {
            "provider": "NovaID",
            "features": (
                "passwordless_login",
                "passkeys",
                "MFA",
                "biometrics",
                "device_trust",
                "continuous_authentication",
                "national_id",
                "passport",
                "driver_licence",
                "visa_work_rights",
                "background_checks",
                "insurance_validation",
                "liveness_detection",
            ),
            "display_fields": ("Driver Verification", "Trust Score", "Identity Level", "Vehicle Status", "Risk Level"),
        },
        "operations": {
            "dashboard_widgets": (
                "online_status",
                "shift_timer",
                "heat_map",
                "peak_demand",
                "available_rides",
                "active_deliveries",
                "fleet_messages",
                "earnings",
                "wallet",
                "safety_alerts",
                "vehicle_health",
                "AI_recommendations",
            ),
            "availability_rule": "dispatchable_requires_valid_session_eligible_driver_compliant_vehicle_valid_shift_location_and_server_confirmation",
            "offline_rule": "safety_critical_operations_wait_for_authoritative_server_acknowledgement",
        },
        "safety": {
            "always_visible_panic_button": True,
            "features": (
                "silent_emergency",
                "live_location",
                "safe_pickup_zones",
                "dangerous_area_warnings",
                "rider_PIN",
                "fatigue_detection",
                "speed_monitoring",
                "emergency_evidence_lock",
            ),
        },
        "payments": {
            "owner": "NovaPay",
            "mobile_money": list(MOBILE_MONEY_METHODS),
            "global": list(GLOBAL_PAYMENT_METHODS),
            "currencies": list(SUPPORTED_CURRENCIES),
        },
        "api_surface": list(DRIVER_API_SURFACE),
    }


def build_rider_platform() -> dict[str, Any]:
    return {
        "name": "NovaRide Rider",
        "positioning": "Universal Mobility Access Platform",
        "surface_principle": "Where are you going?",
        "markets": list(GLOBAL_MARKETS),
        "primary_navigation": list(RIDER_NAVIGATION),
        "secondary_services": list(RIDER_SECONDARY_SERVICES),
        "core_lifecycle": (
            "Discover",
            "Plan",
            "Compare",
            "Book",
            "Verify",
            "Travel",
            "Pay",
            "Track",
            "Receive Evidence",
            "Rate / Support",
        ),
        "identity_levels": ("Guest", "Basic", "Verified", "Trusted", "Business", "Family Administrator"),
        "services": _copy(RIDER_SERVICES),
        "safety": {
            "panic_button": "hold_for_3_seconds",
            "features": (
                "share_live_trip",
                "trusted_contacts",
                "driver_verification",
                "pickup_PIN",
                "route_deviation_alerts",
                "unexpected_stop_alerts",
                "unsafe_area_alerts",
                "silent_emergency",
                "post_trip_welfare_check",
            ),
        },
        "offline": {
            "supports": (
                "cached_saved_places",
                "cached_booking_history",
                "low_data_mode",
                "SMS_booking_fallback",
                "USSD_integration",
                "offline_pickup_PIN",
                "local_trip_state_cache",
                "deferred_receipt_sync",
                "retry_queue",
            ),
            "confirmation_rule": "booking_is_not_confirmed_without_authoritative_server_confirmation",
        },
        "payments": {
            "owner": "NovaPay",
            "mobile_money": list(MOBILE_MONEY_METHODS),
            "global": list(GLOBAL_PAYMENT_METHODS),
            "currencies": list(SUPPORTED_CURRENCIES),
        },
        "api_surface": list(RIDER_API_SURFACE),
    }


def build_operator_platform() -> dict[str, Any]:
    return {
        "name": "NovaRide Operator",
        "positioning": "Mobility Operations Control Plane",
        "mission_flow": (
            "Observe",
            "Detect",
            "Prioritize",
            "Intervene",
            "Coordinate",
            "Resolve",
            "Verify",
            "Record Evidence",
            "Improve",
        ),
        "navigation": list(OPERATOR_NAVIGATION),
        "command_center": {
            "dashboards": ("Global", "Country", "Region", "City", "Zone", "Fleet", "Service Type", "Product"),
            "signals": (
                "active_trips",
                "drivers_online",
                "riders_waiting",
                "unassigned_requests",
                "delayed_pickups",
                "active_emergencies",
                "failed_payments",
                "fleet_availability",
                "regional_service_status",
                "compliance_warnings",
            ),
        },
        "governed_interventions": (
            "manual_assignment",
            "driver_reassignment",
            "cancel_before_pickup",
            "recovery_ride",
            "dispatch_hold",
            "emergency_escalation",
            "feature_flag_emergency_disable",
            "pricing_policy_preview",
        ),
        "ai_boundary": {
            "NovaAI": "advisory_only",
            "prohibited_actions": (
                "force_assignment",
                "suspend_drivers_independently",
                "cancel_safety_critical_trips",
                "approve_payments",
                "authorize_refunds",
                "close_incidents",
            ),
        },
        "api_surface": list(OPERATOR_API_SURFACE),
    }


def build_backend_architecture() -> dict[str, Any]:
    return {
        "authority_model": {
            "rider_backend": {
                "owns": ("customer_mobility_interactions", "journey_search", "booking_intent", "trip_visibility", "support_requests"),
                "does_not_own": ("dispatch_decisions", "payment_settlement", "identity_verification"),
            },
            "driver_backend": {
                "owns": ("driver_workflow", "availability_surface", "shifts", "offers", "trip_execution_surface", "offline_sync"),
                "rule": "driver_is_not_dispatchable_until_core_dispatch_confirms_eligibility",
            },
            "operator_backend": {
                "owns": ("operational_oversight", "governed_intervention", "incident_management", "support_operations", "compliance_views"),
                "rule": "operator_backend_must_not_bypass_authoritative_domain_services",
            },
            "core_backend": {
                "owns": (
                    "bookings",
                    "trips",
                    "dispatch",
                    "matching",
                    "pricing",
                    "safety",
                    "geography",
                    "fleet_rules",
                    "mobility_state",
                ),
            },
            "NovaID": "identity_authentication_RBAC_attributes_device_trust",
            "NovaPay": "payments_wallets_settlement_payouts_financial_ledger",
            "NovaTrust": "signed_evidence_audit_receipts_replay_integrity",
            "NovaAI": "recommendations_only",
            "NovaCodePro": "delivery_releases_diagnostics_deployment_observability_readiness_evidence",
        },
        "core_components": list(CORE_BACKEND_COMPONENTS),
        "trip_state_machine": (
            "CREATED",
            "MATCHING",
            "ASSIGNED",
            "DRIVER_ACCEPTED",
            "DRIVER_EN_ROUTE",
            "DRIVER_ARRIVED",
            "PICKUP_VERIFIED",
            "IN_PROGRESS",
            "COMPLETING",
            "COMPLETED",
            "CANCELLED",
            "EMERGENCY",
            "DISPUTED",
        ),
        "booking_state_machine": ("DRAFT", "QUOTED", "CONFIRMED", "SEARCHING", "ASSIGNED", "CANCELLED", "EXPIRED", "CONVERTED_TO_TRIP"),
        "events": {
            "required_envelope_fields": (
                "event_id",
                "event_type",
                "aggregate_id",
                "aggregate_version",
                "occurred_at",
                "tenant_id",
                "region",
                "actor",
                "correlation_id",
                "causation_id",
                "schema_version",
                "payload",
                "integrity_hash",
            ),
            "event_types": list(MOBILITY_EVENTS),
        },
        "reliability": {
            "idempotent_operations": (
                "booking_creation",
                "offer_acceptance",
                "trip_start",
                "trip_completion",
                "payment_intent",
                "refund_request",
                "emergency_activation",
                "operator_intervention",
            ),
            "optimistic_locking": (
                "prevent_two_drivers_accepting_one_offer",
                "prevent_trip_completed_twice",
                "prevent_duplicate_payment_request",
                "prevent_conflicting_operator_changes",
                "prevent_duplicate_emergency_incidents",
            ),
        },
    }


def build_frontend_architecture() -> dict[str, Any]:
    return {
        "technology": {
            "mobile": ("React Native", "TypeScript", "React Navigation", "TanStack Query", "Zustand or Redux Toolkit", "React Hook Form", "Zod"),
            "web": ("React", "TypeScript", "Vite", "TanStack Router", "TanStack Query", "Zustand", "Map abstraction", "SSE or WebSocket"),
        },
        "apps": list(FRONTEND_APPS),
        "shared_packages": list(FRONTEND_PACKAGES),
        "state_authority": {
            "server_state": "TanStack Query",
            "local_ui_state": "Zustand or Redux Toolkit",
            "durable_offline_state": "SQLite or MMKV",
            "local_state_must_not_authorize": (
                "driver_dispatchability",
                "confirmed_booking",
                "payment_success",
                "identity_verification",
                "emergency_resolution",
            ),
        },
        "offline_policy": {
            "offline_safe": ("save_draft", "cache_route", "queue_profile_change", "store_inspection_evidence", "queue_permitted_trip_telemetry"),
            "authoritative_confirmation_required": ("accept_trip", "start_trip", "complete_trip", "payment", "refund", "identity_approval", "emergency_resolution"),
        },
        "maps": {
            "package": "novaride-maps",
            "providers": ("Google Maps", "Mapbox", "OpenStreetMap", "HERE", "Apple Maps"),
            "capabilities": ("live_location", "background_location", "offline_maps", "route_alternatives", "geofences", "hazard_overlays", "EV_charging", "low_data_mode"),
        },
        "safety_package": {
            "package": "novaride-safety",
            "components": (
                "PanicButton",
                "SafetyCenter",
                "TrustedContacts",
                "TripSharing",
                "PickupVerification",
                "RouteDeviationAlert",
                "WelfareCheck",
                "IncidentForm",
                "EmergencyStatus",
            ),
        },
        "release_governance": (
            "typecheck",
            "tests",
            "security",
            "clean_build",
            "signing",
            "artifact_verification",
            "publication",
            "public_url_verification",
            "device_smoke_test",
            "pilot_approval",
        ),
    }


def build_platform_integration() -> dict[str, Any]:
    return {
        "NovaID": ("authentication", "identity", "device_trust", "driver_rider_operator_RBAC"),
        "NovaPay": ("wallet", "cards", "mobile_money", "cash_reconciliation", "refunds", "settlement", "payouts"),
        "NovaTrust": ("trip_evidence", "receipts", "safety_records", "dispute_evidence", "operator_audit"),
        "NovaCodePro": ("release_governance", "build_provenance", "diagnostics", "feature_flags", "operational_monitoring"),
        "NovaFleet": ("fleet_management", "dispatch", "vehicle_allocation", "driver_scheduling"),
        "NovaAI": ("driver_copilot", "dispatch_intelligence", "safety_intelligence", "fraud_detection", "demand_forecasting"),
    }


def build_resilience_architecture() -> dict[str, Any]:
    return {
        "operating_principle": "preserve_core_journey_when_networks_providers_maps_or_components_are_degraded",
        "platform_qualities": ("flexibility", "accessibility", "reliability", "availability"),
        "omni_channel_booking": list(OMNI_CHANNEL_BOOKING),
        "hybrid_payment_flow": list(HYBRID_PAYMENT_FLOW),
        "universal_payment_methods": {
            "digital": (
                "credit_card",
                "debit_card",
                "apple_pay",
                "google_pay",
                "samsung_wallet",
                "novawallet",
                "qr_payments",
                "bank_transfer",
                "instant_pay",
            ),
            "mobile_money": list(MOBILE_MONEY_METHODS),
            "cash": ("cash", "cash_plus_wallet", "cash_plus_card", "split_payment"),
            "business": ("corporate_account", "monthly_invoicing", "employee_transport", "government_account", "university_account"),
            "advanced": (
                "split_fares",
                "shared_ride_payments",
                "scheduled_payments",
                "tips",
                "promo_codes",
                "gift_rides",
                "vouchers",
                "loyalty_rewards",
                "cashback",
                "subscriptions",
                "family_wallet",
            ),
        },
        "offline_first": {
            "rider": (
                "cached_maps",
                "cached_destinations",
                "offline_booking_queue",
                "offline_receipts",
                "offline_wallet_balance",
                "offline_emergency_button",
            ),
            "driver": (
                "acceptance_queue_requires_authoritative_ack",
                "queued_trip_updates",
                "queued_gps_updates",
                "queued_earnings",
                "queued_signatures",
                "cached_pickup_details",
            ),
            "sync_flow": ("reconnect", "synchronize", "resolve_conflicts", "verify", "continue"),
        },
        "resilience_layer": {
            "components": list(RESILIENCE_COMPONENTS),
            "graceful_degradation": _copy(DEGRADATION_RULES),
            "provider_controls": ("timeouts", "circuit_breakers", "retries", "fallbacks", "health_checks", "rate_limit_handling", "dead_letter_queues", "provider_isolation"),
        },
        "accessibility": {
            "standard": "WCAG_2_2_AA",
            "interface_modes": (
                "screen_reader",
                "keyboard_navigation",
                "high_contrast",
                "large_text",
                "reduced_motion",
                "color_blind_safe_indicators",
                "voice_guided_booking",
                "haptic_feedback",
                "simple_mode",
            ),
            "ride_attributes": (
                "wheelchair_accessible",
                "foldable_wheelchair_supported",
                "service_animal_permitted",
                "driver_assistance_available",
                "low_step_vehicle",
                "child_seat_available",
                "hearing_assistance",
                "visual_assistance",
                "mobility_assistance",
            ),
        },
        "availability_targets": _copy(SERVICE_AVAILABILITY_TARGETS),
        "regional_expansion": _copy(COUNTRY_EXPANSION_PROFILES),
        "operator_signals": (
            "regional_availability",
            "availability_zone_status",
            "payment_provider_health",
            "map_provider_health",
            "sms_whatsapp_health",
            "offline_user_count",
            "sync_backlog",
            "dispatch_backlog",
            "gps_confidence_degradation",
            "service_failover_state",
            "emergency_system_status",
            "database_replication",
            "event_stream_lag",
        ),
        "operations_window": {
            "name": "Resilience and Availability",
            "quick_actions": (
                "enable_degraded_mode",
                "switch_provider",
                "drain_provider",
                "open_circuit",
                "close_circuit",
                "start_reconciliation",
                "pause_low_priority_sync",
                "trigger_failover",
                "broadcast_outage_message",
                "open_incident",
            ),
            "approval_required": (
                "regional_isolation",
                "payment_provider_switch",
                "emergency_only_mode",
                "cross_border_data_rerouting",
            ),
        },
        "multi_zone_topology": {
            "minimum_zones": 3,
            "critical_dependencies": (
                "postgresql_multi_az",
                "replicated_redis",
                "multi_broker_event_stream",
                "versioned_object_storage",
                "secrets_manager",
                "multi_zone_ingress",
                "zone_aware_kubernetes_scheduling",
            ),
            "kubernetes_controls": (
                "topology_spread_constraints",
                "pod_disruption_budgets",
                "anti_affinity",
                "readiness_probes",
                "startup_probes",
                "graceful_shutdown",
                "autoscaling",
                "zone_aware_traffic",
            ),
        },
        "regional_isolation": {
            "regional_services": (
                "regional_api",
                "regional_dispatch",
                "regional_data_store",
                "regional_event_streams",
                "regional_payment_routing",
                "regional_emergency_configuration",
                "regional_observability",
            ),
            "global_control_plane_unavailable_rule": "regional_booking_dispatch_active_trips_and_local_payment_fallback_continue",
        },
        "security_requirements": (
            "encryption_at_rest",
            "encryption_in_transit",
            "payload_minimization",
            "short_lived_data",
            "device_binding",
            "replay_protection",
            "signed_synchronization_requests",
            "nonce_validation",
            "tenant_isolation",
            "region_isolation",
            "full_audit_trails",
        ),
        "production_gates": (
            "durability_tests",
            "idempotency_tests",
            "migration_tests",
            "provider_failure_tests",
            "circuit_breaker_tests",
            "offline_synchronization_tests",
            "conflict_resolution_tests",
            "mobile_restart_tests",
            "queue_corruption_tests",
            "multi_zone_failover_tests",
            "database_promotion_tests",
            "emergency_path_tests",
            "load_tests",
            "security_tests",
            "accessibility_tests",
            "recovery_evidence_verification",
        ),
        "governed_high_impact_actions": (
            "regional_shutdown",
            "emergency_failover",
            "pricing_mode_change",
            "payment_provider_switch",
            "cross_border_data_rerouting",
            "accessibility_configuration_change",
        ),
    }


def build_runtime_metadata() -> dict[str, Any]:
    return {
        "runtime_version": "2026.2",
        "typed_models_implemented": True,
        "persistence_implemented": {
            "in_memory_adapter": True,
            "postgres_migration_contracts": True,
            "live_postgres_deployment_verified": False,
        },
        "state_machines_enforced": True,
        "APIs_implemented": {
            "runtime_status": "/v1/novaride/runtime/status",
            "driver": (
                "/v1/drivers/onboarding",
                "/v1/driver/shifts/start",
                "/v1/driver/{driver_id}/availability",
                "/v1/driver/offers/{offer_id}/accept",
                "/v1/driver/trips/{trip_id}/arrive",
                "/v1/driver/trips/{trip_id}/verify-passenger",
                "/v1/driver/trips/{trip_id}/start",
                "/v1/driver/trips/{trip_id}/location",
                "/v1/driver/trips/{trip_id}/complete",
                "/v1/driver/emergency",
            ),
            "rider": (
                "/v1/riders/onboarding",
                "/v1/rider/fares/quote",
                "/v1/rider/bookings",
                "/v1/rider/trips/{trip_id}/emergency",
            ),
            "operator": (
                "/v1/operator/command-center",
                "/v1/operator/emergencies/{emergency_id}/acknowledge",
                "/v1/operator/commands",
            ),
            "fleet": ("/v1/fleets", "/v1/fleets/{fleet_id}/vehicles"),
            "logistics": (
                "/v1/logistics/orders",
                "/v1/logistics/orders/{order_id}/pickup",
                "/v1/logistics/orders/{order_id}/deliver",
            ),
            "corporate": ("/v1/corporate/accounts", "/v1/corporate/bookings"),
            "transit": ("/v1/transit/journeys/plan",),
            "wallet_references": ("/v1/novaride/wallets/me/summary", "/v1/novaride/payment-intents"),
        },
        "events_persistent": True,
        "replay_supported": ("aggregate", "correlation_id", "event_range"),
        "read_models_operational": (
            "operator_command_center",
            "driver_ride_queue",
            "event_count_projection",
        ),
        "mobile_sdk_integrated": {
            "package": "packages/novaride-api-sdk",
            "generated_openapi_client": False,
            "typed_runtime_client_contract": True,
        },
        "E2E_scenarios_passed": "focused_runtime_suite",
        "release_gates_passed": {
            "code_compilation": True,
            "focused_tests": True,
            "outbox_local_worker": True,
            "deterministic_replay_local": True,
            "replay_side_effect_firewall": True,
            "projection_rebuild_local": True,
            "migration_static_verification": True,
            "event_schema_compatibility": True,
            "fresh_apk_builds": False,
            "public_download_validation": False,
            "physical_device_smoke": False,
        },
        "deployment_certification": {
            "target_status": "deployment_verified_release_certified",
            "current_status": "CERTIFICATION_INCOMPLETE",
            "live_postgresql_verified": False,
            "transactional_outbox_live_verified": False,
            "event_consumers_live_verified": False,
            "deterministic_replay_live_verified": False,
            "immutable_publication_verified": False,
            "device_certification_verified": False,
            "certificate": "reports/novaride/certification/novaride-2026.2.0-certificate.yaml",
        },
        "APK_release_status": "not_built_or_published_in_this_runtime_pass",
        "live_runtime_evidence": {
            "deployed_services_verified": False,
            "live_event_consumers_verified": False,
            "monitoring_collecting_data": False,
        },
        "governance_state": {
            "GA_ALLOWED": False,
            "GA_APPROVAL": "PENDING",
            "REAL_PAYMENTS_ENABLED": False,
            "REAL_PAYMENT_APPROVAL": "PENDING",
        },
    }


@lru_cache(maxsize=1)
def _cached_manifest() -> dict[str, Any]:
    return {
        "id": "novaride-next-generation-universal-mobility-platform",
        "name": "NovaRide Next Generation Universal Mobility Platform",
        "version": NOVARIDE_NEXT_GENERATION_VERSION,
        "status": NOVARIDE_NEXT_GENERATION_STATUS,
        "positioning": "One governed mobility platform for riders, drivers, operators, fleets, support, inspectors, and future autonomous services.",
        "markets": list(GLOBAL_MARKETS),
        "driver": build_driver_platform(),
        "rider": build_rider_platform(),
        "operator": build_operator_platform(),
        "backend": build_backend_architecture(),
        "frontend": build_frontend_architecture(),
        "regional_adaptation": _copy(REGIONAL_ADAPTATION),
        "platform_integration": build_platform_integration(),
        "resilience": build_resilience_architecture(),
        "runtime_metadata": build_runtime_metadata(),
        "localization": {
            "languages": list(SUPPORTED_LANGUAGES),
            "currencies": list(SUPPORTED_CURRENCIES),
            "region_config_files": (
                "australia.json",
                "usa.json",
                "canada.json",
                "uk.json",
                "eu.json",
                "india.json",
                "kenya.json",
                "south_africa.json",
                "tanzania.json",
                "uganda.json",
                "rwanda.json",
                "zambia.json",
                "botswana.json",
                "namibia.json",
                "zimbabwe.json",
                "burundi.json",
                "drc.json",
                "nigeria.json",
                "ghana.json",
                "cote_divoire.json",
                "senegal.json",
                "egypt.json",
                "morocco.json",
            ),
        },
        "target_maturity": _copy(MATURITY_TARGETS),
        "authority_statement": (
            "Rider, Driver, and Operator apps own role-specific experiences; NovaRide Core owns authoritative "
            "trip, dispatch, safety, pricing, geography, fleet, and mobility state."
        ),
        "honest_status": "runtime_capabilities_complete_release_candidate",
    }


def novaride_next_generation_manifest() -> dict[str, Any]:
    return deepcopy(_cached_manifest())


__all__ = [
    "NOVARIDE_NEXT_GENERATION_VERSION",
    "novaride_next_generation_manifest",
    "build_driver_platform",
    "build_rider_platform",
    "build_operator_platform",
    "build_backend_architecture",
    "build_frontend_architecture",
    "build_resilience_architecture",
]
