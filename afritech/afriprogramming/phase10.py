"""NovaRide Phase 10 support and dispute system.

This layer remains projection-only. It turns tenant-scoped audit events, rides,
transactions, dispatch assignments, trust snapshots, and billing context into a
controlled support surface for tickets, refunds, disputes, escalations, and
ride investigations without mutating refund or payment authority.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from afritech.afriprogramming.phase_common import DEFAULT_ORGANIZATION_ID, build_control_projection, get_phase_store, phase_now

from afritech.afriprogramming.phase9 import build_phase9_status


PHASE10_TOPIC = "novaride.phase10.support_dispute_system"

NOVARIDE_SUPPORT_TICKET_STATUSES = ("open", "in_progress", "resolved", "closed")
NOVARIDE_SUPPORT_ESCALATION_LEVELS = (
    {"level": "level_1", "meaning": "standard_support"},
    {"level": "level_2", "meaning": "supervisor_review"},
    {"level": "level_3", "meaning": "critical_admin_review"},
)
NOVARIDE_SUPPORT_ALLOWED_ACTIONS = (
    "view_ride_data",
    "manage_tickets",
    "request_refunds",
    "contact_users",
    "escalate_cases",
)
NOVARIDE_SUPPORT_FORBIDDEN_ACTIONS = (
    "bypass_novapay",
    "mutate_pricing_rules",
    "bypass_audit_logs",
    "directly_execute_payments",
)
NOVARIDE_SUPPORT_MODULES = (
    {
        "key": "customer_ticket_management",
        "name": "Customer Ticket Management",
        "purpose": "Create, triage, assign, resolve, and close passenger, driver, and operator tickets.",
    },
    {
        "key": "ride_lookup_investigation",
        "name": "Ride Lookup & Investigation",
        "purpose": "Search rides, inspect details, and review replay evidence for support decisions.",
    },
    {
        "key": "refund_dispute_handling",
        "name": "Refund & Dispute Handling",
        "purpose": "Review refund requests, verify fares, and route approved refund requests through NovaPay.",
    },
    {
        "key": "driver_and_passenger_assistance",
        "name": "Driver & Passenger Assistance",
        "purpose": "Coordinate user assistance without exposing payment or dispatch authority.",
    },
    {
        "key": "escalation_management",
        "name": "Escalation Management",
        "purpose": "Route high-priority support issues to supervisors, admins, Trust, or audit review.",
    },
    {
        "key": "audit_and_replay_integration",
        "name": "Audit & Replay Integration",
        "purpose": "Make every support decision verifiable through ride, route, timing, pricing, and payment evidence.",
    },
)
NOVARIDE_SUPPORT_NAVIGATION = (
    "workspace",
    "tickets",
    "refunds",
    "disputes",
    "ride_lookup",
    "escalations",
    "replay_evidence",
    "customer_experience",
)
NOVARIDE_SUPPORT_WORKFLOW = (
    "ticket_created",
    "support_agent_reviews_ride",
    "verify_fare_and_replay",
    "decide_refund_or_action",
    "novapay_processes_refund",
    "ticket_closed",
)

_TICKET_EVENT_TYPES = {
    "support_ticket_created",
    "support_ticket_assigned",
    "support_ticket_updated",
    "support_ticket_in_progress",
    "support_ticket_resolved",
    "support_ticket_closed",
}
_REFUND_EVENT_TYPES = {
    "refund_requested",
    "refund_reviewed",
    "refund_approved",
    "refund_rejected",
    "refund_processed",
}
_DISPUTE_EVENT_TYPES = {
    "dispute_opened",
    "dispute_reviewed",
    "dispute_resolved",
    "dispute_escalated",
}
_INVESTIGATION_EVENT_TYPES = {
    "ride_investigation_opened",
    "ride_investigation_reviewed",
    "ride_investigation_closed",
    "support_ride_lookup",
}
_ESCALATION_EVENT_TYPES = {
    "support_escalated",
    "escalation_created",
    "escalation_routed",
    "case_escalated",
}


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


def _money_text(value: Decimal | int | str) -> str:
    return format(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), ".2f")


def _clamp(value: float, *, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


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


def _event_blob(event: dict[str, Any]) -> str:
    payload = event.get("payload", {})
    return " ".join(
        str(value).lower()
        for value in (
            event.get("event_type"),
            event.get("target"),
            event.get("status"),
            payload,
        )
        if value is not None
    )


def _looks_support_related(event: dict[str, Any]) -> bool:
    event_type = str(event.get("event_type", "")).lower()
    if event_type in _TICKET_EVENT_TYPES | _REFUND_EVENT_TYPES | _DISPUTE_EVENT_TYPES | _INVESTIGATION_EVENT_TYPES | _ESCALATION_EVENT_TYPES:
        return True
    blob = _event_blob(event)
    keywords = ("support", "refund", "dispute", "investigation", "replay", "escalat", "ticket")
    return any(keyword in blob for keyword in keywords)


def _canonical_status(value: Any, *, default: str = "open") -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"", "new", "created"}:
        return default
    if normalized in {"pending", "open", "queued"}:
        return "open"
    if normalized in {"assigned", "reviewing", "triaging", "investigating", "in_progress", "in-progress"}:
        return "in_progress"
    if normalized in {"approved", "accepted"}:
        return "approved"
    if normalized in {"rejected", "denied", "declined"}:
        return "rejected"
    if normalized in {"resolved", "resolved_with_refund", "resolved_with_credit"}:
        return "resolved"
    if normalized in {"closed", "complete", "completed"}:
        return "closed"
    if normalized.startswith("level_"):
        return normalized
    return normalized or default


def _support_events(organization_id: str, limit: int) -> list[dict[str, Any]]:
    events = _store().list_audit_events(organization_id=organization_id, limit=limit)
    return [event for event in events if _looks_support_related(event)]


def _rides(organization_id: str, limit: int) -> list[dict[str, Any]]:
    return _store().list_rides(organization_id=organization_id, limit=limit)


def _transactions(organization_id: str, limit: int) -> list[dict[str, Any]]:
    return _store().list_transactions(organization_id=organization_id, limit=limit)


def _dispatch_assignments(organization_id: str, limit: int) -> list[dict[str, Any]]:
    return _store().list_dispatch_assignments(organization_id=organization_id, limit=limit)


def _billing_records(organization_id: str, limit: int) -> list[dict[str, Any]]:
    return _store().list_billing_records(organization_id=organization_id, limit=limit)


def _organization_trust(organization_id: str) -> dict[str, Any] | None:
    return _store().latest_trust_score(organization_id=organization_id)


def _group_support_cases(
    events: list[dict[str, Any]],
    *,
    case_key: str,
    type_name: str,
    status_default: str = "open",
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            payload = {}
        case_id = (
            str(payload.get(case_key) or payload.get("case_id") or payload.get("id") or event.get("target") or "").strip()
        )
        if not case_id:
            continue
        grouped[case_id].append(event)

    cases: list[dict[str, Any]] = []
    for case_id, history in grouped.items():
        history.sort(key=lambda row: _parse_timestamp(row.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc))
        first_event = history[0]
        last_event = history[-1]
        first_ts = _parse_timestamp(first_event.get("created_at"))
        last_ts = _parse_timestamp(last_event.get("created_at"))
        duration_minutes = 0.0
        if first_ts is not None and last_ts is not None:
            duration_minutes = max(0.0, (last_ts - first_ts).total_seconds() / 60.0)
        payload = last_event.get("payload", {})
        if not isinstance(payload, dict):
            payload = {}
        status = _canonical_status(last_event.get("status"), default=status_default)
        priority = str(payload.get("priority") or payload.get("severity") or "medium").lower()
        ride_id = str(payload.get("ride_id") or payload.get("rideId") or payload.get("linked_ride_id") or "")
        cases.append(
            {
                f"{type_name}_id": case_id,
                "ride_id": ride_id or None,
                "latest_status": status,
                "priority": priority,
                "category": str(payload.get("category") or payload.get("reason") or payload.get("issue_type") or type_name).lower(),
                "first_seen_at": first_event.get("created_at"),
                "last_updated_at": last_event.get("created_at"),
                "duration_minutes": round(duration_minutes, 2),
                "evidence_count": len(history),
                "history": history,
                "payload": payload,
                "case_type": type_name,
            }
        )

    cases.sort(
        key=lambda row: (
            row["last_updated_at"] or "",
            row["duration_minutes"],
            row["evidence_count"],
        ),
        reverse=True,
    )
    return cases


def _ticket_queue_projection(*, organization_id: str, events: list[dict[str, Any]], rides: list[dict[str, Any]], limit: int) -> dict[str, Any]:
    ticket_events = [event for event in events if str(event.get("event_type", "")).lower() in _TICKET_EVENT_TYPES]
    ticket_cases = _group_support_cases(ticket_events, case_key="ticket_id", type_name="ticket")

    if not ticket_cases:
        inferred = [
            {
                "ticket_id": f"ticket-inferred-{ride['ride_id']}",
                "ride_id": ride["ride_id"],
                "latest_status": "open" if str(ride.get("status", "")).lower() in {"cancelled", "requested", "matched"} else "resolved",
                "priority": "medium",
                "category": "ride_issue",
                "first_seen_at": ride.get("created_at"),
                "last_updated_at": ride.get("updated_at"),
                "duration_minutes": 0.0,
                "evidence_count": 1,
                "history": [],
                "payload": {"source": "inferred_from_ride", "ride_id": ride["ride_id"]},
                "case_type": "ticket",
            }
            for ride in rides[:limit]
            if str(ride.get("status", "")).lower() in {"cancelled", "completed"}
        ]
        ticket_cases = inferred

    status_counts = Counter(case["latest_status"] for case in ticket_cases)
    priority_counts = Counter(case["priority"] for case in ticket_cases)
    category_counts = Counter(case["category"] for case in ticket_cases)
    open_pressure = status_counts.get("open", 0) + status_counts.get("in_progress", 0)
    resolution_rate = round(
        (status_counts.get("resolved", 0) + status_counts.get("closed", 0)) / max(1, len(ticket_cases)),
        6,
    )
    first_response_minutes = round(
        sum(case["duration_minutes"] for case in ticket_cases if case["evidence_count"] > 1) / max(1, sum(1 for case in ticket_cases if case["evidence_count"] > 1)),
        2,
    )
    support_band = "healthy" if resolution_rate >= 0.75 and open_pressure <= 2 else "watch" if resolution_rate >= 0.5 else "critical"
    return {
        "view": "novaride_phase10_tickets",
        "ticket_total": len(ticket_cases),
        "ticket_status_counts": dict(status_counts),
        "ticket_priority_counts": dict(priority_counts),
        "ticket_category_counts": dict(category_counts),
        "open_pressure": open_pressure,
        "resolution_rate": resolution_rate,
        "first_response_minutes_proxy": first_response_minutes,
        "support_band": support_band,
        "queue_health": "stable" if support_band == "healthy" else "needs_attention",
        "tickets": ticket_cases[:limit],
        "projection_only": True,
        "read_only": True,
    }


def _refund_projection(*, organization_id: str, events: list[dict[str, Any]], rides: list[dict[str, Any]], transactions: list[dict[str, Any]], limit: int) -> dict[str, Any]:
    refund_events = [event for event in events if str(event.get("event_type", "")).lower() in _REFUND_EVENT_TYPES]
    refund_cases = _group_support_cases(refund_events, case_key="refund_id", type_name="refund", status_default="open")
    refund_status_counts = Counter(case["latest_status"] for case in refund_cases)
    approved = refund_status_counts.get("approved", 0)
    rejected = refund_status_counts.get("rejected", 0)
    pending = refund_status_counts.get("open", 0) + refund_status_counts.get("in_progress", 0)

    tx_by_ride: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for transaction in transactions:
        tx_by_ride[str(transaction.get("ride_id"))].append(transaction)

    ride_lookup = {str(ride.get("ride_id")): ride for ride in rides}
    suggested_total = Decimal("0.00")
    suggested_cases: list[dict[str, Any]] = []
    for case in refund_cases:
        payload = case.get("payload", {})
        ride_id = str(case.get("ride_id") or payload.get("ride_id") or "")
        ride = ride_lookup.get(ride_id)
        suggested = Decimal("0.00")
        if ride is not None:
            fare_estimate = _safe_decimal(ride.get("fare_estimate"))
            final_fare = _safe_decimal(ride.get("final_fare", ride.get("fare_estimate")))
            if str(ride.get("status", "")).lower() == "cancelled":
                debit_total = sum(
                    _safe_decimal(tx.get("amount"))
                    for tx in tx_by_ride.get(ride_id, [])
                    if str(tx.get("type", "")).lower() == "debit"
                )
                suggested = max(suggested, debit_total)
            elif final_fare > fare_estimate:
                suggested = max(suggested, final_fare - fare_estimate)
        suggested_total += suggested
        suggested_cases.append(
            {
                **case,
                "suggested_refund_amount": _money_text(suggested),
                "linked_transaction_count": len(tx_by_ride.get(ride_id, [])),
            }
        )

    billing_record = _store().latest_billing_record(organization_id=organization_id)
    refund_authority = "NovaPay_backend_only"
    return {
        "view": "novaride_phase10_refunds",
        "refund_total": len(refund_cases),
        "refund_status_counts": dict(refund_status_counts),
        "approved_refund_count": approved,
        "rejected_refund_count": rejected,
        "pending_refund_count": pending,
        "suggested_refund_total": _money_text(suggested_total),
        "refund_authority": refund_authority,
        "pricing_validation": "required",
        "audit_replay": "required",
        "billing_reference": billing_record,
        "refund_cases": suggested_cases[:limit],
        "projection_only": True,
        "read_only": True,
    }


def _dispute_projection(*, organization_id: str, events: list[dict[str, Any]], rides: list[dict[str, Any]], transactions: list[dict[str, Any]], limit: int) -> dict[str, Any]:
    dispute_events = [event for event in events if str(event.get("event_type", "")).lower() in _DISPUTE_EVENT_TYPES]
    dispute_cases = _group_support_cases(dispute_events, case_key="dispute_id", type_name="dispute", status_default="open")
    dispute_status_counts = Counter(case["latest_status"] for case in dispute_cases)
    ride_lookup = {str(ride.get("ride_id")): ride for ride in rides}
    transactions_by_ride: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for transaction in transactions:
        transactions_by_ride[str(transaction.get("ride_id"))].append(transaction)

    audit_verified = bool(_store().verify_audit_chain(organization_id=organization_id))
    enriched_cases: list[dict[str, Any]] = []
    evidence_ready_count = 0
    for case in dispute_cases:
        payload = case.get("payload", {})
        ride_id = str(case.get("ride_id") or payload.get("ride_id") or "")
        ride = ride_lookup.get(ride_id)
        evidence_ready = bool(ride) and audit_verified and bool(transactions_by_ride.get(ride_id))
        if evidence_ready:
            evidence_ready_count += 1
        enriched_cases.append(
            {
                **case,
                "ride_status": ride.get("status") if ride else None,
                "transaction_count": len(transactions_by_ride.get(ride_id, [])),
                "evidence_ready": evidence_ready,
                "recommended_path": "replay_review" if evidence_ready else "collect_more_evidence",
            }
        )

    resolution_band = (
        "verified"
        if dispute_status_counts.get("resolved", 0) >= max(1, len(dispute_cases) // 2) and audit_verified
        else "review"
        if dispute_cases
        else "idle"
    )
    return {
        "view": "novaride_phase10_disputes",
        "dispute_total": len(dispute_cases),
        "dispute_status_counts": dict(dispute_status_counts),
        "evidence_ready_count": evidence_ready_count,
        "audit_chain_verified": audit_verified,
        "resolution_band": resolution_band,
        "recommended_action": "Use replay evidence to resolve disputes." if dispute_cases else "No disputes currently queued.",
        "disputes": enriched_cases[:limit],
        "projection_only": True,
        "read_only": True,
    }


def _ride_lookup_projection(*, organization_id: str, events: list[dict[str, Any]], rides: list[dict[str, Any]], limit: int) -> dict[str, Any]:
    dispatch_assignments = {str(item.get("ride_id")): item for item in _dispatch_assignments(organization_id, limit)}
    transactions = _transactions(organization_id, limit)
    tx_by_ride: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for transaction in transactions:
        tx_by_ride[str(transaction.get("ride_id"))].append(transaction)

    support_events_by_ride: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            payload = {}
        ride_id = str(payload.get("ride_id") or event.get("target") or payload.get("linked_ride_id") or "")
        if ride_id:
            support_events_by_ride[ride_id].append(event)

    ride_cases: list[dict[str, Any]] = []
    for ride in rides:
        ride_id = str(ride.get("ride_id"))
        ride_events = support_events_by_ride.get(ride_id, [])
        ride_events.sort(key=lambda row: _parse_timestamp(row.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc))
        status = str(ride.get("status", "")).lower()
        dispatch = dispatch_assignments.get(ride_id)
        transactions_for_ride = tx_by_ride.get(ride_id, [])
        fare_estimate = _safe_decimal(ride.get("fare_estimate"))
        final_fare = _safe_decimal(ride.get("final_fare", ride.get("fare_estimate")))
        fare_variance = max(Decimal("0.00"), final_fare - fare_estimate)
        evidence_ready = bool(dispatch) or bool(transactions_for_ride) or bool(ride_events)
        ride_cases.append(
            {
                "ride_id": ride_id,
                "status": status,
                "passenger_id": ride.get("passenger_id"),
                "driver_id": ride.get("driver_id"),
                "currency": ride.get("currency"),
                "fare_estimate": ride.get("fare_estimate"),
                "final_fare": ride.get("final_fare"),
                "fare_variance": _money_text(fare_variance),
                "dispatch_status": dispatch.get("status") if dispatch else None,
                "transaction_count": len(transactions_for_ride),
                "support_event_count": len(ride_events),
                "timeline": [
                    {
                        "event_type": event.get("event_type"),
                        "status": event.get("status"),
                        "created_at": event.get("created_at"),
                        "target": event.get("target"),
                    }
                    for event in ride_events[-6:]
                ],
                "evidence_ready": evidence_ready,
            }
        )

    ride_cases.sort(key=lambda row: (row["support_event_count"], row["evidence_ready"], row["status"]), reverse=True)
    return {
        "view": "novaride_phase10_ride_lookup",
        "ride_total": len(ride_cases),
        "evidence_ready_count": sum(1 for ride in ride_cases if ride["evidence_ready"]),
        "ride_cases": ride_cases[:limit],
        "projection_only": True,
        "read_only": True,
    }


def _escalation_projection(*, organization_id: str, events: list[dict[str, Any]], limit: int) -> dict[str, Any]:
    escalation_events = [event for event in events if str(event.get("event_type", "")).lower() in _ESCALATION_EVENT_TYPES]
    escalation_cases = _group_support_cases(escalation_events, case_key="escalation_id", type_name="escalation", status_default="open")
    level_counts = Counter(str(case.get("payload", {}).get("escalation_level") or case["latest_status"]) for case in escalation_cases)
    queue_by_level = {
        "level_1": level_counts.get("level_1", 0),
        "level_2": level_counts.get("level_2", 0),
        "level_3": level_counts.get("level_3", 0),
    }
    return {
        "view": "novaride_phase10_escalations",
        "escalation_total": len(escalation_cases),
        "escalation_level_counts": dict(level_counts),
        "queue_by_level": queue_by_level,
        "recommended_path": "Route high-severity cases to admins and replay review.",
        "escalations": escalation_cases[:limit],
        "projection_only": True,
        "read_only": True,
    }


def _replay_evidence_projection(*, organization_id: str, events: list[dict[str, Any]], rides: list[dict[str, Any]], limit: int) -> dict[str, Any]:
    audit_verified = bool(_store().verify_audit_chain(organization_id=organization_id))
    recent_rides = rides[:limit]
    evidence_coverage = 0
    replayable_rides = 0
    ride_evidence: list[dict[str, Any]] = []
    for ride in recent_rides:
        ride_id = str(ride.get("ride_id"))
        ride_events = [event for event in events if str((event.get("payload") or {}).get("ride_id") or event.get("target")) == ride_id]
        dispatch = _store().get_dispatch_assignment(organization_id=organization_id, ride_id=ride_id)
        transactions = _store().list_transactions(organization_id=organization_id, ride_id=ride_id, limit=20)
        supported = bool(ride_events) and (bool(dispatch) or bool(transactions))
        if supported:
            replayable_rides += 1
        evidence_coverage += 1 if supported else 0
        ride_evidence.append(
            {
                "ride_id": ride_id,
                "supported": supported,
                "audit_event_count": len(ride_events),
                "transaction_count": len(transactions),
                "dispatch_status": dispatch.get("status") if dispatch else None,
            }
        )

    coverage_pct = round((evidence_coverage / max(1, len(recent_rides))) * 100.0, 2)
    return {
        "view": "novaride_phase10_replay_evidence",
        "audit_chain_verified": audit_verified,
        "coverage_pct": coverage_pct,
        "replayable_rides": replayable_rides,
        "evidence_ready": audit_verified and replayable_rides > 0,
        "ride_evidence": ride_evidence,
        "projection_only": True,
        "read_only": True,
    }


def _customer_experience_projection(*, organization_id: str, tickets: dict[str, Any], refunds: dict[str, Any], disputes: dict[str, Any], replay: dict[str, Any]) -> dict[str, Any]:
    trust = _organization_trust(organization_id)
    trust_score = _safe_int(trust.get("trust_score"), 92) if trust else 92
    resolution_rate = _safe_float(tickets.get("resolution_rate"), 0.0)
    backlog = _safe_int(tickets.get("open_pressure"), 0)
    coverage = _safe_float(replay.get("coverage_pct"), 0.0)
    refund_pressure = _safe_int(refunds.get("pending_refund_count"), 0) + _safe_int(refunds.get("approved_refund_count"), 0)
    dispute_pressure = _safe_int(disputes.get("dispute_total"), 0)
    raw_score = (
        (trust_score * 0.5)
        + (resolution_rate * 50.0)
        + (coverage * 0.15)
        - (backlog * 2.0)
        - (refund_pressure * 0.75)
        - (dispute_pressure * 1.25)
    )
    experience_score = int(round(_clamp(raw_score, minimum=0.0, maximum=100.0)))
    if experience_score >= 85:
        band = "excellent"
    elif experience_score >= 70:
        band = "stable"
    else:
        band = "needs_attention"
    return {
        "view": "novaride_phase10_customer_experience",
        "experience_score": experience_score,
        "experience_band": band,
        "trust_score": trust_score,
        "ticket_resolution_rate": resolution_rate,
        "backlog_pressure": backlog,
        "refund_pressure": refund_pressure,
        "dispute_pressure": dispute_pressure,
        "replay_coverage_pct": coverage,
        "recommended_action": (
            "Keep first-line support on current workflow."
            if band != "needs_attention"
            else "Reduce backlog and prioritize replay-backed disputes."
        ),
        "projection_only": True,
        "read_only": True,
    }


def _support_contract() -> dict[str, Any]:
    return {
        "view": "novaride_phase10_support_contract",
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
            "contract": "/v1/novaride/phase10/support-contract",
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


def build_phase10_support_workspace_projection(
    *,
    organization_id: str,
    limit: int = 100,
    source: str | None = "afriride_support_workspace",
) -> dict[str, Any]:
    phase9 = build_phase9_status(organization_id=organization_id, limit=limit)
    events = _support_events(organization_id, limit)
    rides = _rides(organization_id, limit)
    transactions = _transactions(organization_id, limit)
    billing_records = _billing_records(organization_id, limit)
    support_contract = _support_contract()
    tickets = _ticket_queue_projection(organization_id=organization_id, events=events, rides=rides, limit=limit)
    refunds = _refund_projection(
        organization_id=organization_id,
        events=events,
        rides=rides,
        transactions=transactions,
        limit=limit,
    )
    disputes = _dispute_projection(
        organization_id=organization_id,
        events=events,
        rides=rides,
        transactions=transactions,
        limit=limit,
    )
    ride_lookup = _ride_lookup_projection(
        organization_id=organization_id,
        events=events,
        rides=rides,
        limit=limit,
    )
    escalations = _escalation_projection(organization_id=organization_id, events=events, limit=limit)
    replay_evidence = _replay_evidence_projection(
        organization_id=organization_id,
        events=events,
        rides=rides,
        limit=limit,
    )
    customer_experience = _customer_experience_projection(
        organization_id=organization_id,
        tickets=tickets,
        refunds=refunds,
        disputes=disputes,
        replay=replay_evidence,
    )

    support_activity_total = len(events) + len(rides) + len(transactions)
    subscription_active = bool(_store().latest_active_subscription(organization_id=organization_id))
    ready = bool(subscription_active and support_activity_total > 0 and replay_evidence["audit_chain_verified"])

    summary = {
        "ticket_total": tickets["ticket_total"],
        "refund_total": refunds["refund_total"],
        "dispute_total": disputes["dispute_total"],
        "escalation_total": escalations["escalation_total"],
        "ride_total": ride_lookup["ride_total"],
        "support_activity_total": support_activity_total,
        "ticket_queue_ready": True,
        "refund_workflow_ready": refunds["refund_authority"] == "NovaPay_backend_only",
        "dispute_resolution_ready": disputes["audit_chain_verified"],
        "ride_investigation_ready": ride_lookup["evidence_ready_count"] >= 0,
        "escalation_management_ready": True,
        "replay_evidence_ready": replay_evidence["evidence_ready"],
        "customer_experience_band": customer_experience["experience_band"],
    }

    return {
        "view": "novaride_phase10_support_workspace",
        "phase": "10",
        "platform": "NovaRide Phase 10",
        "organization_id": organization_id,
        "source": source or "afriride_support_workspace",
        "phase9": phase9,
        "contract": support_contract,
        "tickets": tickets,
        "refunds": refunds,
        "disputes": disputes,
        "ride_lookup": ride_lookup,
        "escalations": escalations,
        "replay_evidence": replay_evidence,
        "customer_experience": customer_experience,
        "summary": summary,
        "billing_records": billing_records,
        "projection_only": True,
        "read_only": True,
        "governance_linked": True,
        "creates_authority": False,
        "created_at": _now(),
        "ready": ready,
    }


def build_phase10_status(
    *,
    organization_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    projection = build_phase10_support_workspace_projection(organization_id=org_id, limit=limit)
    readiness = {
        "subscription_active": bool(_store().latest_active_subscription(organization_id=org_id)),
        "ticket_queue_ready": bool(projection["summary"]["ticket_queue_ready"]),
        "refund_workflow_ready": bool(projection["summary"]["refund_workflow_ready"]),
        "dispute_resolution_ready": bool(projection["summary"]["dispute_resolution_ready"]),
        "ride_investigation_ready": bool(projection["summary"]["ride_investigation_ready"]),
        "escalation_management_ready": bool(projection["summary"]["escalation_management_ready"]),
        "replay_evidence_ready": bool(projection["summary"]["replay_evidence_ready"]),
        "customer_experience_ready": projection["customer_experience"]["experience_band"] in {"stable", "excellent"},
        "tenant_isolation_preserved": True,
    }
    ready = all(
        readiness[key]
        for key in (
            "subscription_active",
            "ticket_queue_ready",
            "refund_workflow_ready",
            "dispute_resolution_ready",
            "ride_investigation_ready",
            "escalation_management_ready",
            "replay_evidence_ready",
            "tenant_isolation_preserved",
        )
    )
    return {
        "view": "novaride_phase10_status",
        "phase": "10",
        "platform": "NovaRide Phase 10",
        "organization_id": org_id,
        "phase9": projection["phase9"],
        "support_workspace": projection,
        "readiness": readiness,
        "ready": ready,
        "projection_only": True,
        "read_only": True,
        "governance_linked": True,
        "creates_authority": False,
    }


def build_phase10_support_contract_projection() -> dict[str, Any]:
    return _support_contract()


def build_phase10_tickets_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    events = _support_events(organization_id, limit)
    rides = _rides(organization_id, limit)
    return _ticket_queue_projection(organization_id=organization_id, events=events, rides=rides, limit=limit)


def build_phase10_refunds_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    events = _support_events(organization_id, limit)
    rides = _rides(organization_id, limit)
    transactions = _transactions(organization_id, limit)
    return _refund_projection(organization_id=organization_id, events=events, rides=rides, transactions=transactions, limit=limit)


def build_phase10_disputes_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    events = _support_events(organization_id, limit)
    rides = _rides(organization_id, limit)
    transactions = _transactions(organization_id, limit)
    return _dispute_projection(organization_id=organization_id, events=events, rides=rides, transactions=transactions, limit=limit)


def build_phase10_ride_lookup_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    events = _support_events(organization_id, limit)
    rides = _rides(organization_id, limit)
    return _ride_lookup_projection(organization_id=organization_id, events=events, rides=rides, limit=limit)


def build_phase10_escalations_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    events = _support_events(organization_id, limit)
    return _escalation_projection(organization_id=organization_id, events=events, limit=limit)


def build_phase10_replay_evidence_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    events = _support_events(organization_id, limit)
    rides = _rides(organization_id, limit)
    return _replay_evidence_projection(organization_id=organization_id, events=events, rides=rides, limit=limit)


def build_phase10_customer_experience_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    workspace = build_phase10_support_workspace_projection(organization_id=organization_id, limit=limit)
    return workspace["customer_experience"]


__all__ = [
    "build_phase10_customer_experience_projection",
    "build_phase10_disputes_projection",
    "build_phase10_escalations_projection",
    "build_phase10_replay_evidence_projection",
    "build_phase10_refunds_projection",
    "build_phase10_ride_lookup_projection",
    "build_phase10_status",
    "build_phase10_support_contract_projection",
    "build_phase10_support_workspace_projection",
    "build_phase10_tickets_projection",
]
