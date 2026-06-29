"""NovaRide Phase 13 global execution bridge.

This layer turns the phase 12 global scaling projections into controlled
action surfaces. It remains bounded: the API can record governed execution
events, but this module does not grant raw cloud, payment, or logistics
authority. Instead it composes the existing phase 12, NovaPay, and logistics
surfaces into a deployment plan, a controlled AI decision engine, AWS infra
projection, execution bridge, AI optimization guidance, and NovaTech expansion
views for NovaConnect and NovaPay.
"""

from __future__ import annotations

from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from afritech.afriprogramming.phase_common import DEFAULT_ORGANIZATION_ID, build_control_projection, get_phase_store, phase_now

from afritech.afriprogramming.phase12 import build_phase12_status
from afritech.core_platform.live_transaction import build_live_transaction_readiness
from afritech.core_platform.settlement import build_settlement_corridor_matrix, build_settlement_status
from afritech.services.africonnecttl.contracts import AUTHORITY_BOUNDARY as AFRICONNECTTL_AUTHORITY_BOUNDARY
from afritech.services.africonnecttl.registry import (
    EVIDENCE_FIELDS,
    SHIPMENT_LIFECYCLE,
    STOP_CONDITIONS,
    SURFACE_DEFINITION,
    validate_lifecycle,
    validate_surface_contract,
)


PHASE13_TOPIC = "novaride.phase13.global_execution_bridge"

NOVARIDE_PHASE13_MODULES = (
    {
        "key": "global_deployment_plan",
        "name": "Global Deployment Plan",
        "purpose": "Describe the controlled production rollout plan across regions, services, and rollout stages.",
    },
    {
        "key": "controlled_ai_decision_engine",
        "name": "Controlled AI Decision Engine",
        "purpose": "Convert phase 12 projections into bounded actions only when explicit gates are satisfied.",
    },
    {
        "key": "aws_production_infra",
        "name": "AWS Production Infra",
        "purpose": "Project the AWS runtime, networking, storage, security, and observability surface.",
    },
    {
        "key": "real_execution_layer",
        "name": "Real Execution Layer",
        "purpose": "Turn projections into controlled action candidates with an operator acknowledgment gate.",
    },
    {
        "key": "ai_optimization",
        "name": "AI Optimization",
        "purpose": "Keep pricing and incentives adaptive while remaining bounded and reviewable.",
    },
    {
        "key": "novaconnect_expansion",
        "name": "NovaConnect Expansion",
        "purpose": "Project logistics and custody-chain expansion as a replay-only logistics surface.",
    },
    {
        "key": "novapay_expansion",
        "name": "NovaPay Expansion",
        "purpose": "Project the payment-rail expansion path across settlements, corridors, and live test readiness.",
    },
)

NOVARIDE_PHASE13_NAVIGATION = (
    "workspace",
    "global_deployment_plan",
    "controlled_ai_decision_engine",
    "aws_production_infra",
    "real_execution_layer",
    "ai_optimization",
    "novaconnect_expansion",
    "novapay_expansion",
)

NOVARIDE_PHASE13_ALLOWED_ACTIONS = (
    "view_global_deployment_plan",
    "review_controlled_ai_decisions",
    "review_aws_production_infra",
    "review_real_execution_layer",
    "review_pricing_adjustments",
    "review_incentive_tuning",
    "review_novaconnect_expansion",
    "review_novapay_expansion",
    "activate_controlled_execution",
)

NOVARIDE_PHASE13_FORBIDDEN_ACTIONS = (
    "direct_aws_mutation",
    "direct_provider_execution",
    "bypass_trust_engine",
    "bypass_audit_chain",
    "autonomous_global_deployment",
)

