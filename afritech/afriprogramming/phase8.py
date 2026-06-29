"""NovaRide Phase 8 business and fleet systems.

This layer remains projection-only. It turns tenant-scoped organizations,
accounts, billing, fleet supply, rides, and revenue signals into enterprise
operations intelligence for fleet owners and business clients without mutating
runtime authority.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from afritech.afriprogramming.phase_common import DEFAULT_ORGANIZATION_ID, build_control_projection, get_phase_store, phase_now

from afritech.afriprogramming.phase4 import (
    build_business_budget_allocation_projection,
    build_business_profit_optimization_projection,
    build_phase4_status,
)
from afritech.afriprogramming.phase5 import build_phase5_status
from afritech.afriprogramming.phase6 import build_phase6_status
from afritech.afriprogramming.phase7 import build_phase7_analytics_intelligence_projection, build_phase7_status


PHASE8_TOPIC = "novaride.phase8.business_fleet_systems"


def _store():
    return get_phase_store()


def _now() -> str:
    return phase_now()


def _money_text(value: Decimal | int | str) -> str:
    return format(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), ".2f")


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


def _latest_zone(organization_id: str) -> str:
    snapshot = _store().latest_dashboard_analytics_snapshot(organization_id=organization_id)
    if snapshot is not None:
        payload = snapshot.get("payload", {})
        if isinstance(payload, dict):
            zone = payload.get("primary_zone") or payload.get("zone") or payload.get("demand_zone")
            if zone:
                return str(zone)
    drivers = _store().list_driver_presence(organization_id=organization_id, limit=1)
    if drivers:
        location = drivers[0].get("location") or {}
        label = str(location.get("label") or location.get("name") or location.get("city") or "").strip()
        if label:
            return label
    return "CBD"


def _organization_directory(organization_id: str, limit: int) -> list[dict[str, Any]]:
    return _store().list_organizations(organization_id=organization_id, limit=limit)


def _account_directory(organization_id: str, limit: int) -> list[dict[str, Any]]:
    return _store().list_accounts(organization_id=organization_id, limit=limit)


def _subscription_record(organization_id: str) -> dict[str, Any] | None:
    return _store().latest_subscription(organization_id=organization_id)


def _billing_records(organization_id: str, limit: int) -> list[dict[str, Any]]:
    return _store().list_billing_records(organization_id=organization_id, limit=limit)


def _usage_total(organization_id: str) -> int:
    return _store().count_usage(organization_id=organization_id)


def _latest_billing_preview(organization_id: str) -> dict[str, Any]:
    return build_control_projection("build_billing_preview", organization_id=organization_id)


def _business_accounts(accounts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [account for account in accounts if str(account.get("role")) in {"CLIENT", "ADMIN"}]


def _employee_accounts(accounts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [account for account in accounts if str(account.get("role")) in {"CUSTOMER", "CLIENT"}]


def _driver_accounts(accounts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [account for account in accounts if str(account.get("role")) == "DRIVER"]


def _fleet_summary(
    *,
    organization_id: str,
    accounts: list[dict[str, Any]],
    rides: list[dict[str, Any]],
    drivers: list[dict[str, Any]],
) -> dict[str, Any]:
    driver_accounts = _driver_accounts(accounts)
    active_drivers = [
        driver
        for driver in drivers
        if str(driver.get("status", "")).lower() in {"online", "busy"}
    ]
    busy_drivers = [driver for driver in drivers if str(driver.get("status", "")).lower() == "busy"]
    idle_drivers = [driver for driver in drivers if str(driver.get("status", "")).lower() == "online"]
    utilization_rate = round(len(busy_drivers) / max(1, len(active_drivers)), 6) if active_drivers else 0.0
    operational_rides = [
        ride
        for ride in rides
        if str(ride.get("status", "")).lower() in {"requested", "matched", "accepted", "arriving", "arrived", "in_progress", "completed"}
    ]
    proxy_vehicle_count = max(len(active_drivers), len(driver_accounts))
    proxy_vehicle_registry = [
        {
            "vehicle_id": f"vehicle-proxy-{driver.get('driver_id')}",
            "driver_id": driver.get("driver_id"),
            "status": driver.get("status", "offline"),
            "location": driver.get("location", {}),
            "source": "derived_from_driver_presence",
        }
        for driver in active_drivers[:20]
    ]
    coverage_zones = sorted(
        {
            str((driver.get("location") or {}).get("label") or (driver.get("location") or {}).get("city") or _latest_zone(organization_id))
            for driver in active_drivers
        }
    ) or [_latest_zone(organization_id)]
    trust_score = _safe_int(_store().latest_trust_score(organization_id=organization_id).get("trust_score") if _store().latest_trust_score(organization_id=organization_id) else 92)
    readiness_band = "enterprise_ready" if utilization_rate >= 0.5 and trust_score >= 90 else "growing" if active_drivers else "bootstrapping"
    return {
        "view": "novaride_phase8_fleet_summary",
        "fleet_mode": readiness_band,
        "vehicle_registry_mode": "derived_from_driver_supply" if proxy_vehicle_registry else "pending_vehicle_registry",
        "vehicle_count": proxy_vehicle_count,
        "proxy_vehicle_registry": proxy_vehicle_registry,
        "driver_count": len(driver_accounts) or len(drivers),
        "active_driver_count": len(active_drivers),
        "busy_driver_count": len(busy_drivers),
        "idle_driver_count": len(idle_drivers),
        "ride_count": len(operational_rides),
        "driver_utilization_rate": utilization_rate,
        "coverage_zones": coverage_zones,
        "primary_zone": coverage_zones[0] if coverage_zones else _latest_zone(organization_id),
        "trust_score": trust_score,
        "recommended_action": (
            "Maintain enterprise operating band."
            if readiness_band == "enterprise_ready"
            else "Grow fleet coverage and onboard additional vehicles."
        ),
        "projection_only": True,
        "read_only": True,
    }


def _corporate_accounts(
    *,
    organization_id: str,
    accounts: list[dict[str, Any]],
    organizations: list[dict[str, Any]],
) -> dict[str, Any]:
    business_accounts = _business_accounts(accounts)
    employee_accounts = _employee_accounts(accounts)
    organization_types = Counter(str(org.get("organization_type") or "business") for org in organizations)
    active_subscriptions = [
        sub
        for sub in (
            _store().latest_subscription(organization_id=organization_id),
        )
        if sub is not None and str(sub.get("status")) == "active"
    ]
    return {
        "view": "novaride_phase8_corporate_accounts",
        "business_account_count": len(business_accounts),
        "employee_account_count": len(employee_accounts),
        "organization_count": len(organizations),
        "organization_types": dict(organization_types),
        "active_subscriptions": active_subscriptions,
        "account_roles": Counter(str(account.get("role")) for account in accounts if account.get("role")),
        "tenant_directory": organizations,
        "projection_only": True,
        "read_only": True,
    }


def _employee_booking_surface(
    *,
    organization_id: str,
    accounts: list[dict[str, Any]],
    rides: list[dict[str, Any]],
) -> dict[str, Any]:
    employee_ids = {str(account.get("user_id")) for account in _employee_accounts(accounts) if str(account.get("user_id") or "").strip()}
    employee_rides = [ride for ride in rides if str(ride.get("passenger_id")) in employee_ids]
    scheduled_rides = [ride for ride in employee_rides if str(ride.get("status", "")).lower() in {"requested", "matched", "accepted", "arriving"}]
    completed_rides = [ride for ride in employee_rides if str(ride.get("status", "")).lower() == "completed"]
    cancelled_rides = [ride for ride in employee_rides if str(ride.get("status", "")).lower() == "cancelled"]
    completion_rate = round(len(completed_rides) / max(1, len(employee_rides)), 6) if employee_rides else 0.0
    cancellation_rate = round(len(cancelled_rides) / max(1, len(employee_rides)), 6) if employee_rides else 0.0
    policy_status = "within_budget" if completion_rate >= 0.5 and cancellation_rate <= 0.25 else "review"
    return {
        "view": "novaride_phase8_employee_booking",
        "employee_count": len(employee_ids),
        "ride_count": len(employee_rides),
        "scheduled_ride_count": len(scheduled_rides),
        "completed_ride_count": len(completed_rides),
        "cancelled_ride_count": len(cancelled_rides),
        "completion_rate": completion_rate,
        "cancellation_rate": cancellation_rate,
        "policy_status": policy_status,
        "recommended_action": (
            "Keep business ride approvals automated."
            if policy_status == "within_budget"
            else "Review policy exceptions and budget controls."
        ),
        "projection_only": True,
        "read_only": True,
    }


def _invoicing_projection(
    *,
    organization_id: str,
    accounts: list[dict[str, Any]],
    rides: list[dict[str, Any]],
) -> dict[str, Any]:
    billing_preview = _latest_billing_preview(organization_id)
    billing_records = _billing_records(organization_id, limit=100)
    subscription = _subscription_record(organization_id)
    subscription_plan = str((subscription or {}).get("plan") or billing_preview.get("plan") or "enterprise")
    account_count = len(_employee_accounts(accounts))
    ride_count = len(rides)
    estimated_amount = _safe_decimal(billing_preview.get("estimated_amount"))
    monthly_invoice_amount = estimated_amount + (_safe_decimal(ride_count) * Decimal("1.25")) + (_safe_decimal(account_count) * Decimal("0.85"))
    invoice_status = "open" if billing_records else "preview"
    invoice_items = [
        {
            "label": "Platform usage",
            "amount": billing_preview.get("estimated_amount", "0.00"),
        },
        {
            "label": "Employee ride usage",
            "amount": _money_text(_safe_decimal(ride_count) * Decimal("1.25")),
        },
        {
            "label": "Active account seat usage",
            "amount": _money_text(_safe_decimal(account_count) * Decimal("0.85")),
        },
    ]
    return {
        "view": "novaride_phase8_invoicing",
        "subscription_plan": subscription_plan,
        "billing_preview": billing_preview,
        "billing_records": billing_records,
        "invoice_status": invoice_status,
        "invoice_items": invoice_items,
        "estimated_monthly_invoice": _money_text(monthly_invoice_amount),
        "invoice_count": len(billing_records),
        "projection_only": True,
        "read_only": True,
    }


def _budgeting_projection(
    *,
    organization_id: str,
    limit: int,
) -> dict[str, Any]:
    budget = build_business_budget_allocation_projection(organization_id=organization_id, limit=limit)
    profit = build_business_profit_optimization_projection(organization_id=organization_id, limit=limit)
    return {
        "view": "novaride_phase8_budgeting",
        "budget_allocation": budget.get("budget_allocation", {}),
        "profit_optimization": profit.get("profit_optimization", {}),
        "city_signals": profit.get("city_signals", {}),
        "budget_policy": {
            "mode": budget.get("budget_allocation", {}).get("mode", "supervised"),
            "monthly_control": True,
            "tenant_scoped": True,
            "subscription_guarded": True,
        },
        "projection_only": True,
        "read_only": True,
    }


def _monthly_billing_projection(
    *,
    organization_id: str,
    limit: int,
) -> dict[str, Any]:
    billing_preview = _latest_billing_preview(organization_id)
    billing_records = _billing_records(organization_id, limit=limit)
    subscription = _subscription_record(organization_id)
    latest_record = billing_records[0] if billing_records else None
    total_billed = sum((_safe_decimal(record.get("estimated_amount")) for record in billing_records), Decimal("0.00"))
    return {
        "view": "novaride_phase8_monthly_billing",
        "billing_cycle": str((subscription or {}).get("billing_cycle") or "monthly"),
        "subscription": subscription,
        "billing_preview": billing_preview,
        "latest_billing_record": latest_record,
        "billing_records": billing_records,
        "monthly_billed_total": _money_text(total_billed if total_billed > 0 else _safe_decimal(billing_preview.get("estimated_amount"))),
        "invoice_status": "open" if billing_records else "preview",
        "projection_only": True,
        "read_only": True,
    }


def _adaptive_markets_projection(
    *,
    organization_id: str,
    limit: int,
) -> dict[str, Any]:
    phase7 = build_phase7_analytics_intelligence_projection(organization_id=organization_id, limit=limit)
    phase6 = build_phase6_status(organization_id=organization_id, limit=limit)
    phase5 = build_phase5_status(organization_id=organization_id, limit=limit)
    phase4 = build_phase4_status(organization_id=organization_id, limit=limit)
    reward_proxy = _safe_float(phase7.get("learning_engine", {}).get("rl_model", {}).get("reward_proxy"), 0.0)
    if phase6.get("ready", False) and phase5.get("ready", False) and reward_proxy >= 80:
        market_mode = "adaptive"
        execution_mode = "gradual_real_execution"
    elif reward_proxy >= 60:
        market_mode = "supervised"
        execution_mode = "policy_enforced_supervision"
    else:
        market_mode = "watch"
        execution_mode = "projection_only"
    city_budget = phase4.get("budget_allocation", {})
    return {
        "view": "novaride_phase8_adaptive_markets",
        "market_mode": market_mode,
        "execution_mode": execution_mode,
        "reward_proxy": round(reward_proxy, 4),
        "pricing_engine": phase7.get("analytics_dashboard", {}).get("navigation_intelligence", {}),
        "budget_engine": city_budget,
        "policy_enforcement": {
            "tenant_isolation_preserved": True,
            "subscription_required": True,
            "rbac_enforced": True,
            "billing_guarded": True,
            "no_provider_direct_access": True,
            "read_only": True,
        },
        "projection_only": True,
        "read_only": True,
    }


def _enterprise_revenue_streams(
    *,
    organization_id: str,
    accounts: list[dict[str, Any]],
    rides: list[dict[str, Any]],
    transactions: list[dict[str, Any]],
    billing_records: list[dict[str, Any]],
) -> dict[str, Any]:
    subscription = _subscription_record(organization_id)
    subscription_plan = str((subscription or {}).get("plan") or "enterprise")
    billed_amount = sum((_safe_decimal(record.get("estimated_amount")) for record in billing_records), Decimal("0.00"))
    ride_revenue = sum(
        (_safe_decimal(ride.get("final_fare", ride.get("fare_estimate", "0.00"))) for ride in rides if str(ride.get("status", "")).lower() == "completed"),
        Decimal("0.00"),
    )
    transaction_volume = sum((_safe_decimal(tx.get("amount")) for tx in transactions), Decimal("0.00"))
    employee_count = len(_employee_accounts(accounts))
    fleet_count = len(_driver_accounts(accounts))
    usage_total = _usage_total(organization_id)
    revenue_stream_total = (billed_amount + ride_revenue + transaction_volume).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    stream_mix = {
        "subscription": _money_text(billed_amount),
        "ride_revenue": _money_text(ride_revenue),
        "transaction_volume": _money_text(transaction_volume),
        "usage_proxy": usage_total,
    }
    return {
        "view": "novaride_phase8_enterprise_revenue_streams",
        "subscription_plan": subscription_plan,
        "employee_count": employee_count,
        "fleet_account_count": fleet_count,
        "usage_total": usage_total,
        "billing_records": len(billing_records),
        "revenue_stream_total": _money_text(revenue_stream_total),
        "stream_mix": stream_mix,
        "enterprise_revenue_streams": [
            "subscription_revenue",
            "monthly_billing",
            "employee_ride_booking",
            "fleet_operations",
            "usage_based_billing",
        ],
        "projection_only": True,
        "read_only": True,
    }


def build_phase8_business_fleet_projection(
    *,
    organization_id: str,
    limit: int = 100,
    source: str | None = "afriride_operator_dashboard",
) -> dict[str, Any]:
    organizations = _organization_directory(organization_id, limit)
    accounts = _account_directory(organization_id, limit)
    rides = _store().list_rides(organization_id=organization_id, limit=limit)
    drivers = _store().list_driver_presence(organization_id=organization_id, limit=limit)
    transactions = _store().list_transactions(organization_id=organization_id, limit=limit)
    billing_records = _billing_records(organization_id, limit=limit)
    fleet_summary = _fleet_summary(organization_id=organization_id, accounts=accounts, rides=rides, drivers=drivers)
    corporate_accounts = _corporate_accounts(organization_id=organization_id, accounts=accounts, organizations=organizations)
    employee_booking = _employee_booking_surface(organization_id=organization_id, accounts=accounts, rides=rides)
    invoicing = _invoicing_projection(organization_id=organization_id, accounts=accounts, rides=rides)
    budgeting = _budgeting_projection(organization_id=organization_id, limit=limit)
    monthly_billing = _monthly_billing_projection(organization_id=organization_id, limit=limit)
    adaptive_markets = _adaptive_markets_projection(organization_id=organization_id, limit=limit)
    enterprise_revenue_streams = _enterprise_revenue_streams(
        organization_id=organization_id,
        accounts=accounts,
        rides=rides,
        transactions=transactions,
        billing_records=billing_records,
    )
    phase7 = build_phase7_status(organization_id=organization_id, limit=limit)
    phase6 = build_phase6_status(organization_id=organization_id, limit=limit)
    phase5 = build_phase5_status(organization_id=organization_id, limit=limit)
    phase4 = build_phase4_status(organization_id=organization_id, limit=limit)
    enterprise_learning = build_phase7_analytics_intelligence_projection(organization_id=organization_id, limit=limit)

    policy_enforcement = {
        "tenant_isolation_preserved": True,
        "subscription_required": True,
        "rbac_enforced": True,
        "billing_guarded": True,
        "audit_replay_linked": True,
        "no_provider_direct_access": True,
        "no_dispatch_override": True,
        "read_only": True,
    }
    real_execution = {
        "mode": adaptive_markets["execution_mode"],
        "optional_future": "true_autonomy",
        "gradual_real_execution": adaptive_markets["execution_mode"] == "gradual_real_execution",
        "policy_enforcement": policy_enforcement,
        "safe_limits": {
            "projection_only": True,
            "read_only": True,
            "tenant_isolation_preserved": True,
            "subscription_required": True,
        },
        "recommended_boundary": (
            "Proceed with supervised enterprise automation."
            if adaptive_markets["market_mode"] in {"adaptive", "supervised"}
            else "Hold execution and collect more enterprise evidence."
        ),
    }

    return {
        "view": "novaride_phase8_business_fleet_systems",
        "phase": "8",
        "platform": "NovaRide Phase 8",
        "organization_id": organization_id,
        "source": source or "afriride_operator_dashboard",
        "phase4": phase4,
        "phase5": phase5,
        "phase6": phase6,
        "phase7": phase7,
        "fleet_summary": fleet_summary,
        "corporate_accounts": corporate_accounts,
        "employee_booking": employee_booking,
        "invoicing": invoicing,
        "budgeting": budgeting,
        "monthly_billing": monthly_billing,
        "adaptive_markets": adaptive_markets,
        "policy_enforcement": policy_enforcement,
        "real_execution": real_execution,
        "enterprise_revenue_streams": enterprise_revenue_streams,
        "enterprise_learning": enterprise_learning,
        "projection_only": True,
        "read_only": True,
        "governance_linked": True,
        "creates_authority": False,
        "created_at": _now(),
    }


def build_phase8_status(
    *,
    organization_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    projection = build_phase8_business_fleet_projection(organization_id=org_id, limit=limit)
    readiness = {
        "phase4_ready": bool(projection["phase4"].get("ready", False)),
        "phase5_ready": bool(projection["phase5"].get("ready", False)),
        "phase6_ready": bool(projection["phase6"].get("ready", False)),
        "phase7_ready": bool(projection["phase7"].get("ready", False)),
        "fleet_summary_ready": bool(projection["fleet_summary"].get("vehicle_count") is not None),
        "corporate_accounts_ready": bool(projection["corporate_accounts"].get("organization_count") is not None),
        "employee_booking_ready": bool(projection["employee_booking"].get("employee_count") is not None),
        "invoicing_ready": bool(projection["invoicing"].get("invoice_status")),
        "budgeting_ready": bool(projection["budgeting"].get("budget_allocation")),
        "monthly_billing_ready": bool(projection["monthly_billing"].get("billing_cycle")),
        "adaptive_markets_ready": bool(projection["adaptive_markets"].get("market_mode")),
        "policy_enforcement_ready": bool(projection["policy_enforcement"].get("tenant_isolation_preserved")),
        "enterprise_revenue_ready": bool(projection["enterprise_revenue_streams"].get("revenue_stream_total")),
        "tenant_isolation_preserved": True,
    }
    ready = all(
        readiness[key]
        for key in (
            "fleet_summary_ready",
            "corporate_accounts_ready",
            "employee_booking_ready",
            "invoicing_ready",
            "budgeting_ready",
            "monthly_billing_ready",
            "adaptive_markets_ready",
            "policy_enforcement_ready",
            "enterprise_revenue_ready",
            "tenant_isolation_preserved",
        )
    )
    return {
        "view": "novaride_phase8_status",
        "phase": "8",
        "platform": "NovaRide Phase 8",
        "organization_id": org_id,
        "phase4": projection["phase4"],
        "phase5": projection["phase5"],
        "phase6": projection["phase6"],
        "phase7": projection["phase7"],
        "business_fleet": projection,
        "readiness": readiness,
        "ready": ready,
        "projection_only": True,
        "read_only": True,
        "governance_linked": True,
        "creates_authority": False,
    }


def build_phase8_enterprise_revenue_projection(
    *,
    organization_id: str,
    limit: int = 100,
    source: str | None = "afriride_operator_dashboard",
) -> dict[str, Any]:
    projection = build_phase8_business_fleet_projection(organization_id=organization_id, limit=limit, source=source)
    return {
        "view": "novaride_phase8_enterprise_revenue",
        "organization_id": organization_id,
        "source": source or "afriride_operator_dashboard",
        "enterprise_revenue_streams": projection["enterprise_revenue_streams"],
        "monthly_billing": projection["monthly_billing"],
        "invoicing": projection["invoicing"],
        "fleet_summary": projection["fleet_summary"],
        "corporate_accounts": projection["corporate_accounts"],
        "employee_booking": projection["employee_booking"],
        "adaptive_markets": projection["adaptive_markets"],
        "policy_enforcement": projection["policy_enforcement"],
        "real_execution": projection["real_execution"],
        "projection_only": True,
        "read_only": True,
        "governance_linked": True,
        "creates_authority": False,
        "created_at": projection["created_at"],
    }


__all__ = [
    "PHASE8_TOPIC",
    "build_phase8_business_fleet_projection",
    "build_phase8_enterprise_revenue_projection",
    "build_phase8_status",
]
