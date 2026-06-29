"""Canonical NovaRide architecture contract definitions.

This module is the single source of truth for high-level NovaRide architecture
layers that are exposed through APIs, rendered by dashboards, and referenced by
documentation/tests.
"""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from typing import Any

NOVARIDE_ARCHITECTURE_VERSION = "2026.07.0"

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

NOVARIDE_MATURITY_DIMENSIONS: tuple[dict[str, Any], ...] = (
    {
        "dimension": "Architecture Maturity",
        "capabilities": (
            "Layer separation",
            "Governance",
            "Event sourcing",
            "Replay",
            "Proof",
        ),
    },
    {
        "dimension": "Operational Maturity",
        "capabilities": (
            "Command Center",
            "Incident Engine",
            "Fleet Intelligence",
            "Digital Twin",
            "Public Trust",
        ),
    },
    {
        "dimension": "Production Readiness",
        "capabilities": (
            "Distributed consistency",
            "Key management",
            "Disaster recovery",
            "Regulatory readiness",
            "Independent verification",
        ),
    },
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


def _json_ready(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _build_novaride_architecture_contract() -> dict[str, Any]:
    """Build the versioned high-level NovaRide architecture contract."""

    return {
        "version": NOVARIDE_ARCHITECTURE_VERSION,
        "layers": list(NOVARIDE_LAYERED_ARCHITECTURE),
        "operator_intervention_flow": list(NOVARIDE_OPERATOR_INTERVENTION_FLOW),
        "maturity_dimensions": _json_ready(NOVARIDE_MATURITY_DIMENSIONS),
        "enterprise_operations": _json_ready(NOVARIDE_ENTERPRISE_OPERATIONS_LAYER),
        "production_readiness": _json_ready(NOVARIDE_PRODUCTION_INFRASTRUCTURE_READINESS),
    }


@lru_cache(maxsize=1)
def _cached_novaride_architecture_contract() -> dict[str, Any]:
    """Build and cache the canonical contract for this process."""

    return _build_novaride_architecture_contract()


NOVARIDE_ARCHITECTURE_CONTRACT = _cached_novaride_architecture_contract()


def novaride_architecture_contract() -> dict[str, Any]:
    """Return an isolated copy of the cached NovaRide architecture contract."""

    return deepcopy(_cached_novaride_architecture_contract())