AWS_SERVICE_CATALOG = (
    {"service": "novaride-api", "runtime": "ECS/Fargate", "purpose": "Public API + controlled backend"},
    {"service": "novaride-dashboard", "runtime": "S3/CloudFront", "purpose": "Operator and admin UI"},
    {"service": "novaride-realtime", "runtime": "ECS/Fargate", "purpose": "WebSocket and live telemetry"},
    {"service": "novaride-dispatch", "runtime": "ECS/Fargate", "purpose": "Matching, routing, and execution coordination"},
    {"service": "novaride-payments", "runtime": "ECS/Fargate", "purpose": "NovaPay ledger and settlement bridge"},
    {"service": "novaride-audit", "runtime": "ECS/Fargate", "purpose": "Audit, replay, and evidence indexing"},
    {"service": "novaride-intelligence", "runtime": "ECS/Fargate", "purpose": "Controlled AI decision and optimization surfaces"},
)

AWS_INFRA_COMPONENTS = (
    "Route53",
    "CloudFront",
    "AWS WAF",
    "ALB",
    "ECS/Fargate",
    "RDS PostgreSQL",
    "ElastiCache Redis",
    "S3",
    "ECR",
    "CloudWatch",
    "SNS/SQS",
    "Secrets Manager",
    "KMS",
    "IAM",
)


def _store():
    return get_phase_store()


def _now() -> str:
    return phase_now()


def _safe_decimal(value: Any, default: str = "0.00") -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:  # pragma: no cover - defensive
        return Decimal(default)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:  # pragma: no cover - defensive
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:  # pragma: no cover - defensive
        return default


def _clamp(value: float, *, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _money_text(value: Decimal | int | str) -> str:
    return format(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), ".2f")


def _normalize_text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _latest_snapshot_payload(organization_id: str) -> dict[str, Any]:
    snapshot = _store().latest_dashboard_analytics_snapshot(organization_id=organization_id)
    payload = snapshot.get("payload", {}) if snapshot else {}
    return payload if isinstance(payload, dict) else {}


def _phase12_workspace(organization_id: str, limit: int) -> dict[str, Any]:
    return build_phase12_status(organization_id=organization_id, limit=limit)


def _city_region_code(country_code: str) -> str:
    normalized = _normalize_text(country_code, default="AU").upper()
    if normalized == "AU":
        return "ap-southeast-2"
    if normalized in {"KE", "BI", "CD"}:
        return "af-south-1"
    return "us-east-1"


def _deployment_topology(phase12_workspace: dict[str, Any]) -> list[dict[str, Any]]:
    multi_city = phase12_workspace.get("global_scale_workspace", {}).get("multi_city_management", {})
    cities = list(multi_city.get("city_topology", [])) if isinstance(multi_city, dict) else []
    deployment_topology: list[dict[str, Any]] = []
    for index, city in enumerate(cities, start=1):
        country_code = _normalize_text(city.get("country_code") or "AU", default="AU").upper()
        deployment_topology.append(
            {
                "region_id": f"region-{index:02d}",
                "city": city.get("city", "CBD"),
                "country_code": country_code,
                "currency": _normalize_text(city.get("currency") or "AUD", default="AUD").upper(),
                "language": _normalize_text(city.get("language") or "en", default="en").lower(),
                "aws_region": _city_region_code(country_code),
                "edge_node": f"edge-{_normalize_text(city.get('city') or 'cbd').replace(' ', '-').lower()}",
                "service_cell": f"cell-{index:02d}",
                "deployment_mode": "primary" if index == 1 else "secondary",
                "status": "active" if _safe_int(city.get("drivers"), 0) > 0 else "standby",
                "coverage_score": _safe_int(city.get("coverage_score"), 0),
                "demand_index": _safe_int(city.get("demand_index"), 0),
                "trust_score": _safe_int(city.get("average_trust_score"), 0),
                "region_price_multiplier": _safe_float(city.get("region_price_multiplier"), 1.0),
            }
        )
    return deployment_topology


