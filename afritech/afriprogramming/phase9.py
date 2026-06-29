"""NovaRide Phase 9 partner ecosystem.

This layer remains projection-only. It turns tenant-scoped partner tenants,
guest booking activity, bulk scheduling signals, billing previews, and partner
integrations into a controlled B2B/B2B2C operations surface without granting
dispatch, pricing, or payment authority.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from afritech.afriprogramming.phase4 import (
    build_business_budget_allocation_projection,
    build_business_profit_optimization_projection,
    build_phase4_status,
)
from afritech.afriprogramming.phase5 import build_phase5_status
from afritech.afriprogramming.phase6 import build_phase6_status, build_navigation_maps_intelligence_projection
from afritech.afriprogramming.phase7 import build_phase7_analytics_intelligence_projection, build_phase7_status
from afritech.afriprogramming.phase8 import build_phase8_business_fleet_projection, build_phase8_status


PHASE9_TOPIC = "novaride.phase9.partner_ecosystem"


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


def _ride_directory(organization_id: str, limit: int) -> list[dict[str, Any]]:
    return _store().list_rides(organization_id=organization_id, limit=limit)


def _dispatch_directory(organization_id: str, limit: int) -> list[dict[str, Any]]:
    return _store().list_dispatch_assignments(organization_id=organization_id, limit=limit)


def _transaction_directory(organization_id: str, limit: int) -> list[dict[str, Any]]:
    return _store().list_transactions(organization_id=organization_id, limit=limit)


def _billing_records(organization_id: str, limit: int) -> list[dict[str, Any]]:
    return _store().list_billing_records(organization_id=organization_id, limit=limit)


def _integrations(organization_id: str, limit: int) -> list[dict[str, Any]]:
    return _store().list_integrations(organization_id=organization_id, limit=limit)


def _usage_events(organization_id: str, limit: int) -> list[dict[str, Any]]:
    return _store().list_usage_events(organization_id=organization_id, limit=limit)


def _partner_accounts(accounts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [account for account in accounts if str(account.get("role", "")).upper().startswith("PARTNER")]


def _guest_rides(rides: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [ride for ride in rides if str(ride.get("passenger_id", "")).startswith("guest-")]


def _usage_metric_total(events: list[dict[str, Any]], metric: str) -> int:
    return sum(int(event.get("amount") or 0) for event in events if str(event.get("metric")) == metric)


def _partner_portal_projection(
    *,
    organization_id: str,
    organizations: list[dict[str, Any]],
    accounts: list[dict[str, Any]],
    integrations: list[dict[str, Any]],
    usage_events: list[dict[str, Any]],
) -> dict[str, Any]:
    partner_accounts = _partner_accounts(accounts)
    partner_type = str((organizations[0].get("organization_type") if organizations else "partner") or "partner")
    booking_channels = sorted({str(item.get("type")) for item in integrations if item.get("type")})
    api_enabled = any(channel in {"api", "booking_api", "widget_api"} for channel in booking_channels)
    widget_enabled = any("widget" in channel for channel in booking_channels)
    bulk_requests = _usage_metric_total(usage_events, "partner_bulk_requests")
    guest_bookings = _usage_metric_total(usage_events, "partner_bookings")
    event_transport = _usage_metric_total(usage_events, "partner_event_transport")
    total_usage = sum(int(event.get("amount") or 0) for event in usage_events)
    return {
        "view": "novaride_phase9_partner_portal",
        "partner_type": partner_type,
        "partner_types": [
            "airports",
            "hotels",
            "event_organizers",
            "corporations",
            "travel_agencies",
        ],
        "partner_account_count": len(partner_accounts),
        "booking_channels": booking_channels,
        "booking_api_enabled": api_enabled,
        "booking_widget_enabled": widget_enabled,
        "guest_booking_volume": guest_bookings,
        "bulk_request_volume": bulk_requests,
        "event_transport_volume": event_transport,
        "usage_total": total_usage,
        "allowed_controls": [
            "book_guest_rides",
            "manage_bulk_transport",
            "view_reports_billing",
            "configure_booking_settings",
        ],
        "forbidden_controls": [
            "dispatch_logic_bypass",
            "direct_payment_processing",
            "pricing_rule_bypass",
            "direct_driver_access",
        ],
        "projection_only": True,
        "read_only": True,
    }


def _booking_api_projection(
    *,
    organization_id: str,
    rides: list[dict[str, Any]],
    usage_events: list[dict[str, Any]],
) -> dict[str, Any]:
    guest_rides = _guest_rides(rides)
    scheduled_rides = [ride for ride in guest_rides if str(ride.get("status", "")).lower() in {"requested", "matched", "accepted", "arriving"}]
    completed_rides = [ride for ride in guest_rides if str(ride.get("status", "")).lower() == "completed"]
    cancelled_rides = [ride for ride in guest_rides if str(ride.get("status", "")).lower() == "cancelled"]
    ride_status_counts = Counter(str(ride.get("status", "unknown")).lower() for ride in guest_rides)
    completion_rate = round(len(completed_rides) / max(1, len(guest_rides)), 6) if guest_rides else 0.0
    cancellation_rate = round(len(cancelled_rides) / max(1, len(guest_rides)), 6) if guest_rides else 0.0
    bulk_request_volume = _usage_metric_total(usage_events, "partner_bulk_requests")
    event_transport_volume = _usage_metric_total(usage_events, "partner_event_transport")
    api_booking_volume = _usage_metric_total(usage_events, "partner_bookings")
    average_wait_time_minutes = round(
        _clamp(
            6.0 + (cancellation_rate * 4.0) - (completion_rate * 2.5) - (event_transport_volume * 0.15),
            minimum=1.0,
            maximum=20.0,
        ),
        2,
    )
    return {
        "view": "novaride_phase9_booking_api",
        "guest_booking_volume": len(guest_rides) or api_booking_volume,
        "scheduled_booking_volume": len(scheduled_rides),
        "completed_booking_volume": len(completed_rides),
        "cancelled_booking_volume": len(cancelled_rides),
        "bulk_request_volume": bulk_request_volume,
        "event_transport_volume": event_transport_volume,
        "booking_api_volume": api_booking_volume,
        "ride_status_counts": dict(ride_status_counts),
        "completion_rate": completion_rate,
        "cancellation_rate": cancellation_rate,
        "average_wait_time_minutes": average_wait_time_minutes,
        "routing_mode": "backend_routed",
        "projection_only": True,
        "read_only": True,
    }


def _bulk_scheduling_projection(
    *,
    organization_id: str,
    rides: list[dict[str, Any]],
    usage_events: list[dict[str, Any]],
) -> dict[str, Any]:
    bulk_request_volume = _usage_metric_total(usage_events, "partner_bulk_requests")
    event_transport_volume = _usage_metric_total(usage_events, "partner_event_transport")
    ride_volume = len(rides)
    batch_size = max(1, bulk_request_volume + event_transport_volume)
    estimated_batches = max(1, (ride_volume + batch_size - 1) // batch_size)
    schedule_band = "high_volume" if ride_volume >= 5 or bulk_request_volume >= 3 else "moderate_volume" if ride_volume >= 2 else "pilot"
    return {
        "view": "novaride_phase9_bulk_scheduling",
        "ride_volume": ride_volume,
        "bulk_request_volume": bulk_request_volume,
        "event_transport_volume": event_transport_volume,
        "batch_size_proxy": batch_size,
        "estimated_batches": estimated_batches,
        "schedule_band": schedule_band,
        "recommendation": (
            "Use automated batch transport for recurring partner movements."
            if schedule_band != "pilot"
            else "Gather more ride volume before enabling large batch automation."
        ),
        "projection_only": True,
        "read_only": True,
    }


def _event_transport_projection(
    *,
    organization_id: str,
    rides: list[dict[str, Any]],
    usage_events: list[dict[str, Any]],
) -> dict[str, Any]:
    event_transport_volume = _usage_metric_total(usage_events, "partner_event_transport")
    guest_rides = _guest_rides(rides)
    event_rides = [ride for ride in guest_rides if str(ride.get("status", "")).lower() in {"requested", "matched", "accepted", "completed", "arriving"}]
    active_event_rides = [ride for ride in event_rides if str(ride.get("status", "")).lower() != "completed"]
    return {
        "view": "novaride_phase9_event_transport",
        "event_transport_volume": event_transport_volume,
        "event_ride_volume": len(event_rides) or event_transport_volume,
        "active_event_rides": len(active_event_rides),
        "transport_mode": "bulk_event_routing",
        "recommendation": (
            "Keep event rides on supervised live dispatch influence."
            if event_transport_volume > 0
            else "No event transport activity yet."
        ),
        "projection_only": True,
        "read_only": True,
    }


def _reporting_projection(
    *,
    organization_id: str,
    rides: list[dict[str, Any]],
    transactions: list[dict[str, Any]],
    dispatch_assignments: list[dict[str, Any]],
) -> dict[str, Any]:
    guest_rides = _guest_rides(rides)
    total_rides = len(guest_rides)
    completed_rides = [ride for ride in guest_rides if str(ride.get("status", "")).lower() == "completed"]
    cancelled_rides = [ride for ride in guest_rides if str(ride.get("status", "")).lower() == "cancelled"]
    completed_amount = sum((_safe_decimal(ride.get("final_fare", ride.get("fare_estimate", "0.00"))) for ride in completed_rides), Decimal("0.00"))
    transaction_volume = sum((_safe_decimal(tx.get("amount")) for tx in transactions), Decimal("0.00"))
    assigned_count = len([assignment for assignment in dispatch_assignments if str(assignment.get("status")) in {"assigned", "accepted"}])
    active_partner_zone = _latest_zone(organization_id)
    success_rate = round(len(completed_rides) / max(1, total_rides), 6) if total_rides else 0.0
    cancellation_rate = round(len(cancelled_rides) / max(1, total_rides), 6) if total_rides else 0.0
    average_wait_time = round(_clamp(5.5 + (cancellation_rate * 4.5) - (success_rate * 2.0), minimum=1.0, maximum=30.0), 2)
    return {
        "view": "novaride_phase9_partner_reporting",
        "rides_booked": total_rides,
        "completed_rides": len(completed_rides),
        "cancelled_rides": len(cancelled_rides),
        "ride_success_rate": success_rate,
        "cancellation_rate": cancellation_rate,
        "average_wait_time_minutes": average_wait_time,
        "popular_routes": [active_partner_zone],
        "active_zone": active_partner_zone,
        "assigned_count": assigned_count,
        "completed_amount": _money_text(completed_amount),
        "transaction_volume": _money_text(transaction_volume),
        "exports": ("csv", "excel"),
        "projection_only": True,
        "read_only": True,
    }


def _billing_projection(
    *,
    organization_id: str,
    rides: list[dict[str, Any]],
    usage_events: list[dict[str, Any]],
    billing_records: list[dict[str, Any]],
) -> dict[str, Any]:
    billing_preview = build_control_projection("build_billing_preview", organization_id=organization_id)
    subscription = _store().latest_subscription(organization_id=organization_id)
    guest_rides = _guest_rides(rides)
    bulk_request_volume = _usage_metric_total(usage_events, "partner_bulk_requests")
    event_transport_volume = _usage_metric_total(usage_events, "partner_event_transport")
    usage_total = sum(int(event.get("amount") or 0) for event in usage_events)
    estimated_amount = (
        _safe_decimal(billing_preview.get("estimated_amount"))
        + (Decimal(str(len(guest_rides))) * Decimal("0.85"))
        + (Decimal(str(bulk_request_volume)) * Decimal("4.25"))
        + (Decimal(str(event_transport_volume)) * Decimal("9.50"))
    )
    billing_mode = "postpaid_invoicing" if billing_records else "preview"
    return {
        "view": "novaride_phase9_partner_billing",
        "subscription_plan": str((subscription or {}).get("plan") or billing_preview.get("plan") or "enterprise"),
        "billing_mode": billing_mode,
        "billing_preview": billing_preview,
        "billing_records": billing_records,
        "guest_rides": len(guest_rides),
        "bulk_request_volume": bulk_request_volume,
        "event_transport_volume": event_transport_volume,
        "usage_total": usage_total,
        "estimated_monthly_invoice": _money_text(estimated_amount),
        "partner_wallet_mode": "backend_settled",
        "refund_path": "support_linked_novapay",
        "projection_only": True,
        "read_only": True,
    }


def _configuration_projection(
    *,
    organization_id: str,
    organizations: list[dict[str, Any]],
    accounts: list[dict[str, Any]],
    integrations: list[dict[str, Any]],
) -> dict[str, Any]:
    partner_accounts = _partner_accounts(accounts)
    organization_types = Counter(str(org.get("organization_type") or "partner") for org in organizations)
    integration_names = [str(item.get("name")) for item in integrations if item.get("name")]
    booking_widget_present = any("widget" in str(item.get("type", "")).lower() or "widget" in str(item.get("name", "")).lower() for item in integrations)
    api_present = any("api" in str(item.get("type", "")).lower() or "api" in str(item.get("name", "")).lower() for item in integrations)
    return {
        "view": "novaride_phase9_partner_configuration",
        "organization_types": dict(organization_types),
        "partner_accounts": len(partner_accounts),
        "integration_names": integration_names,
        "booking_widget_present": booking_widget_present,
        "api_present": api_present,
        "default_pickup_locations": [
            _latest_zone(organization_id),
        ],
        "preferred_ride_types": ["standard", "xl", "airport_pickup", "event_shuttle"],
        "white_label_widget_next_phase": True,
        "permission_levels": ["partner_admin", "partner_staff"],
        "projection_only": True,
        "read_only": True,
    }


def _live_dispatch_influence_projection(
    *,
    organization_id: str,
    rides: list[dict[str, Any]],
    usage_events: list[dict[str, Any]],
) -> dict[str, Any]:
    bulk_request_volume = _usage_metric_total(usage_events, "partner_bulk_requests")
    event_transport_volume = _usage_metric_total(usage_events, "partner_event_transport")
    guest_rides = _guest_rides(rides)
    partner_supply_pressure = len(guest_rides) + bulk_request_volume + event_transport_volume
    if partner_supply_pressure >= 6:
        influence_mode = "live_dispatch_influence"
        recommendation = "Feed partner demand into supervised dispatch positioning."
    elif partner_supply_pressure >= 3:
        influence_mode = "guided_dispatch_influence"
        recommendation = "Use partner demand to influence nearby supply, not dispatch authority."
    else:
        influence_mode = "watch_only"
        recommendation = "Collect more partner activity before influencing live dispatch."
    return {
        "view": "novaride_phase9_live_dispatch_influence",
        "influence_mode": influence_mode,
        "partner_supply_pressure": partner_supply_pressure,
        "recommendation": recommendation,
        "safe_thresholds": {
            "no_dispatch_override": True,
            "no_driver_direct_access": True,
            "no_provider_direct_access": True,
            "manual_confirmation_required": influence_mode != "live_dispatch_influence",
        },
        "projection_only": True,
        "read_only": True,
    }


def _automated_incentives_projection(
    *,
    organization_id: str,
    rides: list[dict[str, Any]],
    usage_events: list[dict[str, Any]],
) -> dict[str, Any]:
    guest_rides = _guest_rides(rides)
    completed_rides = [ride for ride in guest_rides if str(ride.get("status", "")).lower() == "completed"]
    completion_rate = round(len(completed_rides) / max(1, len(guest_rides)), 6) if guest_rides else 0.0
    bulk_request_volume = _usage_metric_total(usage_events, "partner_bulk_requests")
    event_transport_volume = _usage_metric_total(usage_events, "partner_event_transport")
    if completion_rate >= 0.8 and (bulk_request_volume + event_transport_volume) >= 3:
        incentive_band = "strong"
        incentive_pct = 8.0
    elif completion_rate >= 0.6:
        incentive_band = "moderate"
        incentive_pct = 4.5
    else:
        incentive_band = "guarded"
        incentive_pct = 2.0
    return {
        "view": "novaride_phase9_automated_incentives",
        "completion_rate": completion_rate,
        "bulk_request_volume": bulk_request_volume,
        "event_transport_volume": event_transport_volume,
        "incentive_band": incentive_band,
        "recommended_incentive_pct": incentive_pct,
        "recommendation": (
            "Enable partner bonuses and recurring transport incentives."
            if incentive_band == "strong"
            else "Keep incentives supervised and review campaign quality."
        ),
        "projection_only": True,
        "read_only": True,
    }


def _enterprise_automation_projection(
    *,
    organization_id: str,
    partner_portal: dict[str, Any],
    live_dispatch_influence: dict[str, Any],
    automated_incentives: dict[str, Any],
) -> dict[str, Any]:
    if live_dispatch_influence["influence_mode"] == "live_dispatch_influence" and automated_incentives["incentive_band"] == "strong":
        automation_mode = "partner_automation_ready"
    elif live_dispatch_influence["influence_mode"] == "guided_dispatch_influence":
        automation_mode = "partner_automation_supervised"
    else:
        automation_mode = "partner_automation_projection"
    return {
        "view": "novaride_phase9_enterprise_automation",
        "automation_mode": automation_mode,
        "partner_booking_api_enabled": bool(partner_portal["booking_api_enabled"]),
        "partner_booking_widget_enabled": bool(partner_portal["booking_widget_enabled"]),
        "live_dispatch_influence": live_dispatch_influence,
        "automated_incentives": automated_incentives,
        "safe_limits": {
            "projection_only": True,
            "read_only": True,
            "tenant_isolation_preserved": True,
            "subscription_required": True,
            "no_dispatch_override": True,
            "no_provider_direct_access": True,
        },
        "recommended_boundary": (
            "Proceed with supervised partner automation."
            if automation_mode != "partner_automation_projection"
            else "Hold execution and collect more partner evidence."
        ),
    }


def build_phase9_partner_ecosystem_projection(
    *,
    organization_id: str,
    limit: int = 100,
    source: str | None = "afriride_partner_portal",
) -> dict[str, Any]:
    organizations = _organization_directory(organization_id, limit)
    accounts = _account_directory(organization_id, limit)
    rides = _ride_directory(organization_id, limit)
    dispatch_assignments = _dispatch_directory(organization_id, limit)
    transactions = _transaction_directory(organization_id, limit)
    billing_records = _billing_records(organization_id, limit)
    integrations = _integrations(organization_id, limit)
    usage_events = _usage_events(organization_id, limit)

    phase4 = build_phase4_status(organization_id=organization_id, limit=limit)
    phase5 = build_phase5_status(organization_id=organization_id, limit=limit)
    phase6 = build_phase6_status(organization_id=organization_id, limit=limit)
    phase7 = build_phase7_status(organization_id=organization_id, limit=limit)
    phase8 = build_phase8_status(organization_id=organization_id, limit=limit)
    phase6_navigation = build_navigation_maps_intelligence_projection(organization_id=organization_id, limit=limit)
    phase7_learning = build_phase7_analytics_intelligence_projection(organization_id=organization_id, limit=limit)
    phase8_business_fleet = build_phase8_business_fleet_projection(organization_id=organization_id, limit=limit)

    partner_portal = _partner_portal_projection(
        organization_id=organization_id,
        organizations=organizations,
        accounts=accounts,
        integrations=integrations,
        usage_events=usage_events,
    )
    bookings = _booking_api_projection(organization_id=organization_id, rides=rides, usage_events=usage_events)
    bulk_scheduling = _bulk_scheduling_projection(organization_id=organization_id, rides=rides, usage_events=usage_events)
    event_transport = _event_transport_projection(organization_id=organization_id, rides=rides, usage_events=usage_events)
    reporting = _reporting_projection(
        organization_id=organization_id,
        rides=rides,
        transactions=transactions,
        dispatch_assignments=dispatch_assignments,
    )
    billing = _billing_projection(
        organization_id=organization_id,
        rides=rides,
        usage_events=usage_events,
        billing_records=billing_records,
    )
    configuration = _configuration_projection(
        organization_id=organization_id,
        organizations=organizations,
        accounts=accounts,
        integrations=integrations,
    )
    live_dispatch_influence = _live_dispatch_influence_projection(
        organization_id=organization_id,
        rides=rides,
        usage_events=usage_events,
    )
    automated_incentives = _automated_incentives_projection(
        organization_id=organization_id,
        rides=rides,
        usage_events=usage_events,
    )
    enterprise_automation = _enterprise_automation_projection(
        organization_id=organization_id,
        partner_portal=partner_portal,
        live_dispatch_influence=live_dispatch_influence,
        automated_incentives=automated_incentives,
    )

    partner_volume = bookings["guest_booking_volume"] + bookings["bulk_request_volume"] + bookings["event_transport_volume"]
    ready = (
        bool(phase8.get("ready", False))
        and bool(partner_portal["booking_api_enabled"])
        and bool(partner_portal["partner_account_count"] >= 1)
        and partner_volume >= 1
    )

    return {
        "view": "novaride_phase9_partner_ecosystem",
        "phase": "9",
        "platform": "NovaRide Phase 9",
        "organization_id": organization_id,
        "source": source or "afriride_partner_portal",
        "phase4": phase4,
        "phase5": phase5,
        "phase6": phase6,
        "phase7": phase7,
        "phase8": phase8,
        "partner_portal": partner_portal,
        "bookings": bookings,
        "bulk_scheduling": bulk_scheduling,
        "event_transport": event_transport,
        "reporting": reporting,
        "billing": billing,
        "configuration": configuration,
        "live_dispatch_influence": live_dispatch_influence,
        "automated_incentives": automated_incentives,
        "enterprise_automation": enterprise_automation,
        "phase6_navigation": phase6_navigation,
        "phase7_learning": phase7_learning,
        "phase8_business_fleet": phase8_business_fleet,
        "projection_only": True,
        "read_only": True,
        "governance_linked": True,
        "creates_authority": False,
        "created_at": _now(),
        "ready": ready,
    }


def build_phase9_status(
    *,
    organization_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    projection = build_phase9_partner_ecosystem_projection(organization_id=org_id, limit=limit)
    readiness = {
        "phase4_ready": bool(projection["phase4"].get("ready", False)),
        "phase5_ready": bool(projection["phase5"].get("ready", False)),
        "phase6_ready": bool(projection["phase6"].get("ready", False)),
        "phase7_ready": bool(projection["phase7"].get("ready", False)),
        "phase8_ready": bool(projection["phase8"].get("ready", False)),
        "partner_portal_ready": bool(projection["partner_portal"].get("booking_api_enabled")),
        "booking_api_ready": bool(projection["bookings"].get("guest_booking_volume") is not None),
        "bulk_scheduling_ready": bool(projection["bulk_scheduling"].get("estimated_batches") is not None),
        "event_transport_ready": bool(projection["event_transport"].get("event_transport_volume") is not None),
        "reporting_ready": bool(projection["reporting"].get("rides_booked") is not None),
        "billing_ready": bool(projection["billing"].get("billing_mode")),
        "configuration_ready": bool(projection["configuration"].get("api_present") is not None),
        "live_dispatch_influence_ready": bool(projection["live_dispatch_influence"].get("influence_mode")),
        "automated_incentives_ready": bool(projection["automated_incentives"].get("incentive_band")),
        "enterprise_automation_ready": bool(projection["enterprise_automation"].get("automation_mode")),
        "tenant_isolation_preserved": True,
    }
    ready = all(
        readiness[key]
        for key in (
            "partner_portal_ready",
            "booking_api_ready",
            "bulk_scheduling_ready",
            "event_transport_ready",
            "reporting_ready",
            "billing_ready",
            "configuration_ready",
            "live_dispatch_influence_ready",
            "automated_incentives_ready",
            "enterprise_automation_ready",
            "tenant_isolation_preserved",
        )
    )
    return {
        "view": "novaride_phase9_status",
        "phase": "9",
        "platform": "NovaRide Phase 9",
        "organization_id": org_id,
        "phase4": projection["phase4"],
        "phase5": projection["phase5"],
        "phase6": projection["phase6"],
        "phase7": projection["phase7"],
        "phase8": projection["phase8"],
        "partner_ecosystem": projection,
        "readiness": readiness,
        "ready": ready,
        "projection_only": True,
        "read_only": True,
        "governance_linked": True,
        "creates_authority": False,
    }


def build_phase9_partner_revenue_projection(
    *,
    organization_id: str,
    limit: int = 100,
    source: str | None = "afriride_partner_portal",
) -> dict[str, Any]:
    projection = build_phase9_partner_ecosystem_projection(organization_id=organization_id, limit=limit, source=source)
    revenue_proxy = _safe_decimal(projection["billing"].get("estimated_monthly_invoice"))
    revenue_proxy += _safe_decimal(projection["reporting"].get("completed_amount"))
    revenue_proxy += _safe_decimal(projection["reporting"].get("transaction_volume"))
    return {
        "view": "novaride_phase9_partner_revenue",
        "organization_id": organization_id,
        "source": source or "afriride_partner_portal",
        "partner_portal": projection["partner_portal"],
        "bookings": projection["bookings"],
        "bulk_scheduling": projection["bulk_scheduling"],
        "event_transport": projection["event_transport"],
        "reporting": projection["reporting"],
        "billing": projection["billing"],
        "live_dispatch_influence": projection["live_dispatch_influence"],
        "automated_incentives": projection["automated_incentives"],
        "enterprise_automation": projection["enterprise_automation"],
        "revenue_proxy": _money_text(revenue_proxy),
        "projection_only": True,
        "read_only": True,
        "governance_linked": True,
        "creates_authority": False,
        "created_at": projection["created_at"],
    }


__all__ = [
    "PHASE9_TOPIC",
    "build_phase9_partner_ecosystem_projection",
    "build_phase9_partner_revenue_projection",
    "build_phase9_status",
]
