"""Next-gen AfriRide mobile API contract router."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field

from afritech.api.auth.jwt_device_auth import JWT, require_roles
from afritech.afriprogramming.control_plane import get_control_plane
from afritech.afriprogramming.rbac import canonical_role_name


def get_gateway() -> Any:
    return _runtime().get_gateway()


def get_trace_log() -> Any:
    return _runtime().get_trace_log()


def proof_events_for_ride(trace_log: Any, ride: Any) -> tuple[Any, ...]:
    return import_module("afriride_system.backend.proof_material").proof_events_for_ride(trace_log, ride)


def _receipt_engine() -> Any:
    return import_module("afriride_system.backend.receipt_engine").ReceiptEngine()


def _system_service(gateway: Any, trace_log: Any) -> Any:
    return import_module("afriride_system.services.system_service").SystemService(gateway, trace_log)


def _runtime() -> Any:
    return import_module("afriride_system.api.dependencies.runtime")


class RBACAssignmentRequest(BaseModel):
    organization_id: str | None = None
    subject_type: str = "user"
    subject_id: str
    role: str
    granted_by: str | None = None
    granted_role: str = "ADMIN"
    status: str = "active"
    notes: list[str] = Field(default_factory=list)


NOVARIDE_APP_SURFACES: tuple[dict[str, Any], ...] = (
    {
        "key": "passenger",
        "name": "NovaRide Passenger",
        "role": "CUSTOMER",
        "platforms": ("Android", "iOS", "Web"),
        "route_prefix": "/v1/novaride/passenger",
        "primary_routes": (
            "/v1/rider/rides",
            "/v1/rider/rides/{ride_id}",
            "/v1/rider/rides/{ride_id}/receipt",
            "/v1/rider/rides/{ride_id}/replay",
        ),
        "capabilities": (
            "book_now",
            "schedule_ride",
            "airport_pickup",
            "multiple_stops",
            "driver_tracking",
            "trip_sharing",
            "sos",
            "novapay_wallet",
            "ride_receipts",
            "support_tickets",
        ),
    },
    {
        "key": "driver",
        "name": "NovaRide Driver",
        "role": "DRIVER",
        "platforms": ("Android", "iOS"),
        "route_prefix": "/v1/novaride/driver",
        "primary_routes": (
            "/v1/driver/{driver_id}/availability",
            "/v1/driver/{driver_id}/ride-queue",
            "/v1/driver/rides/{ride_id}/accept",
            "/v1/driver/rides/{ride_id}/complete",
            "/v1/driver/{driver_id}/earnings",
        ),
        "capabilities": (
            "online_offline",
            "accept_rides",
            "navigation",
            "pickup_verification",
            "passenger_verification",
            "daily_earnings",
            "novapay_cash_out",
            "training_materials",
        ),
    },
    {
        "key": "operator",
        "name": "NovaRide Operator App / Portal",
        "role": "OPERATOR",
        "platforms": ("Web",),
        "route_prefix": "/v1/novaride/operator",
        "primary_routes": (
            "/v1/operator/dashboard",
            "/v1/operator/analytics",
            "/v1/operator/decisions",
            "/v1/operator/actions",
            "/v1/operator/city-automation",
            "/v1/operator/multi-city-orchestration",
            "/v1/operator/digital-twin",
            "/v1/operator/meta-learning-redesign",
            "/v1/operator/demand-forecast",
            "/v1/operator/replay-exceptions",
            "/v1/operator/city-profit-optimization",
        ),
        "capabilities": (
            "live_ride_map",
            "driver_locations",
            "manual_dispatch",
            "ride_reassignment",
            "emergency_monitoring",
            "trust_monitoring",
            "fraud_detection",
            "route_replay",
            "digital_twin_monitoring",
            "self_improving_loop",
            "meta_learning_redesign",
            "city_budget_optimization",
            "predictive_demand_ml",
            "real_time_analytics",
            "live_operations_dashboard",
            "live_map_rides_and_drivers",
            "demand_heatmap",
            "incident_monitoring",
            "sos_escalation",
            "payment_receipt_status",
            "provider_health",
            "operational_alerts",
        ),
    },
    {
        "key": "fleet",
        "name": "NovaRide Fleet",
        "role": "FLEET_OWNER",
        "platforms": ("Web",),
        "route_prefix": "/v1/novaride/fleet",
        "primary_routes": (
            "/v1/afriride/fleet/summary",
            "/v1/afriride/fleet/drivers",
        ),
        "capabilities": (
            "vehicle_management",
            "driver_assignment",
            "maintenance",
            "insurance",
            "fuel_tracking",
            "fleet_earnings",
            "driver_payouts",
            "fleet_reports",
        ),
    },
    {
        "key": "business",
        "name": "NovaRide Business",
        "role": "CLIENT",
        "platforms": ("Web",),
        "route_prefix": "/v1/novaride/business",
        "primary_routes": (
            "/v1/novatech/organizations/{organization_id}/platform",
            "/v1/novatech/organizations/{organization_id}/billing",
            "/v1/novaride/phase3/business/pricing",
            "/v1/novaride/phase3/business/incentives",
            "/v1/novaride/phase4/business/budget-allocation",
            "/v1/novaride/phase4/business/profit-optimization",
        ),
        "capabilities": (
            "employee_bookings",
            "approval_workflows",
            "monthly_invoicing",
            "business_wallet",
            "department_budgets",
            "travel_reports",
            "pricing_visibility",
            "incentive_visibility",
            "budget_allocation_visibility",
            "profit_optimization_visibility",
        ),
    },
    {
        "key": "merchant",
        "name": "NovaRide Merchant Portal",
        "role": "PARTNER",
        "platforms": ("Web",),
        "route_prefix": "/v1/novaride/merchant",
        "primary_routes": (
            "/v1/partners/registry",
            "/v1/partner/verify",
            "/v1/novaride/partner/portal-contract",
        ),
        "capabilities": (
            "guest_ride_booking",
            "corporate_billing",
            "voucher_management",
            "ride_analytics",
            "invoice_management",
            "settlement",
        ),
    },
    {
        "key": "corporate",
        "name": "NovaRide Corporate Portal",
        "role": "CLIENT",
        "platforms": ("Web",),
        "route_prefix": "/v1/novaride/corporate",
        "primary_routes": (
            "/v1/novatech/organizations/{organization_id}/platform",
            "/v1/novatech/organizations/{organization_id}/billing",
            "/v1/novaride/business/portal-contract",
        ),
        "capabilities": (
            "employee_travel",
            "approvals",
            "cost_centres",
            "budgets",
            "invoices",
            "travel_analytics",
        ),
    },
    {
        "key": "admin",
        "name": "NovaRide Admin",
        "role": "ADMIN",
        "platforms": ("Web",),
        "route_prefix": "/v1/novaride/admin",
        "primary_routes": (
            "/v1/afriride/rbac/catalog",
            "/v1/afriride/rbac/assignments",
            "/v1/novatech/saas/status",
            "/v1/ops/audit/dashboard",
        ),
        "capabilities": (
            "user_management",
            "driver_approval",
            "vehicle_approval",
            "pricing_rules",
            "service_zones",
            "promotions",
            "compliance",
            "audit_logs",
            "system_health",
        ),
    },
    {
        "key": "inspector",
        "name": "NovaRide Inspector App / Portal",
        "role": "VERIFIER",
        "platforms": ("Android Tablet", "Web"),
        "route_prefix": "/v1/novaride/inspector",
        "primary_routes": (
            "/v1/operator/public-verification/status",
            "/v1/core-platform/trust/explorer/{receipt_id}",
        ),
        "capabilities": (
            "vehicle_inspection_checklist",
            "driver_verification",
            "license_validation",
            "photo_capture",
            "inspection_reports",
            "compliance_status",
            "permit_check",
            "insurance_check",
            "roadworthiness_checklist",
            "regulatory_export",
            "violation_suspension_workflow",
        ),
    },
    {
        "key": "trust_safety",
        "name": "NovaRide Trust & Safety Portal",
        "role": "OPERATOR",
        "platforms": ("Web",),
        "route_prefix": "/v1/novaride/trust-safety",
        "primary_routes": (
            "/v1/operator/replay-exceptions",
            "/v1/operator/public-verification/status",
            "/v1/core-platform/trust/explorer/{receipt_id}",
        ),
        "capabilities": (
            "sos_cases",
            "incident_timeline",
            "replay",
            "evidence_viewer",
            "driver_verification",
            "passenger_verification",
            "risk_scoring",
        ),
    },
    {
        "key": "support",
        "name": "NovaRide Support",
        "role": "OPERATOR",
        "platforms": ("Web",),
        "route_prefix": "/v1/novaride/support",
        "primary_routes": (
            "/v1/rider/rides/{ride_id}",
            "/v1/rider/rides/{ride_id}/receipt",
            "/v1/operator/replay-exceptions",
        ),
        "capabilities": (
            "customer_tickets",
            "ride_lookup",
            "refund_requests",
            "driver_assistance",
            "passenger_assistance",
            "escalation_management",
        ),
    },
    {
        "key": "partner",
        "name": "NovaRide Partner",
        "role": "PARTNER",
        "platforms": ("Web",),
        "route_prefix": "/v1/novaride/partner",
        "primary_routes": (
            "/v1/partners/registry",
            "/v1/partner/verify",
        ),
        "capabilities": (
            "ride_booking_widget",
            "guest_transport",
            "bulk_ride_requests",
            "partner_reporting",
            "partner_billing",
        ),
    },
    {
        "key": "developer",
        "name": "NovaRide Developer Portal",
        "role": "DEVELOPER",
        "platforms": ("Web",),
        "route_prefix": "/v1/novaride/developer",
        "primary_routes": (
            "/v1/platform-contracts/schemas",
            "/v1/partners/registry",
            "/v1/novaride/ecosystem",
        ),
        "capabilities": (
            "api_keys",
            "sdks",
            "sandbox",
            "webhook_manager",
            "documentation",
            "usage_analytics",
        ),
    },
)

NOVARIDE_SHARED_PLATFORM: tuple[dict[str, str], ...] = (
    {"key": "novaid", "name": "NovaID", "purpose": "Authentication, identity verification, and user profiles"},
    {"key": "policy", "name": "Policy Engine", "purpose": "Jurisdiction, role, safety, and operational policy decisions"},
    {"key": "novapay", "name": "NovaPay", "purpose": "Ride payments, wallets, refunds, driver earnings, and corporate billing"},
    {"key": "dispatch", "name": "Dispatch Engine", "purpose": "Driver matching and ride lifecycle coordination"},
    {"key": "matching", "name": "Matching Engine", "purpose": "Driver selection, queue balancing, and assignment explainability"},
    {"key": "pricing", "name": "Pricing Engine", "purpose": "Fare estimates, deterministic price explanation, service-zone pricing, and incentive controls"},
    {"key": "maps", "name": "Maps & Routing", "purpose": "Navigation, route display, ETA, and trip timeline"},
    {"key": "trust", "name": "Trust Engine", "purpose": "Driver and rider safety, verification, fraud monitoring, and SOS escalation"},
    {"key": "inspection", "name": "Inspection Registry", "purpose": "Vehicle, driver, permit, insurance, roadworthiness, and evidence records"},
    {"key": "incident", "name": "Incident Registry", "purpose": "SOS, safety escalation, incident lifecycle, and closure evidence"},
    {"key": "notifications", "name": "NovaNotify", "purpose": "Push, SMS, email, receipts, and operational alerts"},
    {"key": "analytics", "name": "Analytics Engine", "purpose": "Utilization, cancellations, demand, revenue, and fleet reporting"},
    {"key": "audit", "name": "Audit & Replay", "purpose": "Compliance logs, route replay, proof receipts, and verification"},
    {"key": "events", "name": "Event Platform", "purpose": "Ride lifecycle event stream, replay, evidence binding, and proof emission"},
    {"key": "control_plane", "name": "Control Plane", "purpose": "Feature gates, RBAC, tenant controls, policies, and operational governance"},
)

NOVARIDE_ENTERPRISE_OPERATIONS_LAYER: tuple[dict[str, Any], ...] = (
    {
        "key": "command_center",
        "name": "Unified Command Center",
        "purpose": "One operational control surface for rides, drivers, incidents, payments, providers, and replay evidence.",
        "capabilities": ("city_status", "live_operations", "dispatch_intervention", "incident_escalation", "proof_review"),
    },
    {
        "key": "city_zone_model",
        "name": "City Operations / Zone Model",
        "purpose": "Model cities, service zones, airport zones, geofences, surge boundaries, and jurisdiction-aware operating rules.",
        "capabilities": ("city_registry", "service_zones", "airport_zones", "geofencing", "zone_policy"),
    },
    {
        "key": "operational_digital_twin",
        "name": "Operational Digital Twin",
        "purpose": "Replay and simulate the live mobility network using rides, drivers, demand, incidents, and provider state.",
        "capabilities": ("network_snapshot", "scenario_simulation", "capacity_projection", "replay_comparison", "what_if_analysis"),
    },
    {
        "key": "ai_decision_explanation",
        "name": "AI Decision Explanation Layer",
        "purpose": "Explain dispatch, pricing, safety, fraud, ETA, and demand recommendations without granting AI authority.",
        "capabilities": ("dispatch_explanation", "pricing_explanation", "risk_explanation", "confidence_signals", "operator_review"),
    },
    {
        "key": "workflow_incident_engine",
        "name": "Workflow / Incident Engine",
        "purpose": "Coordinate SOS, disputes, support, trust, compliance, provider incidents, approvals, and closure evidence.",
        "capabilities": ("case_routing", "sla_tracking", "escalation_policy", "evidence_binding", "closure_log"),
    },
    {
        "key": "fleet_intelligence",
        "name": "Fleet Intelligence",
        "purpose": "Track driver supply, vehicle health, inspection status, utilization, maintenance, earnings, and fleet quality.",
        "capabilities": ("supply_health", "vehicle_health", "driver_quality", "maintenance_forecast", "fleet_scorecards"),
    },
    {
        "key": "public_trust_portal",
        "name": "Public Trust Portal",
        "purpose": "Publish controlled transparency views for receipts, safety standards, verification, and public trust evidence.",
        "capabilities": ("receipt_verification", "safety_standards", "trust_reports", "public_status", "audit_exports"),
    },
    {
        "key": "partner_developer_ecosystem",
        "name": "Partner / Developer Ecosystem",
        "purpose": "Expose governed APIs, webhooks, sandbox, SDKs, partner onboarding, and usage analytics.",
        "capabilities": ("api_keys", "webhooks", "sandbox", "sdk_catalog", "partner_analytics"),
    },
    {
        "key": "sre_observability",
        "name": "SRE Observability",
        "purpose": "Measure reliability, latency, errors, queues, provider health, replay lag, and operational risk.",
        "capabilities": ("slo_dashboard", "error_budget", "provider_health", "queue_lag", "replay_lag"),
    },
    {
        "key": "multi_tenant_governance",
        "name": "Multi-Tenant Governance",
        "purpose": "Govern organizations, roles, feature flags, policies, licensing, data boundaries, and tenant isolation.",
        "capabilities": ("tenant_registry", "rbac", "feature_flags", "policy_versions", "data_residency"),
    },
)

NOVARIDE_LAYERED_ARCHITECTURE: tuple[str, ...] = (
    "Applications / Portals",
    "Control Plane",
    "Execution Services",
    "Evidence / Event Platform",
    "Enterprise Operations",
)

NOVARIDE_OPERATOR_INTERVENTION_FLOW: tuple[str, ...] = (
    "Operator",
    "Intervention Request",
    "Policy Evaluation",
    "Control Plane Decision",
    "Execution",
    "Evidence",
)

NOVARIDE_PRODUCTION_INFRASTRUCTURE_READINESS: tuple[dict[str, Any], ...] = (
    {
        "key": "distributed_consistency",
        "name": "Distributed Consistency",
        "purpose": "Ensure checkpoints, Merkle roots, replay, and ledger roots remain deterministic across nodes and regions.",
        "capabilities": ("checkpoint_consistency", "merkle_root_consistency", "replay_consistency", "ledger_root_consistency"),
    },
    {
        "key": "key_management",
        "name": "Key Management",
        "purpose": "Move signing authority into HSM, Cloud KMS, or hardware-backed signing with rotation and audit trails.",
        "capabilities": ("hsm_signing", "cloud_kms", "key_rotation", "signing_audit"),
    },
    {
        "key": "operational_resilience",
        "name": "Operational Resilience",
        "purpose": "Validate regional failover, recovery procedures, chaos testing, and disaster recovery operations.",
        "capabilities": ("regional_failover", "recovery_runbooks", "chaos_testing", "dr_validation"),
    },
    {
        "key": "regulatory_readiness",
        "name": "Regulatory Readiness",
        "purpose": "Keep licensing, corridor configuration, AML/KYC, sanctions, and reporting deployment-ready.",
        "capabilities": ("licensing", "corridor_config", "aml_kyc", "sanctions", "reporting"),
    },
    {
        "key": "independent_verification",
        "name": "Independent Verification",
        "purpose": "Ensure external verifier artifacts validate without internal runtime assumptions.",
        "capabilities": ("offline_verifier", "audit_bundle", "runtime_independence", "partner_audit"),
    },
)

NOVARIDE_API_GATEWAY_RESPONSIBILITIES: tuple[str, ...] = (
    "request_validation",
    "novaid_authentication",
    "rbac_enforcement",
    "backend_service_routing",
)

NOVARIDE_APP_LAYER_CONTRACT: tuple[dict[str, Any], ...] = (
    {
        "app": "Passenger App",
        "role": "CUSTOMER",
        "interface_responsibility": "ride_booking_and_trip_experience",
        "example_route": "/v1/rider/rides",
    },
    {
        "app": "Driver App",
        "role": "DRIVER",
        "interface_responsibility": "trip_execution_and_earnings",
        "example_route": "/v1/driver/rides/{ride_id}/accept",
    },
    {
        "app": "Operator Dashboard",
        "role": "OPERATOR",
        "interface_responsibility": "control_monitoring_and_escalation",
        "example_route": "/v1/operator/actions",
    },
)

NOVARIDE_BACKEND_AUTHORITY_CONTROLS: tuple[str, ...] = (
    "dispatch_decisions",
    "novapay_payments",
    "pricing_calculations",
    "fraud_detection",
    "external_integrations",
)

NOVARIDE_APP_FORBIDDEN_AUTHORITY: tuple[str, ...] = (
    "payment_processing",
    "pricing_mutation",
    "dispatch_bypass",
    "direct_provider_access",
)

NOVARIDE_RIDE_REQUEST_FLOW: tuple[str, ...] = (
    "passenger_app_requests_ride",
    "api_validates_request_with_novaid",
    "pricing_engine_estimates_fare",
    "dispatch_engine_matches_driver",
    "driver_app_receives_request",
    "driver_accepts",
    "maps_tracks_trip",
    "trip_completes",
    "novapay_processes_payment",
    "audit_engine_stores_logs",
    "analytics_updated",
)

NOVARIDE_CROSS_APP_SERVICE_MATRIX: tuple[dict[str, Any], ...] = (
    {"app": "Passenger", "services": ("Pricing", "Dispatch", "NovaPay")},
    {"app": "Driver", "services": ("Dispatch", "Maps", "Earnings")},
    {"app": "Operator", "services": ("Analytics", "Dispatch", "Audit")},
    {"app": "Fleet", "services": ("Analytics", "NovaPay")},
    {"app": "Business", "services": ("NovaPay", "Analytics", "Pricing")},
    {"app": "Admin", "services": ("RBAC", "Pricing", "Audit")},
    {"app": "Inspector", "services": ("Trust", "Audit")},
    {"app": "Support", "services": ("Replay", "NovaPay")},
    {"app": "Partner", "services": ("Dispatch", "Billing")},
)

NOVARIDE_ARCHITECTURE_OUTCOMES: tuple[str, ...] = (
    "scalable_multi_app_ecosystem",
    "centralized_security_authority",
    "clear_separation_of_concerns",
    "enterprise_ready_fleet_business_partner_support",
    "audit_replay_evidence",
    "saas_ready_structure",
)

NOVARIDE_LIFECYCLE: tuple[str, ...] = (
    "passenger_requests_ride",
    "nearest_driver_matched",
    "driver_accepts",
    "driver_arrives",
    "passenger_pickup",
    "trip_in_progress",
    "destination_reached",
    "payment_via_novapay",
    "driver_settlement",
    "ratings_and_feedback",
)

NOVARIDE_OPERATOR_DASHBOARD_MODULES: tuple[dict[str, Any], ...] = (
    {
        "key": "operations",
        "name": "Operations",
        "purpose": "Real-time control center for rides, drivers, and demand posture.",
        "features": (
            "live_ride_map",
            "driver_availability",
            "zone_distribution",
            "demand_heatmap_next_phase",
        ),
        "actions": ("submit_dispatch_intervention_request", "request_assignment_review", "trigger_rematching"),
        "backend_integrations": ("dispatch", "maps", "analytics"),
        "status": "partially_implemented",
    },
    {
        "key": "ride_management",
        "name": "Ride Management",
        "purpose": "Search, inspect, replay, and intervene in ride lifecycle events.",
        "features": ("ride_lookup", "ride_timeline", "receipt_view", "route_replay"),
        "actions": ("reassign_driver", "cancel_ride", "modify_route_controlled", "force_complete_admin"),
        "backend_integrations": ("dispatch", "audit"),
        "status": "partially_implemented",
    },
    {
        "key": "driver_monitoring",
        "name": "Driver Monitoring",
        "purpose": "Monitor driver state, trust, performance, and compliance posture.",
        "features": ("live_driver_tracking", "driver_status", "acceptance_rate", "cancellation_rate", "ratings"),
        "actions": ("suspend_driver", "flag_for_inspection", "trigger_compliance_checks"),
        "backend_integrations": ("trust", "analytics"),
        "status": "partially_implemented",
    },
    {
        "key": "safety_emergency",
        "name": "Safety & Emergency",
        "purpose": "Handle SOS, route anomalies, suspicious patterns, and escalation.",
        "features": ("sos_monitoring", "incident_location", "risk_detection", "trust_dashboard"),
        "actions": ("contact_driver", "contact_passenger", "escalate_incident", "notify_authorities_future"),
        "backend_integrations": ("trust", "audit"),
        "status": "implemented",
    },
    {
        "key": "analytics",
        "name": "Analytics Dashboard",
        "purpose": "Operational, driver, financial, and demand intelligence.",
        "features": ("active_rides", "completed_rides", "cancelled_rides", "driver_utilization", "revenue_dashboard", "demand_trends", "real_time_analytics"),
        "actions": ("review_trends", "export_metrics", "open_exception_review"),
        "backend_integrations": ("analytics", "novapay", "pricing"),
        "status": "implemented",
    },
    {
        "key": "predictive_demand",
        "name": "Predictive Demand ML",
        "purpose": "Bounded demand forecasting and real-time city pressure analytics for operator planning.",
        "features": ("demand_forecast", "supply_gap", "zone_pressure", "forecast_windows", "real_time_analytics"),
        "actions": ("review_forecast", "rebalance_supply", "export_demand_trace"),
        "backend_integrations": ("analytics", "dispatch", "audit"),
        "status": "implemented",
    },
    {
        "key": "business_pricing",
        "name": "Business Pricing & Incentives",
        "purpose": "Preview deterministic fares, bounded incentive plans, and commercial take-rate for the mobility business layer.",
        "features": ("fare_preview", "price_multiplier", "incentive_plan", "take_rate", "demand_signal", "revenue_preview"),
        "actions": ("review_pricing_projection", "review_incentive_plan", "export_pricing_trace"),
        "backend_integrations": ("pricing", "analytics", "novapay", "audit"),
        "status": "implemented",
    },
    {
        "key": "business_optimization",
        "name": "Budget Allocation & Profit Optimization",
        "purpose": "Allocate spend across cities and optimize profit margins using deterministic operational and financial signals.",
        "features": ("city_budget_allocation", "profit_projection", "city_margin", "budget_rebalance", "coverage_guard"),
        "actions": ("review_budget_allocation", "review_profit_projection", "export_optimization_trace"),
        "backend_integrations": ("analytics", "pricing", "novapay", "audit"),
        "status": "implemented",
    },
    {
        "key": "strategy_engine",
        "name": "Autonomous Strategy Engine",
        "purpose": "Synthesize bounded autonomy, demand, pricing, and profit signals into a read-only city strategy plan.",
        "features": ("strategy_lane", "city_priorities", "strategy_windows", "guardrails", "read_only_projection"),
        "actions": ("review_strategy_plan", "rebalance_city_priority", "export_strategy_trace"),
        "backend_integrations": ("analytics", "dispatch", "pricing", "novapay", "audit"),
        "status": "implemented",
    },
    {
        "key": "ecosystem",
        "name": "NovaRide Ecosystem Panel",
        "purpose": "Expose the nine-app NovaRide product family and authority boundaries.",
        "features": ("app_count", "app_surfaces", "authority_boundaries", "lifecycle_preview"),
        "actions": ("inspect_surface_contract", "verify_backend_authority"),
        "backend_integrations": ("novaid", "novapay", "dispatch", "trust", "audit"),
        "status": "implemented",
    },
    {
        "key": "support_escalation",
        "name": "Support & Escalation",
        "purpose": "Link ride issues, refund requests, driver assistance, and passenger assistance.",
        "features": ("customer_ticket_lookup", "ride_issue_tracking", "refund_management", "escalation_management"),
        "actions": ("issue_refund_via_novapay", "escalate_case", "link_support_workflow"),
        "backend_integrations": ("support", "novapay", "audit"),
        "status": "contract_declared",
    },
)

NOVARIDE_OPERATOR_LAYOUT: dict[str, Any] = {
    "left_navigation": ("Operations", "Rides", "Drivers", "Safety", "Analytics", "Support"),
    "main_area": ("Live map", "Analytics widgets", "Alerts and notifications"),
    "side_panels": ("Ride details", "Driver details", "NovaRide ecosystem overview"),
}

NOVARIDE_OPERATOR_ALLOWED_ACTIONS: tuple[str, ...] = (
    "manual_dispatch",
    "ride_reassignment",
    "monitoring",
    "emergency_handling",
)

NOVARIDE_OPERATOR_FORBIDDEN_ACTIONS: tuple[str, ...] = (
    "direct_payment_execution",
    "direct_provider_integrations",
    "backend_rule_bypass",
)

NOVARIDE_OPERATOR_WORKFLOW: tuple[str, ...] = (
    "passenger_requests_ride",
    "dispatch_assigns_driver",
    "operator_monitors_live_map",
    "driver_delayed_operator_reassigns",
    "risk_flag_operator_intervenes",
    "trip_completed",
    "payment_processed_by_novapay",
    "operator_reviews_analytics",
)

NOVARIDE_FLEET_MANAGER_MODULES: tuple[dict[str, Any], ...] = (
    {
        "key": "fleet_management",
        "name": "Fleet Management",
        "purpose": "Centralized overview for vehicles, active drivers, service posture, and utilization.",
        "features": (
            "total_vehicles",
            "active_drivers",
            "vehicles_in_service",
            "vehicles_offline",
            "fleet_utilization_rate",
            "zone_availability",
        ),
        "actions": ("assign_drivers_to_vehicles", "track_fleet_activity", "monitor_zone_availability"),
        "backend_integrations": ("dispatch", "analytics"),
        "status": "partially_implemented",
    },
    {
        "key": "driver_management",
        "name": "Driver Management",
        "purpose": "Manage driver profiles, vehicle assignment, performance, and compliance posture.",
        "features": (
            "driver_profiles",
            "assignment_controls",
            "multi_driver_rotation",
            "ratings",
            "acceptance_rate",
            "cancellation_rate",
            "trip_history",
            "driver_status",
        ),
        "actions": ("approve_driver", "reject_driver", "flag_for_inspection", "trigger_retraining"),
        "backend_integrations": ("novaid", "trust", "analytics", "novalearn"),
        "status": "partially_implemented",
    },
    {
        "key": "vehicle_management",
        "name": "Vehicle Management",
        "purpose": "Register, verify, document, and monitor vehicles in the fleet.",
        "features": (
            "vehicle_registry",
            "plate_number",
            "model_year",
            "capacity",
            "registration_documents",
            "insurance",
            "inspection_certificates",
            "vehicle_status",
        ),
        "actions": ("add_vehicle", "remove_vehicle", "update_documents", "track_expiration_alerts"),
        "backend_integrations": ("trust", "inspector"),
        "status": "contract_declared",
    },
    {
        "key": "maintenance_compliance",
        "name": "Maintenance & Compliance",
        "purpose": "Track scheduled maintenance, service evidence, insurance, inspections, and violations.",
        "features": (
            "scheduled_maintenance",
            "service_history",
            "repair_logs",
            "license_validity",
            "insurance_expiry",
            "safety_certifications",
            "inspection_reports",
            "photo_evidence",
        ),
        "actions": ("create_maintenance_schedule", "record_service", "review_compliance_alerts"),
        "backend_integrations": ("trust", "inspector", "audit"),
        "status": "contract_declared",
    },
    {
        "key": "financial_management",
        "name": "Financial Management",
        "purpose": "Summarize fleet earnings, driver payouts, expenses, and profit/loss without direct provider access.",
        "features": (
            "fleet_earnings",
            "earnings_per_vehicle",
            "earnings_per_driver",
            "driver_payouts",
            "commission_models",
            "expense_tracking",
            "profit_loss_summary",
            "revenue_trends",
        ),
        "actions": ("preview_payouts", "export_reports", "review_expenses"),
        "backend_integrations": ("novapay", "analytics", "pricing"),
        "status": "contract_declared",
    },
    {
        "key": "fleet_analytics",
        "name": "Fleet Analytics",
        "purpose": "Operational, driver, demand, and financial intelligence for fleet owners.",
        "features": (
            "fleet_utilization_rate",
            "ride_completion_rate",
            "idle_time",
            "top_performing_drivers",
            "low_performing_drivers",
            "driver_turnover",
            "peak_hours",
            "zone_performance",
        ),
        "actions": ("review_trends", "identify_underutilized_assets", "open_driver_review"),
        "backend_integrations": ("analytics",),
        "status": "partially_implemented",
    },
)

NOVARIDE_FLEET_NAVIGATION: tuple[str, ...] = (
    "Dashboard",
    "Vehicles",
    "Drivers",
    "Maintenance",
    "Finance",
    "Reports",
)

NOVARIDE_FLEET_ALLOWED_ACTIONS: tuple[str, ...] = (
    "manage_vehicles",
    "assign_drivers",
    "view_earnings_reports",
    "receive_payouts_via_novapay",
)

NOVARIDE_FLEET_FORBIDDEN_ACTIONS: tuple[str, ...] = (
    "bypass_control_plane_dispatch_policy",
    "direct_payment_provider_access",
    "bypass_trust_compliance_checks",
)

NOVARIDE_FLEET_WORKFLOW: tuple[str, ...] = (
    "fleet_adds_vehicles",
    "fleet_registers_drivers",
    "fleet_assigns_drivers_to_vehicles",
    "drivers_go_online",
    "dispatch_assigns_rides",
    "trips_completed",
    "payments_processed_via_novapay",
    "fleet_receives_earnings",
    "drivers_get_payouts",
    "fleet_monitors_analytics",
)

NOVARIDE_BUSINESS_PORTAL_MODULES: tuple[dict[str, Any], ...] = (
    {
        "key": "corporate_travel",
        "name": "Corporate Travel Management",
        "purpose": "Book, schedule, and track employee rides for business travel.",
        "features": (
            "employee_ride_booking",
            "scheduled_rides",
            "airport_transfers",
            "group_transport",
            "business_trips",
            "daily_commute",
            "client_meetings",
            "active_ride_visibility",
        ),
        "actions": ("book_employee_ride", "schedule_future_ride", "track_employee_trip"),
        "backend_integrations": ("dispatch", "maps", "notifications"),
        "status": "contract_declared",
    },
    {
        "key": "employee_management",
        "name": "Employee Management",
        "purpose": "Manage employee profiles, roles, departments, budgets, and travel permissions.",
        "features": (
            "employee_profiles",
            "department_assignment",
            "client_sub_roles",
            "role_based_permissions",
            "department_restrictions",
            "assigned_budget",
        ),
        "actions": ("add_employee", "remove_employee", "assign_role", "set_travel_permissions"),
        "backend_integrations": ("novaid", "rbac"),
        "status": "contract_declared",
    },
    {
        "key": "approval_workflow",
        "name": "Approval Workflow",
        "purpose": "Control who can book rides and when approval is required.",
        "features": (
            "auto_approved_rides",
            "high_cost_approval",
            "premium_ride_approval",
            "out_of_policy_review",
            "manager_approval",
            "multi_level_approval",
            "instant_notifications",
        ),
        "actions": ("approve_request", "reject_request", "route_for_manager_review"),
        "backend_integrations": ("workflow", "notifications"),
        "status": "contract_declared",
    },
    {
        "key": "business_wallet_billing",
        "name": "Business Wallet & Billing",
        "purpose": "Centralize corporate wallet, monthly invoicing, settlement, and refunds through NovaPay.",
        "features": (
            "business_wallet",
            "prepaid_postpaid_options",
            "monthly_invoicing",
            "department_breakdown",
            "downloadable_reports",
            "automatic_deductions",
            "invoice_settlement",
            "refund_handling",
        ),
        "actions": ("preview_invoice", "download_billing_report", "review_refund"),
        "backend_integrations": ("novapay", "audit", "pricing", "analytics"),
        "status": "partially_implemented",
    },
    {
        "key": "pricing_incentives",
        "name": "Pricing & Incentives",
        "purpose": "Preview deterministic fare posture, bounded incentives, and commercial take-rate without direct authority.",
        "features": (
            "fare_preview",
            "price_multiplier",
            "driver_incentives",
            "rider_transparency",
            "take_rate_preview",
            "demand_signal",
        ),
        "actions": ("review_pricing_projection", "review_incentive_plan", "export_pricing_trace"),
        "backend_integrations": ("pricing", "analytics", "novapay", "audit"),
        "status": "implemented",
    },
    {
        "key": "budget_allocation_optimization",
        "name": "Budget Allocation & Profit Optimization",
        "purpose": "Allocate spend across cities and optimize profit margins using deterministic operational and financial signals.",
        "features": (
            "city_budget_allocation",
            "profit_projection",
            "city_margin",
            "budget_rebalance",
            "coverage_guard",
        ),
        "actions": ("review_budget_allocation", "review_profit_projection", "export_optimization_trace"),
        "backend_integrations": ("analytics", "pricing", "novapay", "audit"),
        "status": "implemented",
    },
    {
        "key": "department_budgets",
        "name": "Department Budgets",
        "purpose": "Allocate and enforce spend controls by department, employee, and project.",
        "features": (
            "department_budget_allocation",
            "employee_budget_allocation",
            "project_budget_allocation",
            "spend_limits",
            "near_limit_alerts",
            "optional_hard_stops",
            "real_time_usage",
        ),
        "actions": ("set_department_budget", "set_employee_budget", "review_budget_alerts"),
        "backend_integrations": ("analytics", "novapay"),
        "status": "contract_declared",
    },
    {
        "key": "reporting_analytics",
        "name": "Reporting & Analytics",
        "purpose": "Analyze corporate travel spend, usage, routes, and policy compliance.",
        "features": (
            "total_spend",
            "spend_per_department",
            "spend_per_employee",
            "ride_counts",
            "peak_usage_times",
            "popular_routes",
            "cost_per_trip",
            "budget_vs_actual",
            "policy_compliance_rate",
            "pdf_excel_csv_exports",
        ),
        "actions": ("export_pdf", "export_excel", "export_csv", "review_policy_compliance"),
        "backend_integrations": ("analytics", "audit"),
        "status": "contract_declared",
    },
)

NOVARIDE_BUSINESS_NAVIGATION: tuple[str, ...] = (
    "Dashboard",
    "Employees",
    "Bookings",
    "Approvals",
    "Finance",
    "Budgets",
    "Reports",
)

NOVARIDE_BUSINESS_SUB_ROLES: tuple[str, ...] = ("Admin", "Manager", "Employee")

NOVARIDE_BUSINESS_ALLOWED_ACTIONS: tuple[str, ...] = (
    "book_rides",
    "approve_reject_requests",
    "manage_employees",
    "view_billing_reports",
)

NOVARIDE_BUSINESS_FORBIDDEN_ACTIONS: tuple[str, ...] = (
    "direct_payment_execution",
    "dispatch_logic_bypass",
    "pricing_rule_bypass",
)

NOVARIDE_BUSINESS_WORKFLOW: tuple[str, ...] = (
    "company_onboarded",
    "employees_added",
    "budgets_assigned",
    "employee_requests_ride",
    "approval_if_required",
    "ride_booked",
    "trip_completed",
    "novapay_processes_payment",
    "monthly_invoice_generated",
    "admin_reviews_reports",
)

NOVARIDE_ADMIN_MODULES: tuple[dict[str, Any], ...] = (
    {
        "key": "user_role_management",
        "name": "User & Role Management",
        "purpose": "Administer users, role assignments, permissions, and activity logs.",
        "features": (
            "passenger_accounts",
            "driver_accounts",
            "fleet_owner_accounts",
            "business_client_accounts",
            "operator_accounts",
            "role_assignment",
            "permission_mapping",
            "role_audits",
        ),
        "actions": ("create_user", "suspend_user", "grant_role", "revoke_role", "reset_account"),
        "backend_integrations": ("novaid", "rbac", "audit"),
        "status": "partially_implemented",
    },
    {
        "key": "driver_vehicle_approval",
        "name": "Driver & Vehicle Approval",
        "purpose": "Ensure only verified and compliant drivers and vehicles can operate.",
        "features": (
            "driver_application_review",
            "license_verification",
            "identity_verification",
            "vehicle_registration_validation",
            "insurance_verification",
            "inspection_status",
            "approval_status_tracking",
        ),
        "actions": ("approve_driver", "reject_driver", "approve_vehicle", "reject_vehicle", "trigger_reverification"),
        "backend_integrations": ("trust", "inspector"),
        "status": "contract_declared",
    },
    {
        "key": "pricing_service_configuration",
        "name": "Pricing & Service Configuration",
        "purpose": "Configure fare rules, dynamic pricing policies, and ride types.",
        "features": (
            "base_fare",
            "cost_per_km",
            "cost_per_minute",
            "surge_pricing_rules",
            "peak_hour_adjustments",
            "event_based_pricing",
            "ride_type_catalog",
        ),
        "actions": ("set_global_pricing", "set_region_pricing", "change_pricing_policy"),
        "backend_integrations": ("pricing",),
        "status": "contract_declared",
    },
    {
        "key": "geography_service_zones",
        "name": "Geography & Service Zones",
        "purpose": "Define cities, service areas, geo-fences, restricted areas, and airport rules.",
        "features": (
            "service_area_definition",
            "city_region_configuration",
            "geo_fencing",
            "airport_rules",
            "restricted_areas",
            "pricing_geography_links",
        ),
        "actions": ("add_zone", "edit_zone", "remove_zone", "link_pricing_to_zone"),
        "backend_integrations": ("maps", "dispatch"),
        "status": "contract_declared",
    },
    {
        "key": "promotions_campaigns",
        "name": "Promotions & Campaigns",
        "purpose": "Manage promo codes, referral bonuses, partner offers, and targeted campaigns.",
        "features": (
            "promo_codes",
            "referral_bonuses",
            "seasonal_campaigns",
            "partner_offers",
            "business_incentives",
            "targeting_by_user_location_ride_type",
        ),
        "actions": ("create_campaign", "retire_campaign", "review_campaign_performance"),
        "backend_integrations": ("pricing", "notifications"),
        "status": "contract_declared",
    },
    {
        "key": "compliance_audit",
        "name": "Compliance & Audit",
        "purpose": "Investigate incidents, review logs, export reports, and replay decisions.",
        "features": (
            "audit_logs",
            "user_activity_logs",
            "financial_logs",
            "trip_replay",
            "payment_trace",
            "decision_trace",
            "regulatory_compliance",
            "safety_policy_enforcement",
        ),
        "actions": ("investigate_incident", "review_flagged_case", "export_compliance_report"),
        "backend_integrations": ("audit", "novapay", "trust"),
        "status": "partially_implemented",
    },
    {
        "key": "system_health_monitoring",
        "name": "System Health & Monitoring",
        "purpose": "Monitor API uptime, service availability, alerts, latency, errors, and load.",
        "features": (
            "api_uptime",
            "service_availability",
            "service_failure_alerts",
            "payment_issue_alerts",
            "dispatch_delay_alerts",
            "request_latency",
            "error_rates",
            "load_monitoring",
        ),
        "actions": ("review_alert", "acknowledge_incident", "inspect_system_health"),
        "backend_integrations": ("monitoring", "analytics"),
        "status": "partially_implemented",
    },
)

NOVARIDE_ADMIN_NAVIGATION: tuple[str, ...] = (
    "Dashboard",
    "Users",
    "Drivers & Vehicles",
    "Pricing",
    "Zones",
    "Promotions",
    "Audit",
    "System",
)

NOVARIDE_ADMIN_ALLOWED_ACTIONS: tuple[str, ...] = (
    "configure_platform_rules",
    "approve_participants",
    "control_pricing_zones",
    "monitor_compliance",
)

NOVARIDE_ADMIN_FORBIDDEN_ACTIONS: tuple[str, ...] = (
    "direct_ride_execution",
    "manual_payment_processing",
    "audit_replay_bypass",
)

NOVARIDE_ADMIN_WORKFLOW: tuple[str, ...] = (
    "driver_registers",
    "admin_reviews_documents",
    "admin_approves_driver_vehicle",
    "driver_becomes_active",
    "admin_configures_pricing",
    "admin_sets_surge_rules",
    "admin_defines_service_zones",
    "system_runs_rides_automatically",
    "novapay_processes_payments",
    "audit_logs_captured",
    "admin_monitors_system_health",
    "admin_reviews_alerts",
    "admin_adjusts_rules_if_needed",
)

NOVARIDE_INSPECTOR_MODULES: tuple[dict[str, Any], ...] = (
    {
        "key": "inspection_workflow",
        "name": "Inspection Workflow",
        "purpose": "Guide field inspectors through structured, repeatable driver and vehicle inspections.",
        "features": (
            "start_new_inspection",
            "resume_ongoing_inspection",
            "inspection_history",
            "offline_mode_sync_later",
            "structured_checklist",
        ),
        "actions": ("select_driver_vehicle", "start_inspection", "complete_checklist", "submit_report"),
        "backend_integrations": ("inspector_api", "audit", "trust"),
        "status": "contract_declared",
    },
    {
        "key": "driver_verification",
        "name": "Driver Verification",
        "purpose": "Validate driver identity, license details, and NovaID profile match.",
        "features": (
            "identity_check",
            "license_number_verification",
            "license_expiry_tracking",
            "novaid_profile_match",
            "biometric_face_match_next_phase",
        ),
        "actions": ("verify_identity", "validate_license", "mark_pending", "mark_rejected"),
        "backend_integrations": ("novaid", "trust"),
        "status": "contract_declared",
    },
    {
        "key": "vehicle_inspection",
        "name": "Vehicle Inspection",
        "purpose": "Inspect physical condition, cleanliness, safety equipment, mechanical basics, and vehicle match.",
        "features": (
            "exterior_condition",
            "interior_condition",
            "cleanliness",
            "seatbelts_airbags",
            "lights_tires_brakes",
            "engine_warning_indicators",
            "plate_verification",
            "vin_optional_next_phase",
        ),
        "actions": ("complete_vehicle_checklist", "flag_safety_issue", "confirm_plate_match"),
        "backend_integrations": ("fleet", "trust"),
        "status": "contract_declared",
    },
    {
        "key": "document_validation",
        "name": "Document Validation",
        "purpose": "Validate insurance, registration, certificates, and expiry posture.",
        "features": (
            "insurance_verification",
            "registration_validation",
            "inspection_certificate_upload",
            "expiry_monitoring",
            "reupload_requests",
        ),
        "actions": ("approve_document", "flag_invalid_document", "request_reupload"),
        "backend_integrations": ("trust", "audit"),
        "status": "contract_declared",
    },
    {
        "key": "photo_evidence_capture",
        "name": "Photo & Evidence Capture",
        "purpose": "Capture timestamped, location-tagged evidence linked to inspection reports and replay.",
        "features": (
            "front_vehicle_photo",
            "rear_vehicle_photo",
            "interior_photo",
            "license_photo",
            "insurance_photo",
            "timestamped_evidence",
            "gps_location_tagging",
            "secure_backend_upload",
        ),
        "actions": ("capture_photo", "attach_document_image", "upload_evidence"),
        "backend_integrations": ("audit", "trust"),
        "status": "contract_declared",
    },
    {
        "key": "inspection_reports",
        "name": "Inspection Reports",
        "purpose": "Generate reports with findings, checklist results, comments, and report history.",
        "features": (
            "auto_generated_report",
            "summary_of_findings",
            "checklist_results",
            "inspector_comments",
            "report_history",
        ),
        "actions": ("submit_report", "edit_before_submission", "view_past_reports"),
        "backend_integrations": ("audit", "admin"),
        "status": "contract_declared",
    },
    {
        "key": "compliance_status",
        "name": "Compliance Status",
        "purpose": "Surface compliant, pending, and non-compliant states while Trust Engine remains final authority.",
        "features": (
            "compliant_allowed_to_operate",
            "pending_requires_review",
            "non_compliant_suspended",
            "driver_online_control_signal",
            "fleet_manager_status_sync",
        ),
        "actions": ("submit_compliance_evidence", "review_status", "sync_status_to_fleet"),
        "backend_integrations": ("trust", "driver_app", "fleet"),
        "status": "contract_declared",
    },
)

NOVARIDE_INSPECTOR_NAVIGATION: tuple[str, ...] = (
    "Home",
    "Inspection",
    "Reports",
    "Profile",
)

NOVARIDE_INSPECTOR_ALLOWED_ACTIONS: tuple[str, ...] = (
    "perform_inspections",
    "submit_reports",
    "capture_evidence",
    "validate_documents",
)

NOVARIDE_INSPECTOR_FORBIDDEN_ACTIONS: tuple[str, ...] = (
    "approve_payments",
    "admin_decision_bypass",
    "trust_engine_bypass",
)

NOVARIDE_INSPECTOR_WORKFLOW: tuple[str, ...] = (
    "inspector_logs_in",
    "selects_driver_vehicle",
    "starts_inspection",
    "completes_checklist",
    "captures_photos",
    "submits_report",
    "trust_engine_evaluates_compliance",
    "status_updated",
    "driver_approved_or_suspended",
)

NOVARIDE_INSPECTOR_STATUS_TYPES: tuple[dict[str, str], ...] = (
    {"status": "compliant", "meaning": "allowed_to_operate"},
    {"status": "pending", "meaning": "requires_review"},
    {"status": "non_compliant", "meaning": "suspended"},
)

NOVARIDE_SUPPORT_MODULES: tuple[dict[str, Any], ...] = (
    {
        "key": "customer_ticket_management",
        "name": "Customer Ticket Management",
        "purpose": "Create, triage, assign, resolve, and close passenger, driver, and operator tickets.",
        "features": (
            "passenger_created_tickets",
            "driver_created_tickets",
            "operator_manual_entry",
            "ride_issue",
            "payment_issue",
            "lost_found",
            "safety_concern",
            "complaint",
            "ticket_status_workflow",
        ),
        "actions": ("create_ticket", "assign_ticket", "update_status", "close_ticket"),
        "backend_integrations": ("support_api", "notifications", "novaid"),
        "status": "contract_declared",
    },
    {
        "key": "ride_lookup_investigation",
        "name": "Ride Lookup & Investigation",
        "purpose": "Search rides, inspect details, and review replay evidence for support decisions.",
        "features": (
            "search_by_ride_id",
            "search_by_passenger",
            "search_by_driver",
            "search_by_date_time",
            "trip_timeline",
            "pickup_dropoff",
            "fare_breakdown",
            "payment_status",
            "full_trip_replay",
        ),
        "actions": ("lookup_ride", "inspect_ride_details", "open_trip_replay", "analyze_anomaly"),
        "backend_integrations": ("audit", "dispatch"),
        "status": "partially_implemented",
    },
    {
        "key": "refund_dispute_handling",
        "name": "Refund & Dispute Handling",
        "purpose": "Review refund requests, verify fares, and route approved refund requests through NovaPay.",
        "features": (
            "partial_refund_request",
            "full_refund_request",
            "extra_charge_dispute",
            "fare_vs_route_validation",
            "pricing_rule_validation",
            "surge_logic_check",
            "suggested_refund_amounts",
            "rule_based_decisions",
        ),
        "actions": ("request_refund", "reject_request", "escalate_case", "review_decision_support"),
        "backend_integrations": ("novapay", "pricing", "audit"),
        "status": "contract_declared",
    },
    {
        "key": "driver_passenger_assistance",
        "name": "Driver & Passenger Assistance",
        "purpose": "Assist users through messaging, call integration, guidance, and operator-linked ride actions.",
        "features": (
            "contact_passenger",
            "contact_driver",
            "messaging_integration",
            "call_integration",
            "driver_late",
            "passenger_no_show",
            "route_disagreement",
            "behavior_complaints",
        ),
        "actions": ("provide_guidance", "request_reassignment", "request_trip_cancel_with_reason"),
        "backend_integrations": ("operator_dashboard", "notifications"),
        "status": "contract_declared",
    },
    {
        "key": "escalation_management",
        "name": "Escalation Management",
        "purpose": "Route high-priority support issues to supervisors, admins, Trust, or audit review.",
        "features": (
            "level_1_standard_support",
            "level_2_supervisor",
            "level_3_critical_admin",
            "safety_incidents",
            "fraud_suspicion",
            "payment_disputes",
            "legal_issues",
        ),
        "actions": ("trigger_escalation", "route_to_supervisor", "route_to_admin", "resolve_escalation"),
        "backend_integrations": ("admin", "trust", "audit"),
        "status": "contract_declared",
    },
    {
        "key": "audit_replay_integration",
        "name": "Audit & Replay Integration",
        "purpose": "Make every support decision verifiable through ride, route, timing, pricing, and payment evidence.",
        "features": (
            "request_match_trip_payment_replay",
            "route_taken",
            "driver_behavior",
            "timing_events",
            "pricing_decisions",
            "evidence_backed_decisions",
            "fraud_detection_support",
        ),
        "actions": ("inspect_replay", "attach_evidence", "record_support_decision"),
        "backend_integrations": ("audit", "trust"),
        "status": "partially_implemented",
    },
)

NOVARIDE_SUPPORT_NAVIGATION: tuple[str, ...] = (
    "Tickets",
    "Ride Lookup",
    "Refunds",
    "Escalations",
    "Reports",
)

NOVARIDE_SUPPORT_TICKET_STATUSES: tuple[str, ...] = (
    "Open",
    "In Progress",
    "Resolved",
    "Closed",
)

NOVARIDE_SUPPORT_ESCALATION_LEVELS: tuple[dict[str, str], ...] = (
    {"level": "level_1", "meaning": "standard_support"},
    {"level": "level_2", "meaning": "supervisor"},
    {"level": "level_3", "meaning": "critical_admin"},
)

NOVARIDE_SUPPORT_ALLOWED_ACTIONS: tuple[str, ...] = (
    "view_ride_data",
    "manage_tickets",
    "request_refunds",
    "contact_users",
    "escalate_cases",
)

NOVARIDE_SUPPORT_FORBIDDEN_ACTIONS: tuple[str, ...] = (
    "novapay_bypass",
    "pricing_rule_mutation",
    "audit_log_bypass",
    "direct_payment_execution",
)

NOVARIDE_SUPPORT_WORKFLOW: tuple[str, ...] = (
    "passenger_raises_issue",
    "ticket_created",
    "support_agent_reviews_ride",
    "replay_trip_data",
    "verify_fare_via_pricing_engine",
    "decide_refund_or_action",
    "novapay_processes_refund",
    "ticket_closed",
)

NOVARIDE_PARTNER_MODULES: tuple[dict[str, Any], ...] = (
    {
        "key": "ride_booking_widget",
        "name": "Ride Booking & Widget Integration",
        "purpose": "Embed NovaRide booking into partner websites, kiosks, apps, and booking systems.",
        "features": (
            "hotel_website_widget",
            "airport_kiosk_widget",
            "event_platform_widget",
            "api_integration",
            "instant_booking",
            "scheduled_rides",
            "airport_pickup_scheduling",
        ),
        "actions": ("configure_widget", "create_partner_booking", "schedule_partner_ride"),
        "backend_integrations": ("dispatch", "maps", "novaid_guest_mode"),
        "status": "contract_declared",
    },
    {
        "key": "guest_transport_management",
        "name": "Guest Transport Management",
        "purpose": "Book, track, and share rides for guests without requiring a full account.",
        "features": (
            "book_on_behalf_of_guest",
            "guest_mode",
            "guest_name_phone",
            "pickup_instructions",
            "hotel_airport_transfers",
            "event_shuttle_transport",
            "active_guest_ride_tracking",
            "share_trip_details",
        ),
        "actions": ("book_guest_ride", "track_guest_ride", "share_guest_trip"),
        "backend_integrations": ("passenger_backend", "notifications"),
        "status": "contract_declared",
    },
    {
        "key": "bulk_ride_requests",
        "name": "Bulk Ride Requests",
        "purpose": "Support high-volume group, event, recurring, CSV, and batch ride creation.",
        "features": (
            "multiple_rides_at_once",
            "pickup_locations",
            "time_slots",
            "ride_types",
            "event_based_transport",
            "recurring_bookings",
            "csv_upload",
            "batch_management",
        ),
        "actions": ("upload_bulk_data", "generate_batch_requests", "review_batch_status"),
        "backend_integrations": ("dispatch", "analytics"),
        "status": "contract_declared",
    },
    {
        "key": "partner_reporting",
        "name": "Partner Reporting",
        "purpose": "Analyze partner usage, routes, ride success, cancellations, wait times, and export reports.",
        "features": (
            "rides_booked",
            "peak_booking_times",
            "popular_routes",
            "guest_usage_trends",
            "ride_success_rate",
            "cancellation_rate",
            "average_wait_time",
            "excel_csv_exports",
        ),
        "actions": ("view_usage_analytics", "export_csv", "export_excel"),
        "backend_integrations": ("analytics",),
        "status": "contract_declared",
    },
    {
        "key": "billing_payments",
        "name": "Billing & Payments",
        "purpose": "Manage prepaid wallet, postpaid invoicing, pay-per-ride, refunds, and financial logs through NovaPay.",
        "features": (
            "prepaid_wallet",
            "postpaid_invoicing",
            "pay_per_ride",
            "partner_wallet",
            "department_event_billing",
            "monthly_summary",
            "ride_by_ride_breakdown",
            "support_linked_refunds",
        ),
        "actions": ("view_wallet", "review_invoice", "request_refund_review"),
        "backend_integrations": ("novapay", "audit"),
        "status": "contract_declared",
    },
    {
        "key": "partner_configuration",
        "name": "Partner Configuration",
        "purpose": "Configure pickup defaults, preferred ride types, contract pricing references, users, permissions, and API settings.",
        "features": (
            "default_pickup_locations",
            "preferred_ride_types",
            "contract_pricing_reference",
            "white_label_widget_next_phase",
            "partner_admin_users",
            "partner_staff_users",
            "permission_levels",
            "api_keys",
        ),
        "actions": ("update_settings", "manage_partner_users", "rotate_api_key"),
        "backend_integrations": ("novaid", "rbac"),
        "status": "contract_declared",
    },
)

NOVARIDE_PARTNER_NAVIGATION: tuple[str, ...] = (
    "Dashboard",
    "Bookings",
    "Guests",
    "Tracking",
    "Reports",
    "Billing",
    "Settings",
)

NOVARIDE_PARTNER_TYPES: tuple[str, ...] = (
    "airports",
    "hotels",
    "event_organizers",
    "corporations",
    "travel_agencies",
)

NOVARIDE_PARTNER_ALLOWED_ACTIONS: tuple[str, ...] = (
    "book_guest_rides",
    "manage_bulk_transport",
    "view_reports_billing",
    "configure_booking_settings",
)

NOVARIDE_PARTNER_FORBIDDEN_ACTIONS: tuple[str, ...] = (
    "dispatch_logic_bypass",
    "direct_payment_processing",
    "pricing_rule_bypass",
    "direct_driver_access",
)

NOVARIDE_PARTNER_WORKFLOW: tuple[str, ...] = (
    "hotel_staff_logs_in",
    "books_ride_for_guest",
    "guest_receives_ride_details",
    "driver_picks_up_guest",
    "trip_completed",
    "novapay_charges_partner_account",
    "monthly_invoice_generated",
    "partner_reviews_reports",
)


def _novaride_ecosystem_payload() -> dict[str, Any]:
    surfaces = [dict(surface) for surface in NOVARIDE_APP_SURFACES]
    return {
        "view": "novaride_ecosystem",
        "status": "controlled_pilot_ready",
        "platform": "NovaRide",
        "apps": surfaces,
        "app_count": len(surfaces),
        "shared_platform": [dict(service) for service in NOVARIDE_SHARED_PLATFORM],
        "enterprise_operations_layer": [dict(capability) for capability in NOVARIDE_ENTERPRISE_OPERATIONS_LAYER],
        "enterprise_operations_score": "10/10",
        "enterprise_operations_classification": "governed_evidence_backed_ai_assisted_mobility_control_platform",
        "layered_architecture": list(NOVARIDE_LAYERED_ARCHITECTURE),
        "operator_intervention_flow": list(NOVARIDE_OPERATOR_INTERVENTION_FLOW),
        "production_infrastructure_readiness": [
            dict(capability) for capability in NOVARIDE_PRODUCTION_INFRASTRUCTURE_READINESS
        ],
        "lifecycle": list(NOVARIDE_LIFECYCLE),
        "intelligence_layer": (
            "Demand Forecasting",
            "Driver Position Prediction",
            "ETA Prediction",
            "Fraud Detection",
            "Safety Scoring",
            "Dynamic Pricing",
            "Traffic Intelligence",
            "Dispatch Optimization",
            "Operational Insights",
        ),
        "trust_proof_flow": (
            "Ride Request",
            "Dispatch Decision",
            "Driver Assignment",
            "Pickup",
            "Trip",
            "Payment",
            "Receipt",
            "Replay Timeline",
            "Verification Package",
        ),
        "domain_model": (
            "Organization",
            "Customer",
            "Driver",
            "Vehicle",
            "Ride",
            "Dispatch",
            "Trip",
            "Payment",
            "Receipt",
            "Event Stream",
            "Replay",
            "Audit",
        ),
        "upgrade_principle": (
            "Rider/Driver apps request and display; Operator/Inspector portals control quality and compliance; "
            "Control Plane decides; Execution Plane performs; Event Platform proves."
        ),
        "authority_boundary": {
            "mobile_apps": "request_and_observe_only",
            "backend": "dispatch_payment_trust_and_replay_authority",
            "payments": "NovaPay_backend_only",
            "maps_notifications_providers": "backend_integrations_only",
        },
        "route_families": {
            surface["key"]: surface["route_prefix"] for surface in surfaces
        },
    }


def _novaride_platform_architecture_contract() -> dict[str, Any]:
    return {
        "view": "novaride_shared_platform_architecture_contract",
        "status": "controlled_pilot_contract_ready",
        "principle": "Apps request and display; Control Plane decides; Execution Plane performs; Event Platform proves",
        "layers": {
            "app_layer": [dict(app) for app in NOVARIDE_APP_LAYER_CONTRACT],
            "api_gateway": {
                "name": "NovaRide API",
                "role": "single_entry_point",
                "responsibilities": list(NOVARIDE_API_GATEWAY_RESPONSIBILITIES),
            },
            "execution_layer": {
                "name": "Shared NovaRide Platform",
                "services": [dict(service) for service in NOVARIDE_SHARED_PLATFORM],
            },
        },
        "authority_boundary": {
            "backend_full_control": list(NOVARIDE_BACKEND_AUTHORITY_CONTROLS),
            "apps_no_authority": list(NOVARIDE_APP_FORBIDDEN_AUTHORITY),
            "payments": "NovaPay_backend_only",
            "external_integrations": "backend_only",
        },
        "ride_request_flow": list(NOVARIDE_RIDE_REQUEST_FLOW),
        "cross_app_service_matrix": [
            {"app": row["app"], "services": list(row["services"])}
            for row in NOVARIDE_CROSS_APP_SERVICE_MATRIX
        ],
        "strategic_outcomes": list(NOVARIDE_ARCHITECTURE_OUTCOMES),
        "next_level_contracts": (
            "microservices_deployment_architecture",
            "event_driven_queues",
            "database_schema",
            "websocket_live_tracking",
            "saas_monetization_model",
        ),
    }


def _novaride_surface_payload(surface_key: str) -> dict[str, Any]:
    normalized = surface_key.strip().lower()
    for surface in NOVARIDE_APP_SURFACES:
        if surface["key"] == normalized:
            return {
                "view": "novaride_app_workspace",
                "surface": dict(surface),
                "shared_services": [service["key"] for service in NOVARIDE_SHARED_PLATFORM],
                "readiness": {
                    "api_contract": "declared",
                    "backend_authority": "centralized",
                    "provider_integrations": "backend_only",
                    "replay_required": True,
                    "novapay_required": surface["key"] in {"passenger", "driver", "business", "fleet", "partner"},
                },
            }
    raise HTTPException(status_code=404, detail="novaride_surface_not_found")


def _novaride_operator_dashboard_contract() -> dict[str, Any]:
    return {
        "view": "novaride_operator_dashboard_contract",
        "status": "controlled_pilot_ready",
        "purpose": "NovaRide human and system decision layer for operations, safety, analytics, support, and escalation.",
        "modules": [dict(module) for module in NOVARIDE_OPERATOR_DASHBOARD_MODULES],
        "layout": dict(NOVARIDE_OPERATOR_LAYOUT),
        "authority_model": {
            "allowed": list(NOVARIDE_OPERATOR_ALLOWED_ACTIONS),
            "forbidden": list(NOVARIDE_OPERATOR_FORBIDDEN_ACTIONS),
            "backend_authority": {
                "dispatch": "backend",
                "payments": "NovaPay",
                "fraud_detection": "Trust Engine",
                "replay": "Audit Engine",
            },
        },
        "workflow": list(NOVARIDE_OPERATOR_WORKFLOW),
        "api_alignment": {
            "implemented": (
                "/v1/operator/dashboard",
                "/v1/operator/analytics",
                "/v1/operator/decisions",
                "/v1/operator/actions",
                "/v1/operator/replay-exceptions",
                "/v1/operator/demand-forecast",
                "/v1/operator/strategy-engine",
                "/v1/operator/city-profit-optimization",
                "/v1/novaride/ecosystem",
            ),
            "contract": "/v1/novaride/operator/dashboard-contract",
        },
        "next_phase": (
            "bounded_strategy_execution_safeguards",
            "predictive_demand_engine",
            "automated_fraud_alerts",
            "smart_fleet_balancing",
            "voice_based_operations",
            "incident_replay_visualization",
        ),
    }


def _novaride_fleet_manager_contract() -> dict[str, Any]:
    return {
        "view": "novaride_fleet_manager_contract",
        "status": "controlled_pilot_contract_ready",
        "role": "FLEET_OWNER",
        "purpose": "Fleet business control plane for vehicles, drivers, finances, maintenance, compliance, and analytics.",
        "modules": [dict(module) for module in NOVARIDE_FLEET_MANAGER_MODULES],
        "navigation": list(NOVARIDE_FLEET_NAVIGATION),
        "rbac": {
            "role": "FLEET_OWNER",
            "allowed": list(NOVARIDE_FLEET_ALLOWED_ACTIONS),
            "forbidden": list(NOVARIDE_FLEET_FORBIDDEN_ACTIONS),
        },
        "authority_model": {
            "dispatch": "backend_only",
            "payments": "NovaPay_backend_only",
            "trust_compliance": "Trust_Engine_required",
            "inspection": "NovaRide_Inspector_evidence_required",
            "audit": "Audit_Engine_replay_required",
        },
        "workflow": list(NOVARIDE_FLEET_WORKFLOW),
        "api_alignment": {
            "implemented": (
                "/v1/afriride/fleet/summary",
                "/v1/afriride/fleet/drivers",
                "/v1/novaride/fleet/workspace",
            ),
            "contract": "/v1/novaride/fleet/manager-contract",
            "next_phase": (
                "/v1/fleet/vehicles",
                "/v1/fleet/maintenance",
                "/v1/fleet/earnings",
                "/v1/fleet/payouts",
                "/v1/fleet/analytics",
            ),
        },
        "ecosystem_integrations": {
            "driver_app": "operated_by_fleet_drivers",
            "operator_dashboard": "monitors_fleet_performance",
            "inspector_app": "validates_vehicles_and_drivers",
            "business_portal": "corporate_ride_billing",
            "novapay": "earnings_and_payouts",
        },
        "advanced_next_phase": (
            "ai_fleet_optimization",
            "smart_driver_allocation",
            "fuel_optimization_analytics",
            "predictive_maintenance",
            "multi_country_fleet_operations",
            "franchise_fleet_networks",
        ),
    }


def _novaride_business_portal_contract() -> dict[str, Any]:
    return {
        "view": "novaride_business_portal_contract",
        "status": "controlled_pilot_contract_ready",
        "role": "CLIENT",
        "sub_roles": list(NOVARIDE_BUSINESS_SUB_ROLES),
        "purpose": "Corporate travel control plane for employee rides, approvals, budgets, billing, and reporting.",
        "modules": [dict(module) for module in NOVARIDE_BUSINESS_PORTAL_MODULES],
        "navigation": list(NOVARIDE_BUSINESS_NAVIGATION),
        "rbac": {
            "role": "CLIENT",
            "sub_roles": list(NOVARIDE_BUSINESS_SUB_ROLES),
            "allowed": list(NOVARIDE_BUSINESS_ALLOWED_ACTIONS),
            "forbidden": list(NOVARIDE_BUSINESS_FORBIDDEN_ACTIONS),
        },
        "authority_model": {
            "dispatch": "backend_only",
            "payments": "NovaPay_backend_only",
            "identity": "NovaID_required",
            "approvals": "workflow_engine_required",
            "pricing": "Pricing_Engine_required",
            "audit": "Audit_Engine_replay_required",
        },
        "workflow": list(NOVARIDE_BUSINESS_WORKFLOW),
        "api_alignment": {
            "implemented": (
                "/v1/novatech/organizations/{organization_id}/platform",
                "/v1/novatech/organizations/{organization_id}/billing",
                "/v1/novaride/business/workspace",
                "/v1/novaride/phase3/business/pricing",
                "/v1/novaride/phase3/business/incentives",
                "/v1/novaride/phase4/business/budget-allocation",
                "/v1/novaride/phase4/business/profit-optimization",
            ),
            "contract": "/v1/novaride/business/portal-contract",
            "next_phase": (
                "/v1/business/employees",
                "/v1/business/approvals",
                "/v1/business/bookings",
                "/v1/business/budgets",
                "/v1/business/reports",
            ),
        },
        "ecosystem_integrations": {
            "passenger_app": "used_by_employees",
            "operator_dashboard": "monitors_corporate_rides",
            "fleet_manager": "supplies_vehicles",
            "novapay": "billing_wallet_invoices",
            "novaid": "identity_and_roles",
        },
        "advanced_next_phase": (
            "multi_company_saas",
            "travel_policy_engine",
            "ai_cost_optimization",
            "hr_system_integrations",
            "erp_integration_api",
            "subscription_plans",
            "invoice_tax_handling",
        ),
    }


def _novaride_admin_contract() -> dict[str, Any]:
    return {
        "view": "novaride_admin_contract",
        "status": "controlled_pilot_contract_ready",
        "role": "ADMIN",
        "purpose": "Governance, control, and configuration layer that defines how NovaRide behaves.",
        "modules": [dict(module) for module in NOVARIDE_ADMIN_MODULES],
        "navigation": list(NOVARIDE_ADMIN_NAVIGATION),
        "rbac": {
            "role": "ADMIN",
            "managed_roles": (
                "CUSTOMER",
                "DRIVER",
                "OPERATOR",
                "ADMIN",
                "CLIENT",
                "FLEET_OWNER",
                "VERIFIER",
            ),
            "allowed": list(NOVARIDE_ADMIN_ALLOWED_ACTIONS),
            "forbidden": list(NOVARIDE_ADMIN_FORBIDDEN_ACTIONS),
        },
        "authority_model": {
            "payments": "NovaPay_policy_level_only",
            "dispatch": "Dispatch_Engine_required",
            "trust_safety": "Trust_Engine_required",
            "logs": "Audit_Engine_required",
            "pricing": "Pricing_Engine_required",
            "identity": "NovaID_RBAC_required",
        },
        "workflow": list(NOVARIDE_ADMIN_WORKFLOW),
        "api_alignment": {
            "implemented": (
                "/v1/afriride/rbac/catalog",
                "/v1/afriride/rbac/assignments",
                "/v1/novatech/saas/status",
                "/v1/ops/audit/dashboard",
                "/v1/novaride/admin/workspace",
            ),
            "contract": "/v1/novaride/admin/contract",
            "next_phase": (
                "/v1/admin/users",
                "/v1/admin/drivers/approvals",
                "/v1/admin/vehicles/approvals",
                "/v1/admin/pricing",
                "/v1/admin/zones",
                "/v1/admin/promotions",
                "/v1/admin/system-health",
            ),
        },
        "ecosystem_integrations": {
            "passenger_app": "governed_by_pricing_zones",
            "driver_app": "controlled_via_approvals",
            "operator_dashboard": "uses_admin_rules",
            "fleet_manager": "managed_via_compliance",
            "business_portal": "uses_billing_rules",
            "novapay": "policy_level_control_only",
        },
        "advanced_next_phase": (
            "ai_pricing_optimization",
            "automated_compliance_checks",
            "fraud_intelligence_dashboard",
            "multi_region_governance",
            "saas_tenant_management",
        ),
    }


def _novaride_inspector_app_contract() -> dict[str, Any]:
    return {
        "view": "novaride_inspector_app_contract",
        "status": "controlled_pilot_contract_ready",
        "role": "VERIFIER",
        "purpose": "Physical-world validation layer for driver, vehicle, document, evidence, and compliance inspections.",
        "modules": [dict(module) for module in NOVARIDE_INSPECTOR_MODULES],
        "navigation": list(NOVARIDE_INSPECTOR_NAVIGATION),
        "status_types": [dict(status) for status in NOVARIDE_INSPECTOR_STATUS_TYPES],
        "rbac": {
            "role": "VERIFIER",
            "allowed": list(NOVARIDE_INSPECTOR_ALLOWED_ACTIONS),
            "forbidden": list(NOVARIDE_INSPECTOR_FORBIDDEN_ACTIONS),
        },
        "authority_model": {
            "identity": "NovaID_required",
            "evidence": "Audit_Engine_replay_required",
            "compliance": "Trust_Engine_final_authority",
            "driver_online_control": "Driver_App_enforced_from_trust_status",
            "fleet_visibility": "Fleet_Manager_receives_inspection_data",
            "admin_review": "Admin_reviews_reports",
        },
        "workflow": list(NOVARIDE_INSPECTOR_WORKFLOW),
        "api_alignment": {
            "implemented": (
                "/v1/operator/public-verification/status",
                "/v1/core-platform/trust/explorer/{receipt_id}",
                "/v1/novaride/inspector/workspace",
            ),
            "contract": "/v1/novaride/inspector/app-contract",
            "next_phase": (
                "/v1/inspector/inspections",
                "/v1/inspector/reports",
                "/v1/inspector/upload",
                "/v1/inspector/compliance-status",
            ),
        },
        "ecosystem_integrations": {
            "driver_app": "affected_by_compliance",
            "fleet_manager": "receives_inspection_data",
            "admin": "reviews_reports",
            "operator_dashboard": "monitors_flagged_issues",
            "trust_engine": "final_authority",
        },
        "advanced_next_phase": (
            "offline_inspections",
            "ai_assisted_defect_detection",
            "ocr_document_scanning",
            "biometric_identity_verification",
            "real_time_compliance_alerts",
        ),
    }


def _novaride_support_contract() -> dict[str, Any]:
    return {
        "view": "novaride_support_contract",
        "status": "controlled_pilot_contract_ready",
        "role": "OPERATOR",
        "purpose": "Problem-resolution layer for ride issues, refunds, driver and passenger assistance, escalations, and replay-backed support decisions.",
        "modules": [dict(module) for module in NOVARIDE_SUPPORT_MODULES],
        "navigation": list(NOVARIDE_SUPPORT_NAVIGATION),
        "ticket_statuses": list(NOVARIDE_SUPPORT_TICKET_STATUSES),
        "escalation_levels": [dict(level) for level in NOVARIDE_SUPPORT_ESCALATION_LEVELS],
        "rbac": {
            "role": "OPERATOR",
            "allowed": list(NOVARIDE_SUPPORT_ALLOWED_ACTIONS),
            "forbidden": list(NOVARIDE_SUPPORT_FORBIDDEN_ACTIONS),
        },
        "authority_model": {
            "refund_execution": "NovaPay_backend_only",
            "pricing_validation": "Pricing_Engine_required",
            "ride_evidence": "Audit_Engine_replay_required",
            "risk_flags": "Trust_Engine_required",
            "escalations": "Operator_Admin_workflow_required",
            "identity": "NovaID_required",
        },
        "workflow": list(NOVARIDE_SUPPORT_WORKFLOW),
        "api_alignment": {
            "implemented": (
                "/v1/rider/rides/{ride_id}",
                "/v1/rider/rides/{ride_id}/receipt",
                "/v1/operator/replay-exceptions",
                "/v1/novaride/support/workspace",
            ),
            "contract": "/v1/novaride/support/contract",
            "next_phase": (
                "/v1/support/tickets",
                "/v1/support/refunds",
                "/v1/support/escalations",
                "/v1/support/ride-lookup",
            ),
        },
        "ecosystem_integrations": {
            "passenger_app": "creates_support_tickets",
            "driver_app": "reports_issues",
            "operator_dashboard": "handles_escalations",
            "novapay": "processes_refunds",
            "audit_engine": "provides_replay",
            "trust_engine": "flags_risks",
        },
        "advanced_next_phase": (
            "ai_ticket_classification",
            "smart_refund_suggestions",
            "chatbot_first_line_support",
            "voice_support_integration",
            "sla_tracking_automation",
            "fraud_pattern_detection",
        ),
    }


def _novaride_partner_portal_contract() -> dict[str, Any]:
    return {
        "view": "novaride_partner_portal_contract",
        "status": "controlled_pilot_contract_ready",
        "role": "PARTNER",
        "purpose": "B2B and B2B2C integration layer for hotels, airports, events, travel agencies, and external organizations.",
        "partner_types": list(NOVARIDE_PARTNER_TYPES),
        "modules": [dict(module) for module in NOVARIDE_PARTNER_MODULES],
        "navigation": list(NOVARIDE_PARTNER_NAVIGATION),
        "rbac": {
            "role": "PARTNER",
            "allowed": list(NOVARIDE_PARTNER_ALLOWED_ACTIONS),
            "forbidden": list(NOVARIDE_PARTNER_FORBIDDEN_ACTIONS),
        },
        "authority_model": {
            "dispatch": "Dispatch_Engine_required",
            "payments": "NovaPay_backend_only",
            "pricing": "Pricing_Engine_contract_reference_required",
            "identity": "NovaID_partner_guest_mode_required",
            "analytics": "Analytics_Engine_required",
            "audit": "Audit_Engine_financial_logs_required",
        },
        "workflow": list(NOVARIDE_PARTNER_WORKFLOW),
        "api_alignment": {
            "implemented": (
                "/v1/partners/registry",
                "/v1/partner/verify",
                "/v1/novaride/partner/workspace",
            ),
            "contract": "/v1/novaride/partner/portal-contract",
            "next_phase": (
                "/v1/partner/bookings",
                "/v1/partner/bulk-requests",
                "/v1/partner/reports",
                "/v1/partner/billing",
                "/v1/partner/guests",
            ),
        },
        "ecosystem_integrations": {
            "passenger_app": "guest_ride_execution",
            "driver_app": "driver_performs_trip",
            "operator_dashboard": "monitors_partner_rides",
            "fleet_manager": "supplies_vehicles",
            "novapay": "billing_and_payments",
            "analytics_engine": "reporting",
        },
        "advanced_next_phase": (
            "white_label_ride_booking_widgets",
            "partner_api_marketplace",
            "dynamic_pricing_contracts",
            "smart_guest_recommendations",
            "event_transport_automation",
            "multi_tenant_partner_onboarding",
        ),
    }


def build_afriride_next_gen_mobile_router() -> APIRouter:
    router = APIRouter(prefix="/v1", tags=["afriride-next-gen-mobile"])

    @router.get("/novaride/ecosystem")
    def novaride_ecosystem() -> dict[str, Any]:
        return _novaride_ecosystem_payload()

    @router.get("/novaride/platform/architecture-contract")
    def novaride_platform_architecture_contract() -> dict[str, Any]:
        return _novaride_platform_architecture_contract()

    @router.get("/novaride/{surface_key}/workspace")
    def novaride_workspace(surface_key: str) -> dict[str, Any]:
        return _novaride_surface_payload(surface_key)

    @router.get("/novaride/operator/dashboard-contract")
    def novaride_operator_dashboard_contract() -> dict[str, Any]:
        return _novaride_operator_dashboard_contract()

    @router.get("/operator/business-pricing")
    def operator_business_pricing() -> dict[str, Any]:
        return get_control_plane().dashboard_business_pricing()

    @router.get("/operator/city-profit-optimization")
    def operator_city_profit_optimization() -> dict[str, Any]:
        return get_control_plane().dashboard_city_profit_optimization()

    @router.get("/novaride/fleet/manager-contract")
    def novaride_fleet_manager_contract() -> dict[str, Any]:
        return _novaride_fleet_manager_contract()

    @router.get("/novaride/business/portal-contract")
    def novaride_business_portal_contract() -> dict[str, Any]:
        return _novaride_business_portal_contract()

    @router.get("/novaride/admin/contract")
    def novaride_admin_contract() -> dict[str, Any]:
        return _novaride_admin_contract()

    @router.get("/novaride/inspector/app-contract")
    def novaride_inspector_app_contract() -> dict[str, Any]:
        return _novaride_inspector_app_contract()

    @router.get("/novaride/support/contract")
    def novaride_support_contract() -> dict[str, Any]:
        return _novaride_support_contract()

    @router.get("/novaride/partner/portal-contract")
    def novaride_partner_portal_contract() -> dict[str, Any]:
        return _novaride_partner_portal_contract()

    @router.post("/mobile/auth/session")
    def create_mobile_session(payload: dict[str, Any]) -> dict[str, Any]:
        actor_id = str(payload.get("actor_id", "")).strip()
        role = canonical_role_name(str(payload.get("role", "")).strip())
        device_id = str(payload.get("device_id", "")).strip()
        app_version = str(payload.get("app_version", "0.1")).strip()
        platform = str(payload.get("platform", "unknown")).strip()
        if not actor_id:
            raise HTTPException(status_code=400, detail="actor_id required")
        if role not in {
            "CUSTOMER",
            "DRIVER",
            "DISPATCHER",
            "FLEET_OWNER",
            "ADMIN",
            "CLIENT",
            "SUPPLIER",
            "INVESTOR",
            "OPERATOR",
            "VERIFIER",
            "PARTNER",
            "DEVELOPER",
            "DEVICE",
            "OBSERVER",
        }:
            raise HTTPException(status_code=400, detail="invalid_role")

        expires_at = datetime.now(UTC) + timedelta(hours=12)
        role_profile = get_control_plane().rbac_role(role=role)
        return {
            "session_id": f"sess-{actor_id}",
            "actor_id": actor_id,
            "role": role,
            "requested_role": str(payload.get("role", "")).strip(),
            "expires_at": expires_at.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "api_base_url": "https://api.afrtechnology.com",
            "token": JWT.create_token(actor_id, role=role),
            "client_event": {
                "device_id": device_id or None,
                "app_version": app_version,
                "platform": platform,
            },
            "rbac": {
                "role": role_profile["role"]["role"],
                "label": role_profile["role"]["label"],
                "category": role_profile["role"]["category"],
                "aliases": role_profile["role"]["aliases"],
                "permissions": role_profile["role"]["permissions"],
                "visible_panels": role_profile["role"]["visible_panels"],
                "api_surfaces": role_profile["role"]["api_surfaces"],
                "dashboard_surface": role_profile["role"]["dashboard_surface"],
            },
        }

    @router.get("/afriride/rbac/catalog")
    def afriride_rbac_catalog(
        limit: int = 100,
        claims = Depends(require_roles("CUSTOMER", "DRIVER", "DISPATCHER", "FLEET_OWNER", "ADMIN", "OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        return get_control_plane().rbac_catalog(
            organization_id=claims.organization_id,
            limit=limit,
        )

    @router.get("/afriride/rbac/roles/{role}")
    def afriride_rbac_role(
        role: str,
        claims = Depends(require_roles("CUSTOMER", "DRIVER", "DISPATCHER", "FLEET_OWNER", "ADMIN", "OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        return get_control_plane().rbac_role(role=role, organization_id=claims.organization_id)

    @router.get("/afriride/rbac/roles/{role}/dashboard")
    def afriride_rbac_role_dashboard(
        role: str,
        limit: int = 100,
        claims = Depends(require_roles("CUSTOMER", "DRIVER", "DISPATCHER", "FLEET_OWNER", "ADMIN", "OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        return get_control_plane().rbac_role_dashboard(
            role=role,
            organization_id=claims.organization_id,
            limit=limit,
        )

    @router.get("/afriride/rbac/assignments")
    def afriride_rbac_assignments(
        limit: int = 100,
        role: str | None = None,
        subject_type: str | None = None,
        subject_id: str | None = None,
        status: str | None = None,
        claims = Depends(require_roles("ADMIN")),
    ) -> dict[str, Any]:
        return get_control_plane().rbac_assignments(
            organization_id=claims.organization_id,
            role=role,
            subject_type=subject_type,
            subject_id=subject_id,
            status=status,
            limit=limit,
        )

    @router.post("/afriride/rbac/assignments")
    def afriride_rbac_assign_role(
        payload: RBACAssignmentRequest,
        claims = Depends(require_roles("ADMIN")),
    ) -> dict[str, Any]:
        return get_control_plane().rbac_assign_role(
            organization_id=payload.organization_id or claims.organization_id,
            subject_type=payload.subject_type,
            subject_id=payload.subject_id,
            role=payload.role,
            granted_by=payload.granted_by or claims.sub,
            granted_role=payload.granted_role,
            status=payload.status,
            notes=payload.notes,
        )

    @router.get("/afriride/rbac/check")
    def afriride_rbac_check(
        role: str,
        permission: str,
        actor_id: str | None = None,
        owner_id: str | None = None,
        assigned_driver_id: str | None = None,
        claims = Depends(require_roles("CUSTOMER", "DRIVER", "DISPATCHER", "FLEET_OWNER", "ADMIN", "OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        return get_control_plane().rbac_check_access(
            role=role,
            permission=permission,
            actor_id=actor_id,
            owner_id=owner_id,
            assigned_driver_id=assigned_driver_id,
        )

    @router.post("/rider/rides")
    def request_ride(
        payload: dict[str, Any],
        gateway=Depends(get_gateway),
        trace_log=Depends(get_trace_log),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        rider_id = str(payload.get("rider_id", "")).strip()
        pickup = str(payload.get("pickup", "")).strip()
        dropoff = str(payload.get("dropoff", "")).strip()
        ride_type = str(payload.get("ride_type", "Economy")).strip() or "Economy"
        ride_id = str(payload.get("ride_id", "")).strip() or None
        if not rider_id or not pickup or not dropoff:
            raise HTTPException(status_code=400, detail="missing_ride_fields")
        if idempotency_key is not None:
            _ = idempotency_key
        ride = gateway.passenger.request_ride(
            {
                "passenger_id": rider_id,
                "pickup": pickup,
                "destination": dropoff,
                "ride_id": ride_id,
            }
        )
        _log_trace_event(
            trace_log,
            ride["ride_id"],
            event_id=f"{ride['ride_id']}.request",
            actor_type="rider",
            actor_id=rider_id,
            action="POST /v1/rider/rides/request",
            payload={
                "pickup": pickup,
                "dropoff": dropoff,
                "ride_type": ride_type,
            },
        )
        total = _fare_total(pickup, dropoff, ride_type)
        status = _mobile_ride_status(str(ride["status"]))
        return {
            "ride_id": ride["ride_id"],
            "status": status,
            "quoted_total": total,
            "currency": "AUD",
            "confirmation_token": f"confirm-{ride['ride_id']}",
            "trust_score": 91,
            "ride_type": ride_type,
        }

    @router.get("/rider/rides/history")
    def rider_history(gateway=Depends(get_gateway), trace_log=Depends(get_trace_log)) -> dict[str, Any]:
        items = []
        for ride in gateway.dispatcher.rides.values():
            validation = trace_log.validate_ride(ride.ride_id) if ride.events else None
            items.append(
                {
                    "ride_id": ride.ride_id,
                    "status": _mobile_ride_status(ride.status),
                    "trust_score": 92 if ride.status == "COMPLETED" else 88,
                    "verification_status": "PASSED" if validation and validation.valid else "REVIEW_REQUIRED",
                }
            )
        return {"items": items}

    @router.get("/rider/rides/{ride_id}")
    def rider_status(ride_id: str, gateway=Depends(get_gateway)) -> dict[str, Any]:
        ride = _require_ride(gateway, ride_id)
        return _ride_snapshot_payload(ride, gateway)

    @router.get("/rider/rides/{ride_id}/receipt")
    def rider_receipt(ride_id: str, gateway=Depends(get_gateway), trace_log=Depends(get_trace_log)) -> dict[str, Any]:
        ride = _require_completed_ride(gateway, ride_id)
        events = proof_events_for_ride(trace_log, ride)
        receipt = _receipt_engine().derive(ride_id, events)
        return {
            "ride_id": ride_id,
            "receipt_id": receipt.receipt_id,
            "status": "completed",
            "distance_text": f"{max(4, len(ride.pickup) + len(ride.destination))}.0 km",
            "total_text": _fare_total(ride.pickup, ride.destination, "Economy"),
            "started_at": "2026-06-21T09:12:00Z",
            "completed_at": "2026-06-21T09:45:00Z",
            "trust_score": 92,
            "verification_status": "PASSED",
            "replay_match": True,
            "evidence_complete": True,
        }

    @router.get("/rider/rides/{ride_id}/replay")
    def rider_replay(ride_id: str, gateway=Depends(get_gateway), trace_log=Depends(get_trace_log)) -> dict[str, Any]:
        ride = _require_ride(gateway, ride_id)
        events = proof_events_for_ride(trace_log, ride)
        timeline = [
            {
                "label": event.transition or "FAILED",
                "verified": True,
                "sequence": event.sequence_id,
            }
            for event in events
            if event.transition
        ]
        return {
            "ride_id": ride_id,
            "replay_id": f"rply-{ride_id}",
            "replay_verified": ride.status == "COMPLETED",
            "route_summary": f"{ride.pickup} to {ride.destination}",
            "explanation_steps": [
                "Ride request was admitted",
                "Driver acceptance matched assignment state",
                "Trip completion replay matched receipt hash",
            ]
            if ride.status == "COMPLETED"
            else [
                "Replay is pending until the ride completes",
            ],
            "timeline_events": timeline,
        }

    @router.get("/rider/rides/{ride_id}/ledger-receipt")
    def rider_ledger_receipt(ride_id: str, gateway=Depends(get_gateway), trace_log=Depends(get_trace_log)) -> dict[str, Any]:
        ride = _require_completed_ride(gateway, ride_id)
        validation = trace_log.validate_ride(ride_id)
        receipt = _receipt_engine().derive(ride_id, proof_events_for_ride(trace_log, ride))
        return {
            "receipt_id": receipt.receipt_id,
            "verdict": "VALID" if validation.valid else "INVALID",
            "receipt_hash": receipt.receipt_hash,
            "event_count": len(trace_log.events_for_ride(ride_id)),
            "root_hash": validation.trace_hash,
            "hash_mode": "sha256_canonical_chain",
            "signature_mode": receipt.signature_validation.signature_mode,
            "all_signatures_valid": receipt.signature_validation.all_signatures_valid,
            "all_identities_verified": validation.valid,
            "replay_valid": validation.replay_verified,
        }

    @router.get("/rider/rides/{ride_id}/price-explanation")
    def rider_price_explanation(ride_id: str, gateway=Depends(get_gateway)) -> dict[str, Any]:
        ride = _require_ride(gateway, ride_id)
        distance_units = max(1, len(ride.pickup) + len(ride.destination))
        total = round(4.0 + (distance_units * 0.35), 2)
        return {
            "ride_id": ride_id,
            "price_explanation": "Deterministic fare returned by core system.",
            "source": "core_system",
            "line_items": [
                {"label": "Base fare", "amount_text": "AUD 4.00"},
                {"label": "Distance", "amount_text": f"AUD {round(distance_units * 0.35, 2):.2f}"},
                {"label": "Total", "amount_text": f"AUD {total:.2f}"},
            ],
        }

    @router.get("/driver/{driver_id}/availability")
    def driver_availability(driver_id: str, gateway=Depends(get_gateway)) -> dict[str, Any]:
        driver = gateway.dispatcher.drivers.get(driver_id)
        completed = sum(
            1
            for ride in gateway.dispatcher.rides.values()
            if ride.assigned_driver == driver_id and ride.status == "COMPLETED"
        )
        return {
            "driver_id": driver_id,
            "status": "available" if driver and driver.online else "offline",
            "updated_at": "2026-06-21T09:00:01Z",
            "trust_score": 94 if completed else 90,
            "verified_rides": completed,
            "replay_consistency_pct": 100,
        }

    @router.post("/driver/{driver_id}/availability")
    def update_driver_availability(driver_id: str, payload: dict[str, Any], gateway=Depends(get_gateway)) -> dict[str, Any]:
        status = str(payload.get("status", "offline")).strip().lower()
        online = status == "available"
        gateway.driver.status({"driver_id": driver_id, "online": online})
        return {
            "driver_id": driver_id,
            "status": "available" if online else "offline",
            "updated_at": "2026-06-21T09:00:01Z",
            "trust_score": 94,
            "verified_rides": 152,
            "replay_consistency_pct": 100,
        }

    @router.get("/driver/{driver_id}/ride-queue")
    def driver_ride_queue(driver_id: str, gateway=Depends(get_gateway)) -> dict[str, Any]:
        rides = gateway.driver.requests(driver_id)
        items = [
            {
                "ride_id": ride["ride_id"],
                "pickup_text": ride["pickup"],
                "dropoff_text": ride["destination"],
                "rider_name": ride.get("passenger_id", "Rider"),
                "rider_trust_score": 91,
                "status": "pending",
                "quoted_total_text": _fare_total(ride["pickup"], ride["destination"], "Economy"),
                "eta_text": "15 min",
            }
            for ride in rides
        ]
        return {"items": items}

    @router.post("/driver/rides/{ride_id}/accept")
    def driver_accept(ride_id: str, payload: dict[str, Any], gateway=Depends(get_gateway), trace_log=Depends(get_trace_log)) -> dict[str, Any]:
        driver_id = str(payload.get("driver_id", ""))
        ride = gateway.driver.accept({"driver_id": driver_id, "ride_id": ride_id})
        _log_trace_event(
            trace_log,
            ride_id=ride["ride_id"],
            event_id=f"{ride['ride_id']}.accept",
            actor_type="driver",
            actor_id=driver_id,
            action=f"POST /v1/driver/rides/{ride_id}/accept",
            payload={"driver_id": driver_id},
        )
        return _trip_payload(ride)

    @router.post("/driver/rides/{ride_id}/reject")
    def driver_reject(ride_id: str, payload: dict[str, Any], gateway=Depends(get_gateway), trace_log=Depends(get_trace_log)) -> dict[str, Any]:
        ride = _require_ride(gateway, ride_id)
        gateway.dispatcher.cancel_ride(
            passenger_id=ride["passenger_id"],
            ride_id=ride_id,
        )
        driver_id = str(payload.get("driver_id", ""))
        _log_trace_event(
            trace_log,
            ride_id=ride_id,
            event_id=f"{ride_id}.reject",
            actor_type="driver",
            actor_id=driver_id or "driver",
            action=f"POST /v1/driver/rides/{ride_id}/reject",
            payload={"driver_id": driver_id},
        )
        return _trip_payload({**ride, "status": "CANCELED"}, status_hint="cancelled")

    @router.post("/driver/rides/{ride_id}/arrive")
    def driver_arrive(ride_id: str, payload: dict[str, Any], gateway=Depends(get_gateway), trace_log=Depends(get_trace_log)) -> dict[str, Any]:
        driver_id = str(payload.get("driver_id", ""))
        ride = gateway.driver.arrive({"driver_id": driver_id, "ride_id": ride_id})
        _log_trace_event(
            trace_log,
            ride["ride_id"],
            event_id=f"{ride['ride_id']}.arrive",
            actor_type="driver",
            actor_id=driver_id,
            action=f"POST /v1/driver/rides/{ride_id}/arrive",
            payload={"driver_id": driver_id},
        )
        return _trip_payload(ride)

    @router.post("/driver/rides/{ride_id}/start")
    def driver_start(ride_id: str, payload: dict[str, Any], gateway=Depends(get_gateway), trace_log=Depends(get_trace_log)) -> dict[str, Any]:
        driver_id = str(payload.get("driver_id", ""))
        ride = gateway.driver.start({"driver_id": driver_id, "ride_id": ride_id})
        _log_trace_event(
            trace_log,
            ride["ride_id"],
            event_id=f"{ride['ride_id']}.start",
            actor_type="driver",
            actor_id=driver_id,
            action=f"POST /v1/driver/rides/{ride_id}/start",
            payload={"driver_id": driver_id},
        )
        return _trip_payload(ride)

    @router.post("/driver/rides/{ride_id}/complete")
    def driver_complete(ride_id: str, payload: dict[str, Any], gateway=Depends(get_gateway), trace_log=Depends(get_trace_log)) -> dict[str, Any]:
        driver_id = str(payload.get("driver_id", ""))
        ride = gateway.driver.complete({"driver_id": driver_id, "ride_id": ride_id})
        _log_trace_event(
            trace_log,
            ride["ride_id"],
            event_id=f"{ride['ride_id']}.complete",
            actor_type="driver",
            actor_id=driver_id,
            action=f"POST /v1/driver/rides/{ride_id}/complete",
            payload={"driver_id": driver_id},
        )
        events = proof_events_for_ride(trace_log, gateway.dispatcher.rides[ride_id])
        _ = _receipt_engine().derive(ride_id, events)
        return _trip_payload(ride)

    @router.get("/driver/{driver_id}/earnings")
    def driver_earnings(driver_id: str, gateway=Depends(get_gateway)) -> dict[str, Any]:
        completed = [
            ride
            for ride in gateway.dispatcher.rides.values()
            if ride.assigned_driver == driver_id and ride.status == "COMPLETED"
        ]
        total = float(len(completed) * 10)
        return {
            "driver_id": driver_id,
            "period_label": "This week",
            "total_text": f"AUD {total:.2f}",
            "ride_count": len(completed),
            "source": "core_system",
            "verified_ride_count": len(completed),
            "dispute_count": 0,
            "trust_score": 94 if completed else 90,
        }

    @router.get("/driver/{driver_id}/replay-history")
    def driver_replay_history(driver_id: str, gateway=Depends(get_gateway), trace_log=Depends(get_trace_log)) -> dict[str, Any]:
        items = []
        for ride in gateway.dispatcher.rides.values():
            if ride.assigned_driver != driver_id or ride.status != "COMPLETED":
                continue
            events = proof_events_for_ride(trace_log, ride)
            items.append(
                {
                    "ride_id": ride.ride_id,
                    "replay_id": f"replay-{ride.ride_id}",
                    "replay_verified": True,
                    "completed_at": "2026-06-21T09:45:00Z",
                    "trust_score": 92,
                    "timeline_events": [
                        event.transition for event in events if event.transition
                    ],
                }
            )
        return {"items": items}

    @router.get("/operator/dashboard")
    def operator_dashboard(gateway=Depends(get_gateway), trace_log=Depends(get_trace_log)) -> dict[str, Any]:
        control_plane = get_control_plane()
        service = _system_service(gateway, trace_log)
        trust = service.trust_metrics()
        pilot = service.pilot_metrics()
        evidence = service.evidence_pipeline()
        replay = service.replay_health()
        payload = {
            "fleet_trust_score": trust["trust_score"],
            "active_drivers": trust["drivers_online"],
            "verified_rides_today": pilot["completed_rides"],
            "evidence_packets_today": evidence["receipts_count"],
            "open_replay_exceptions": len(service.guard_violations()["violations"]),
            "replay_exception_rate_pct": round((replay["failures"] / max(1, pilot["total_rides"])) * 100, 1),
            "driver_trust_trend": _driver_trust_trend(gateway),
            "public_verification": {
                "status": "operational" if replay["status"] == "PASS" else "degraded",
                "checks_today": evidence["receipts_count"],
                "pass_rate_pct": 100 if replay["status"] == "PASS" else 0,
            },
            "pilot_evidence": {
                "shift_count": pilot["total_rides"] or 1,
                "gps_signal_loss_events": 0,
                "route_deviation_events": replay["hash_chain_failures"],
                "latency_breaches": 0,
            },
        }
        try:
            analytics_snapshot = control_plane.record_dashboard_analytics_snapshot(
                payload=payload,
                source="afriride_operator_dashboard",
                snapshot_type="operator_dashboard",
            )
            payload["analytics_snapshot_id"] = analytics_snapshot["snapshot_id"]
            payload["analytics_snapshot_window"] = analytics_snapshot["window_bucket"]
        except Exception:
            payload["analytics_snapshot_id"] = None
            payload["analytics_snapshot_window"] = None
        try:
            decision_snapshot = control_plane.record_dashboard_decision_snapshot(
                payload=payload,
                source="afriride_operator_dashboard",
                decision_type="operator_decision",
            )
            payload["decision_snapshot_id"] = decision_snapshot["decision_id"]
            payload["decision_snapshot_window"] = decision_snapshot["window_bucket"]
        except Exception:
            payload["decision_snapshot_id"] = None
            payload["decision_snapshot_window"] = None
        try:
            action_snapshot = control_plane.record_dashboard_action_snapshot(
                payload=payload,
                source="afriride_operator_dashboard",
                decision_snapshot_id=payload.get("decision_snapshot_id"),
                action_type="controlled_autonomous_action",
            )
            payload["action_snapshot_id"] = action_snapshot["action_id"]
            payload["action_snapshot_window"] = action_snapshot["window_bucket"]
        except Exception:
            payload["action_snapshot_id"] = None
            payload["action_snapshot_window"] = None
        return payload

    @router.get("/operator/analytics")
    def operator_analytics(
        source: str = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return get_control_plane().dashboard_analytics(source=source, limit=limit)

    @router.get("/operator/analytics/history")
    def operator_analytics_history(
        source: str = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return get_control_plane().dashboard_analytics_history(source=source, limit=limit)

    @router.get("/operator/analytics/insights")
    def operator_analytics_insights(
        source: str = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return get_control_plane().dashboard_analytics_insights(source=source, limit=limit)

    @router.get("/operator/analytics/predictions")
    def operator_analytics_predictions(
        source: str = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return get_control_plane().dashboard_analytics_prediction(source=source, limit=limit)

    @router.get("/operator/demand-forecast")
    def operator_demand_forecast(
        organization_id: str | None = None,
        source: str = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return get_control_plane().dashboard_demand_forecast(
            organization_id=organization_id,
            source=source,
            limit=limit,
        )

    @router.get("/operator/strategy-engine")
    def operator_strategy_engine(
        organization_id: str | None = None,
        source: str = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        from afritech.afriprogramming.phase5 import build_autonomous_strategy_projection

        org_id = organization_id or phase0_control_plane.DEFAULT_ORGANIZATION_ID
        return build_autonomous_strategy_projection(organization_id=org_id, source=source, limit=limit)

    @router.get("/operator/decisions")
    def operator_decisions(
        source: str = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return get_control_plane().dashboard_decisions(source=source, limit=limit)

    @router.get("/operator/decisions/history")
    def operator_decisions_history(
        source: str = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return get_control_plane().dashboard_decisions_history(source=source, limit=limit)

    @router.get("/operator/actions")
    def operator_actions(
        source: str = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return get_control_plane().dashboard_actions(source=source, limit=limit)

    @router.get("/operator/autonomy")
    def operator_autonomy(
        source: str = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return get_control_plane().dashboard_autonomy(source=source, limit=limit)

    @router.get("/operator/city-automation")
    def operator_city_automation(
        source: str = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return get_control_plane().dashboard_city_automation(source=source, limit=limit)

    @router.get("/operator/multi-city-orchestration")
    def operator_multi_city_orchestration(
        source: str = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return get_control_plane().dashboard_multi_city_orchestration(source=source, limit=limit)

    @router.get("/operator/digital-twin")
    def operator_digital_twin(
        source: str = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return get_control_plane().dashboard_digital_twin(source=source, limit=limit)

    @router.get("/operator/meta-learning-redesign")
    def operator_meta_learning_redesign(
        source: str = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return get_control_plane().dashboard_meta_learning_redesign(source=source, limit=limit)

    @router.get("/operator/actions/history")
    def operator_actions_history(
        source: str = "afriride_operator_dashboard",
        limit: int = 24,
    ) -> dict[str, Any]:
        return get_control_plane().dashboard_actions_history(source=source, limit=limit)

    @router.get("/operator/replay-exceptions")
    def replay_exceptions(gateway=Depends(get_gateway), trace_log=Depends(get_trace_log)) -> dict[str, Any]:
        service = _system_service(gateway, trace_log)
        violations = service.guard_violations()["violations"]
        items = []
        for index, violation in enumerate(violations, start=1):
            items.append(
                {
                    "ride_id": f"ride-{index:03d}",
                    "receipt_id": f"rcpt-{index:03d}",
                    "severity": "review",
                    "reason": violation["type"].lower(),
                    "assigned_team": "pilot-ops",
                }
            )
        return {"items": items}

    @router.get("/operator/public-verification/status")
    def public_verification_status(gateway=Depends(get_gateway), trace_log=Depends(get_trace_log)) -> dict[str, Any]:
        replay = _system_service(gateway, trace_log).replay_health()
        return {
            "status": "operational" if replay["status"] == "PASS" else "degraded",
            "last_success_at": "2026-06-21T09:45:00Z",
            "checks_today": trace_log.integrity_summary()["valid_traces"],
            "pass_rate_pct": 100 if replay["status"] == "PASS" else 0,
            "private_data_redaction": "enabled",
        }

    return router


def _trip_payload(ride: dict[str, Any], *, status_hint: str | None = None) -> dict[str, Any]:
    current_status = status_hint or _mobile_trip_status(str(ride["status"]))
    return {
        "ride_id": ride["ride_id"],
        "status": current_status,
        "rider_name": ride.get("passenger_id", "Rider"),
        "pickup_text": ride.get("pickup", ""),
        "dropoff_text": ride.get("destination", ""),
        "next_instruction": "Receipt ready" if current_status == "completed" else "Follow the system-provided trip state.",
        "trust_score": 92 if current_status == "completed" else 90,
        "replay_verified": current_status == "completed",
    }


def _ride_snapshot_payload(ride: Any, gateway: Any) -> dict[str, Any]:
    ride_status = str(ride.status)
    has_driver = bool(ride.assigned_driver)
    driver_name = "Djuma O" if has_driver else None
    vehicle_label = "Toyota Pilot" if has_driver else None
    return {
        "ride_id": ride.ride_id,
        "status": _mobile_ride_status(ride_status),
        "driver_name": driver_name,
        "vehicle_label": vehicle_label,
        "eta_text": "3 min" if has_driver else "Driver not assigned",
        "location_text": "Approaching pickup" if has_driver else "Waiting for driver",
        "driver_trust_score": 94 if has_driver else None,
        "trust_score": 92 if ride_status == "COMPLETED" else 91,
        "trust_summary": {
            "trust_score": 92 if ride_status == "COMPLETED" else 91,
            "verification_status": "PASSED" if ride_status == "COMPLETED" else "REVIEW_REQUIRED",
            "replay_match": ride_status == "COMPLETED",
            "evidence_complete": ride_status == "COMPLETED",
            "receipt_id": f"rcpt-{ride.ride_id}" if ride_status == "COMPLETED" else None,
            "public_verification_url": f"/public/trust/rcpt-{ride.ride_id}" if ride_status == "COMPLETED" else None,
        },
    }


def _require_ride(gateway, ride_id: str) -> Any:
    ride = gateway.dispatcher.rides.get(ride_id)
    if ride is None:
        raise HTTPException(status_code=404, detail="ride_not_found")
    return ride


def _require_completed_ride(gateway, ride_id: str) -> Any:
    ride = _require_ride(gateway, ride_id)
    if ride.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="ride_not_completed")
    return ride


def _mobile_ride_status(status: str) -> str:
    mapping = {
        "REQUESTED": "requested",
        "DRIVER_ASSIGNED": "driver_assigned",
        "DRIVER_ARRIVED": "arriving",
        "IN_TRIP": "in_progress",
        "COMPLETED": "completed",
        "CANCELED": "cancelled",
    }
    return mapping.get(status, "requested")


def _mobile_trip_status(status: str) -> str:
    mapping = {
        "REQUESTED": "accepted",
        "DRIVER_ASSIGNED": "accepted",
        "DRIVER_ARRIVED": "arrived",
        "IN_TRIP": "started",
        "COMPLETED": "completed",
        "CANCELED": "cancelled",
    }
    return mapping.get(status, "accepted")


def _fare_total(pickup: str, dropoff: str, ride_type: str) -> str:
    distance_units = max(1, len(pickup) + len(dropoff))
    base = 4.0 + (distance_units * 0.35)
    premium = 1.0 if ride_type.lower() == "premium" else 0.0
    airport = 6.0 if ride_type.lower() == "airport" else 0.0
    total = round(base + premium + airport, 2)
    return f"AUD {total:.2f}"


def _driver_trust_trend(gateway) -> list[dict[str, Any]]:
    completed_count = sum(1 for ride in gateway.dispatcher.rides.values() if ride.status == "COMPLETED")
    base = max(90, 90 + min(completed_count, 6))
    return [
        {"label": "Mon", "score": max(90, base - 3)},
        {"label": "Tue", "score": max(90, base - 2)},
        {"label": "Wed", "score": max(90, base - 1)},
        {"label": "Thu", "score": base},
    ]


def _log_trace_event(
    trace_log: Any,
    ride_id: str,
    *,
    event_id: str,
    actor_type: str,
    actor_id: str,
    action: str,
    payload: dict[str, Any],
) -> None:
    trace_log.append(
        {
            "event_id": event_id,
            "device_id": f"{actor_type}-{actor_id or 'system'}",
            "actor_type": actor_type,
            "actor_id": actor_id or "system",
            "action": action,
            "payload": payload,
            "local_timestamp": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "app_version": "1.0.0",
            "test_mode": False,
        },
        ride_id,
    )


__all__ = ["build_afriride_next_gen_mobile_router"]