def _deployment_plan_projection(
    *,
    organization_id: str,
    phase12_workspace: dict[str, Any],
    limit: int,
) -> dict[str, Any]:
    deployment_requests = _store().list_deployment_requests(organization_id=organization_id, limit=limit)
    deployments = _store().list_deployments(organization_id=organization_id, limit=limit)
    latest_request = deployment_requests[0] if deployment_requests else None
    latest_deployment = deployments[0] if deployments else None
    topology = _deployment_topology(phase12_workspace)
    base_ready = bool(phase12_workspace["ready"])
    deployment_plan_ready = bool(base_ready and topology and (deployment_requests or deployments))

    rollout_stages = [
        {
            "stage": "foundation",
            "mode": "single_region",
            "target": "core api, dashboard, auth, dispatch, payments, audit",
            "gate": "phase12_ready",
        },
        {
            "stage": "regional_active",
            "mode": "multi_region_active",
            "target": "regional read replicas, live dispatch, live telemetry",
            "gate": "city_topology_ready",
        },
        {
            "stage": "controlled_expansion",
            "mode": "controlled_execution",
            "target": "AI decision engine, pricing adjustments, incentives tuning",
            "gate": "operator_acknowledged",
        },
        {
            "stage": "global_learning",
            "mode": "global_learning_loop",
            "target": "NovaConnect + NovaPay expansion surfaces",
            "gate": "bounded_review",
        },
    ]

    deployment_plan = {
        "view": "novaride_phase13_global_deployment_plan",
        "execution_mode": "controlled_execution_bridge",
        "deployment_plan_ready": deployment_plan_ready,
        "primary_region": topology[0]["aws_region"] if topology else "ap-southeast-2",
        "regional_topology": topology,
        "services": list(AWS_SERVICE_CATALOG),
        "infrastructure": {
            "networking": [
                "Route53",
                "CloudFront",
                "AWS WAF",
                "ALB",
                "multi_az_vpc",
                "private_subnets",
            ],
            "compute": ["ECS/Fargate", "ECR"],
            "data": ["RDS PostgreSQL", "ElastiCache Redis", "S3"],
            "messaging": ["SNS/SQS"],
            "security": ["IAM", "Secrets Manager", "KMS"],
            "observability": ["CloudWatch", "central_logs", "trace_sampling"],
        },
        "rollout_stages": rollout_stages,
        "delivery_pipeline": {
            "source_control": "GitHub",
            "build": "GitHub Actions",
            "container_registry": "ECR",
            "deployment_strategy": "blue_green_with_canary",
            "rollback_strategy": "automatic_health_gate_rollback",
        },
        "availability_targets": {
            "api": "99.9%",
            "dispatch": "99.9%",
            "payments": "99.95%",
            "audit": "99.99%",
        },
        "security_posture": {
            "least_privilege": True,
            "mfa_required": True,
            "secrets_managed": True,
            "kms_encryption": True,
            "waf_enabled": True,
        },
        "readiness": {
            "phase12_ready": bool(base_ready),
            "topology_ready": bool(topology),
            "deployment_request_ready": bool(deployment_requests),
            "deployment_record_ready": bool(deployments),
            "latest_request_status": latest_request.get("status") if latest_request else None,
            "latest_deployment_status": latest_deployment.get("status") if latest_deployment else None,
        },
        "latest_request": latest_request,
        "latest_deployment": latest_deployment,
        "projection_only": True,
        "read_only": True,
        "governance_linked": True,
        "creates_authority": False,
    }
    deployment_plan["readiness"]["plan_ready"] = deployment_plan_ready
    return deployment_plan


def _controlled_ai_decision_engine_projection(
    *,
    phase12_workspace: dict[str, Any],
    deployment_plan: dict[str, Any],
) -> dict[str, Any]:
    multi_city = phase12_workspace.get("global_scale_workspace", {}).get("multi_city_management", {})
    auto_decision = phase12_workspace.get("global_scale_workspace", {}).get("auto_decision_engine", {})
    fraud_prediction = phase12_workspace.get("global_scale_workspace", {}).get("fraud_prediction", {})
    driver_incentives = phase12_workspace.get("global_scale_workspace", {}).get("driver_incentives", {})
    phase12_ready = bool(phase12_workspace.get("ready"))
    deployment_plan_ready = bool(deployment_plan.get("deployment_plan_ready"))
    decision_lane = _normalize_text(auto_decision.get("decision_lane"), default="hold")
    predicted_risk_score = _safe_int(fraud_prediction.get("predicted_risk_score"), 100)
    safe_to_execute = bool(
        phase12_ready
        and deployment_plan_ready
        and decision_lane in {"scale", "review"}
        and predicted_risk_score <= 55
    )
    controlled_lane = "scale" if safe_to_execute and decision_lane == "scale" else "review" if safe_to_execute else "hold"
    control_actions = [
        "adjust_region_pricing" if controlled_lane in {"scale", "review"} else "hold_pricing",
        "tune_driver_incentives" if controlled_lane in {"scale", "review"} else "hold_incentives",
        "allocate_city_capacity" if controlled_lane == "scale" else "review_city_capacity",
        "prepare_novaconnect_expansion" if controlled_lane == "scale" else "hold_novaconnect",
        "prepare_novapay_expansion" if controlled_lane in {"scale", "review"} else "hold_novapay",
    ]
    if controlled_lane == "hold":
        summary = "Controlled execution remains held until the deployment plan and trust gate align."
    elif controlled_lane == "scale":
        summary = "The controlled AI decision engine can widen execution within bounded thresholds."
    else:
        summary = "The controlled AI decision engine is review-ready but not yet broad enough for execution widening."

    return {
        "view": "novaride_phase13_controlled_ai_decision_engine",
        "decision_lane": controlled_lane,
        "source_decision_lane": decision_lane,
        "decision_summary": summary,
        "safe_to_execute": safe_to_execute,
        "operator_acknowledged_required": True,
        "control_actions": control_actions,
        "decision_controls": {
            "max_predicted_risk_score": 55,
            "min_global_scale_score": 70,
            "min_multi_city_count": 2,
            "max_pricing_delta_pct": 15,
            "max_incentive_delta_pct": 20,
        },
        "signals": {
            "global_scale_score": _safe_int(phase12_workspace.get("global_scale_workspace", {}).get("global_scale_score"), 0),
            "global_coverage_score": _safe_int(multi_city.get("global_coverage_score"), 0),
            "global_trust_score": _safe_int(multi_city.get("global_trust_score"), 0),
            "predicted_risk_score": predicted_risk_score,
            "risk_band": _normalize_text(fraud_prediction.get("risk_band"), default="low"),
            "driver_incentive_focus": _normalize_text(driver_incentives.get("incentive_focus"), default="balance"),
            "deployment_plan_ready": deployment_plan_ready,
        },
        "projection_only": True,
        "read_only": True,
    }


def _aws_production_infra_projection(
    *,
    phase12_workspace: dict[str, Any],
    deployment_plan: dict[str, Any],
) -> dict[str, Any]:
    deployment_topology = list(deployment_plan.get("regional_topology", []))
    global_scale_workspace = phase12_workspace.get("global_scale_workspace", {})
    city_count = _safe_int(global_scale_workspace.get("multi_city_management", {}).get("city_count"), 0)
    deployment_mode = "multi_region_active" if city_count >= 2 else "single_region"
    return {
        "view": "novaride_phase13_aws_production_infra",
        "deployment_mode": deployment_mode,
        "networking": deployment_plan["infrastructure"]["networking"],
        "compute": deployment_plan["infrastructure"]["compute"],
        "data": deployment_plan["infrastructure"]["data"],
        "messaging": deployment_plan["infrastructure"]["messaging"],
        "security": deployment_plan["infrastructure"]["security"],
        "observability": deployment_plan["infrastructure"]["observability"],
        "regional_topology": deployment_topology,
        "availability_targets": deployment_plan["availability_targets"],
        "deployment_strategy": deployment_plan["delivery_pipeline"]["deployment_strategy"],
        "aws_account_baseline": {
            "multi_az": True,
            "backups": True,
            "encryption": True,
            "autoscaling": True,
            "drift_detection": True,
            "cost_controls": True,
        },
        "aws_infra_ready": bool(deployment_plan.get("deployment_plan_ready") and deployment_topology),
        "projection_only": True,
        "read_only": True,
    }


def _real_execution_layer_projection(
    *,
    phase12_workspace: dict[str, Any],
    deployment_plan: dict[str, Any],
    controlled_ai_decision_engine: dict[str, Any],
) -> dict[str, Any]:
    ready = bool(
        deployment_plan.get("deployment_plan_ready")
        and controlled_ai_decision_engine.get("safe_to_execute")
        and phase12_workspace.get("ready")
    )
    execution_mode = "controlled_actions" if ready else "review_only"
    controlled_actions = []
    if execution_mode == "controlled_actions":
        controlled_actions = [
            "activate controlled deployment plan",
            "apply bounded region pricing",
            "tune live incentives within guardrails",
            "prepare NovaConnect expansion review",
            "prepare NovaPay settlement expansion review",
        ]
    else:
        controlled_actions = [
            "hold execution bridge",
            "review deployment prerequisites",
            "keep pricing and incentives advisory-only",
        ]
    return {
        "view": "novaride_phase13_real_execution_layer",
        "execution_mode": execution_mode,
        "execution_ready": ready,
        "controlled_actions": controlled_actions,
        "operator_acknowledgment_required": True,
        "action_lane": controlled_ai_decision_engine.get("decision_lane", "hold"),
        "deployment_mode": deployment_plan.get("execution_mode", "controlled_execution_bridge"),
        "projection_only": True,
        "read_only": True,
    }


def _ai_optimization_projection(
    *,
    phase12_workspace: dict[str, Any],
) -> dict[str, Any]:
    business_pricing = phase12_workspace.get("business_pricing", {})
    city_profit = phase12_workspace.get("city_profit_optimization", {})
    driver_incentives = phase12_workspace.get("driver_incentives", {})
    pricing = dict(business_pricing.get("pricing", {})) if isinstance(business_pricing, dict) else {}
    incentives = dict(business_pricing.get("incentives", {})) if isinstance(business_pricing, dict) else {}
    base_price = _safe_decimal(pricing.get("adjusted_price") or pricing.get("base_price") or "0.00")
    commercial_take_rate = _safe_float(incentives.get("commercial_take_rate"), 0.2)
    demand_pressure = _safe_int(phase12_workspace.get("global_scale_workspace", {}).get("multi_city_management", {}).get("global_demand_index"), 0)
    risk_band = _normalize_text(phase12_workspace.get("global_scale_workspace", {}).get("fraud_prediction", {}).get("risk_band"), default="low")

    if risk_band in {"high", "critical"}:
        pricing_adjustment_pct = Decimal("0.0")
        incentive_adjustment_pct = Decimal("0.0")
        optimization_mode = "bounded_hold"
        rationale = "Keep pricing and incentives review-only while fraud risk remains elevated."
    elif demand_pressure >= 70:
        pricing_adjustment_pct = Decimal("4.0")
        incentive_adjustment_pct = Decimal("12.0")
        optimization_mode = "bounded_scale"
        rationale = "Increase pricing and incentives in line with strong demand, but keep operator guardrails active."
    elif demand_pressure >= 40:
        pricing_adjustment_pct = Decimal("2.0")
        incentive_adjustment_pct = Decimal("6.0")
        optimization_mode = "bounded_tune"
        rationale = "Tune pricing and incentives conservatively around current demand."
    else:
        pricing_adjustment_pct = Decimal("0.5")
        incentive_adjustment_pct = Decimal("3.0")
        optimization_mode = "bounded_balance"
        rationale = "Keep the market balanced while preserving deterministic pricing."

    price_delta = (base_price * pricing_adjustment_pct / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    adjusted_price = (base_price + price_delta).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    incentive_adjustment = min(20.0, float(incentive_adjustment_pct))

    city_adjustments = []
    for city in phase12_workspace.get("global_scale_workspace", {}).get("multi_city_management", {}).get("city_topology", []):
        city_adjustments.append(
            {
                "city": city.get("city", "CBD"),
                "currency": city.get("currency", "AUD"),
                "pricing_adjustment_pct": _money_text(pricing_adjustment_pct),
                "incentive_adjustment_pct": f"{incentive_adjustment:.1f}",
                "focus": "demand" if _safe_int(city.get("demand_index"), 0) >= 50 else "balance",
            }
        )

    return {
        "view": "novaride_phase13_ai_optimization",
        "optimization_mode": optimization_mode,
        "pricing_adjustment_pct": _money_text(pricing_adjustment_pct),
        "incentive_adjustment_pct": f"{incentive_adjustment:.1f}",
        "base_price": _money_text(base_price),
        "adjusted_price": _money_text(adjusted_price),
        "commercial_take_rate": round(commercial_take_rate, 4),
        "driver_incentive_focus": driver_incentives.get("incentive_focus", "balance"),
        "city_adjustments": city_adjustments,
        "city_profit": city_profit,
        "rationale": rationale,
        "optimization_ready": bool(city_adjustments),
        "projection_only": True,
        "read_only": True,
    }


def _novaconnect_expansion_projection() -> dict[str, Any]:
    lifecycle = [{"contract_id": contract_id, "status": status} for contract_id, status in SHIPMENT_LIFECYCLE]
    surface_ready = False
    lifecycle_ready = False
    surface_error = None
    lifecycle_error = None
    try:
        surface_ready = validate_surface_contract()
    except Exception as exc:  # pragma: no cover - defensive
        surface_error = str(exc)
    try:
        lifecycle_ready = validate_lifecycle(lifecycle)
    except Exception as exc:  # pragma: no cover - defensive
        lifecycle_error = str(exc)
    return {
        "view": "novaride_phase13_novaconnect_expansion",
        "surface": SURFACE_DEFINITION,
        "authority_boundary": AFRICONNECTTL_AUTHORITY_BOUNDARY,
        "shipment_lifecycle": lifecycle,
        "evidence_fields": list(EVIDENCE_FIELDS),
        "stop_conditions": list(STOP_CONDITIONS),
        "surface_ready": surface_ready,
        "lifecycle_ready": lifecycle_ready,
        "live_deployment_forbidden": True,
        "deployment_state": "planned",
        "integration_targets": [
            "warehouse_operations",
            "courier_dispatch",
            "freight_custody_chain",
            "proof_of_delivery",
            "replay_verification",
        ],
        "surface_error": surface_error,
        "lifecycle_error": lifecycle_error,
        "projection_only": True,
        "read_only": True,
    }


def _novapay_expansion_projection(
    *,
    phase12_workspace: dict[str, Any],
) -> dict[str, Any]:
    readiness = build_live_transaction_readiness()
    settlement = build_settlement_status()
    corridors = build_settlement_corridor_matrix()
    supported_currencies = list(phase12_workspace.get("global_scale_workspace", {}).get("currency_support", {}).get("supported_currencies", []))
    ready_corridors = list(readiness.get("ready_corridors", []))
    live_ready = bool(readiness.get("live_ready"))
    expansion_ready = bool(readiness["provider"]["available"] and settlement.get("cross_border_supported"))
    payment_rails = [
        "wallet",
        "mobile_money",
        "bank_transfer",
        "cards",
        "mfs_africa",
        "settlement_bridge",
    ]
    if live_ready:
        expansion_stage = "live_ready"
    elif ready_corridors:
        expansion_stage = "controlled_live_test_ready"
    else:
        expansion_stage = "controlled_review"
    return {
        "view": "novaride_phase13_novapay_expansion",
        "expansion_stage": expansion_stage,
        "ready": expansion_ready,
        "live_ready": live_ready,
        "provider": readiness["provider"],
        "settlement": settlement,
        "corridors": corridors,
        "ready_corridors": ready_corridors,
        "supported_currencies": supported_currencies,
        "payment_rails": payment_rails,
        "controls": readiness["required_live_controls"],
        "operator_confirmation_required": readiness["operator_confirmation_required"],
        "real_money_movement_blocked": readiness["real_money_movement_blocked"],
        "expansion_summary": (
            "NovaPay can expand through controlled live tests."
            if live_ready
            else "NovaPay expansion remains review-bound until live controls are satisfied."
        ),
        "projection_only": True,
        "read_only": True,
    }


def build_phase13_global_execution_workspace_projection(
    *,
    organization_id: str,
    limit: int = 100,
    source: str | None = "afriride_phase13_global_execution",
) -> dict[str, Any]:
    phase12_status = _phase12_workspace(organization_id, limit)
    deployment_plan = _deployment_plan_projection(
        organization_id=organization_id,
        phase12_workspace=phase12_status,
        limit=limit,
    )
    controlled_ai_decision_engine = _controlled_ai_decision_engine_projection(
        phase12_workspace=phase12_status,
        deployment_plan=deployment_plan,
    )
    aws_production_infra = _aws_production_infra_projection(
        phase12_workspace=phase12_status,
        deployment_plan=deployment_plan,
    )
    real_execution_layer = _real_execution_layer_projection(
        phase12_workspace=phase12_status,
        deployment_plan=deployment_plan,
        controlled_ai_decision_engine=controlled_ai_decision_engine,
    )
    ai_optimization = _ai_optimization_projection(phase12_workspace=phase12_status)
    novaconnect_expansion = _novaconnect_expansion_projection()
    novapay_expansion = _novapay_expansion_projection(phase12_workspace=phase12_status)

    phase12_ready = bool(phase12_status.get("ready"))
    plan_ready = bool(deployment_plan.get("deployment_plan_ready"))
    controlled_ai_ready = bool(controlled_ai_decision_engine.get("safe_to_execute"))
    aws_ready = bool(aws_production_infra.get("aws_infra_ready"))
    real_execution_ready = bool(real_execution_layer.get("execution_ready"))
    ai_optimization_ready = bool(ai_optimization.get("optimization_ready"))
    nova_connect_ready = bool(novaconnect_expansion.get("surface_ready") and novaconnect_expansion.get("lifecycle_ready"))
    novapay_ready = bool(novapay_expansion.get("ready"))

    global_execution_score = int(
        round(
            _clamp(
                (_safe_int(phase12_status.get("global_scale_workspace", {}).get("global_scale_score"), 0) * 0.24)
                + (100 if plan_ready else 0) * 0.16
                + (100 if controlled_ai_ready else 0) * 0.16
                + (100 if aws_ready else 0) * 0.16
                + (100 if real_execution_ready else 0) * 0.12
                + (100 if ai_optimization_ready else 0) * 0.08
                + (100 if nova_connect_ready else 0) * 0.04
                + (100 if novapay_ready else 0) * 0.04,
                minimum=0.0,
                maximum=100.0,
            )
        )
    )
    if global_execution_score >= 85:
        readiness_band = "global_execution_ready"
    elif global_execution_score >= 70:
        readiness_band = "global_execution_review_ready"
    elif global_execution_score >= 50:
        readiness_band = "global_execution_watch"
    else:
        readiness_band = "global_execution_held"

    summary = {
        "phase12_ready": phase12_ready,
        "global_deployment_plan_ready": plan_ready,
        "controlled_ai_engine_ready": controlled_ai_ready,
        "aws_infra_ready": aws_ready,
        "real_execution_ready": real_execution_ready,
        "ai_optimization_ready": ai_optimization_ready,
        "nova_connect_ready": nova_connect_ready,
        "novapay_ready": novapay_ready,
        "tenant_isolation_preserved": True,
    }
    ready = all(summary.values())

    return {
        "view": "novaride_phase13_global_execution_workspace",
        "phase": "13",
        "platform": "NovaRide Phase 13",
        "organization_id": organization_id,
        "source": source or "afriride_phase13_global_execution",
        "phase12": phase12_status,
        "global_deployment_plan": deployment_plan,
        "controlled_ai_decision_engine": controlled_ai_decision_engine,
        "aws_production_infra": aws_production_infra,
        "real_execution_layer": real_execution_layer,
        "ai_optimization": ai_optimization,
        "novaconnect_expansion": novaconnect_expansion,
        "novapay_expansion": novapay_expansion,
        "summary": summary,
        "global_execution_score": global_execution_score,
        "readiness_band": readiness_band,
        "ready": ready,
        "projection_only": True,
        "read_only": True,
        "governance_linked": True,
        "creates_authority": False,
        "created_at": _now(),
    }


def build_phase13_status(
    *,
    organization_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    workspace = build_phase13_global_execution_workspace_projection(organization_id=org_id, limit=limit)
    summary = dict(workspace["summary"])
    summary["subscription_active"] = bool(_store().latest_active_subscription(organization_id=org_id))
    return {
        "view": "novaride_phase13_status",
        "phase": "13",
        "platform": "NovaRide Phase 13",
        "organization_id": org_id,
        "phase12": workspace["phase12"],
        "global_execution_workspace": workspace,
        "readiness": summary,
        "ready": bool(workspace["ready"]),
        "projection_only": True,
        "read_only": True,
        "governance_linked": True,
        "creates_authority": False,
    }


def build_phase13_contract_projection() -> dict[str, Any]:
    return {
        "view": "novaride_phase13_global_execution_contract",
        "status": "controlled_global_execution_ready",
        "role": "OPERATOR",
        "purpose": "Controlled execution bridge for global deployment planning, AWS infrastructure, AI decision gating, pricing optimization, logistics expansion, and NovaPay expansion.",
        "modules": [dict(module) for module in NOVARIDE_PHASE13_MODULES],
        "navigation": list(NOVARIDE_PHASE13_NAVIGATION),
        "rbac": {
            "role": "OPERATOR",
            "allowed": list(NOVARIDE_PHASE13_ALLOWED_ACTIONS),
            "forbidden": list(NOVARIDE_PHASE13_FORBIDDEN_ACTIONS),
        },
        "authority_model": {
            "global_deployment_plan": "projection_only",
            "controlled_ai_decision_engine": "projection_only",
            "aws_production_infra": "backend_controlled_plan",
            "real_execution_layer": "operator_acknowledged_control",
            "ai_optimization": "projection_only",
            "novaconnect_expansion": "replay_only_planned",
            "novapay_expansion": "backend_controlled",
        },
        "api_alignment": {
            "implemented": (
                "/v1/novaride/phase13/status",
                "/v1/novaride/phase13/global-deployment-plan",
                "/v1/novaride/phase13/controlled-ai-decision-engine",
                "/v1/novaride/phase13/aws-production-infra",
                "/v1/novaride/phase13/real-execution-layer",
                "/v1/novaride/phase13/ai-optimization",
                "/v1/novaride/phase13/nova-connect-expansion",
                "/v1/novaride/phase13/novapay-expansion",
                "/v1/novaride/phase13/controlled-execution",
            ),
            "contract": "/v1/novaride/phase13/global-execution-contract",
        },
        "ecosystem_integrations": {
            "phase12_global_scaling": "multi_city_projection",
            "aws_production_infra": "regional_runtime_stack",
            "controlled_ai_decision_engine": "bounded_action_bridge",
            "real_execution_layer": "operator_acknowledged_actions",
            "ai_optimization": "bounded_pricing_and_incentive_tuning",
            "novaconnect_expansion": "logistics_replay_surface",
            "novapay_expansion": "settlement_and_payment_rails",
        },
        "advanced_next_phase": (
            "city_state_automation",
            "global_safe_execution",
            "multi_product_expansion",
            "regional_autoscaling",
            "bounded_autonomous_operations",
        ),
    }


__all__ = [
    "PHASE13_TOPIC",
    "build_phase13_contract_projection",
    "build_phase13_global_execution_workspace_projection",
    "build_phase13_status",
]
