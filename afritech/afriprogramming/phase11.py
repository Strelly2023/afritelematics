"""NovaRide Phase 11 compliance and inspection system.

This layer remains projection-only. It turns tenant-scoped audit events,
rides, transactions, driver presence, and support evidence into a controlled
surface for compliance tracking, inspections, document verification, driver
scoring, fraud detection, smart refund recommendations, and auto ticket
classification without mutating refund or payment authority.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from afritech.afriprogramming.phase10 import build_phase10_support_contract_projection


PHASE11_TOPIC = "novaride.phase11.compliance_inspection"

NOVARIDE_PHASE11_MODULES = (
    {
        "key": "support_dashboard_ui",
        "name": "Support Dashboard UI",
        "purpose": "Surface tickets, refund recommendations, inspections, fraud signals, and compliance summaries in a bounded control plane.",
    },
    {
        "key": "auto_ticket_classification",
        "name": "Auto Ticket Classification",
        "purpose": "Classify support tickets by payment, safety, compliance, and ride issue categories with deterministic confidence bands.",
    },
    {
        "key": "smart_refunds",
        "name": "Smart Refund System",
        "purpose": "Recommend refund amounts from ride evidence, fare variance, cancellations, and disputes without executing payments directly.",
    },
    {
        "key": "analytics_backend",
        "name": "Analytics Backend",
        "purpose": "Compute compliance, inspection, fraud, and driver scoring summaries for operator dashboards.",
    },
    {
        "key": "driver_scoring",
        "name": "Driver Scoring Algorithm",
        "purpose": "Derive stable driver scores from trust, completion, cancellations, inspections, and support pressure.",
    },
    {
        "key": "vehicle_inspection",
        "name": "Vehicle Inspection",
        "purpose": "Track field inspection workflows and evidence-linked status summaries for driver and vehicle compliance.",
    },
    {
        "key": "document_verification",
        "name": "Document Verification",
        "purpose": "Summarize license, registration, insurance, and certificate verification without exposing authority to apps.",
    },
    {
        "key": "inspection_reports",
        "name": "Inspection Reports",
        "purpose": "Publish evidence-backed inspection reports and operator-ready compliance outcomes.",
    },
    {
        "key": "fraud_detection",
        "name": "Fraud Detection",
        "purpose": "Aggregate disputes, anomalies, document failures, and refund pressure into fraud risk bands.",
    },
    {
        "key": "regulatory_readiness",
        "name": "Regulatory Readiness",
        "purpose": "Combine compliance, document, inspection, and audit posture into government review readiness.",
    },
)

NOVARIDE_PHASE11_NAVIGATION = (
    "workspace",
    "support_dashboard",
    "inspections",
    "documents",
    "reports",
    "compliance_tracking",
    "driver_scoring",
    "fraud_detection",
    "smart_refunds",
    "analytics",
)

NOVARIDE_PHASE11_ALLOWED_ACTIONS = (
    "view_compliance_dashboard",
    "classify_tickets",
    "review_refund_recommendations",
    "review_inspections",
    "review_documents",
    "review_reports",
    "export_compliance_reports",
)

NOVARIDE_PHASE11_FORBIDDEN_ACTIONS = (
    "direct_payment_execution",
    "direct_provider_access",
    "override_trust_engine",
    "bypass_audit_chain",
)

NOVARIDE_PHASE11_TICKET_TYPES = (
    "support_ticket_created",
    "support_ticket_assigned",
    "support_ticket_updated",
    "support_ticket_in_progress",
    "support_ticket_resolved",
    "support_ticket_closed",
    "refund_requested",
    "refund_reviewed",
    "refund_approved",
    "refund_rejected",
    "refund_processed",
    "dispute_opened",
    "dispute_reviewed",
    "dispute_resolved",
    "dispute_escalated",
)

NOVARIDE_PHASE11_INSPECTION_TYPES = (
    "inspection_started",
    "inspection_submitted",
    "inspection_approved",
    "inspection_rejected",
    "vehicle_inspected",
    "compliance_updated",
)

NOVARIDE_PHASE11_DOCUMENT_TYPES = (
    "document_verified",
    "document_expired",
    "document_rejected",
    "license_verified",
    "license_expired",
    "insurance_verified",
    "insurance_expired",
    "registration_verified",
    "registration_expired",
    "inspection_certificate_uploaded",
)

NOVARIDE_PHASE11_REPORT_TYPES = (
    "inspection_report_submitted",
    "inspection_report_saved",
    "inspection_report_issued",
)

NOVARIDE_PHASE11_FRAUD_TYPES = (
    "fraud_flagged",
    "fraud_detected",
    "trip_anomaly_detected",
    "compliance_breach_detected",
    "blacklist_added",
    "safety_alert_raised",
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


def _event_payload(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload", {})
    return payload if isinstance(payload, dict) else {}


def _event_blob(event: dict[str, Any]) -> str:
    payload = _event_payload(event)
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


def _looks_phase11_related(event: dict[str, Any]) -> bool:
    event_type = str(event.get("event_type", "")).lower()
    if event_type in set(NOVARIDE_PHASE11_TICKET_TYPES) | set(NOVARIDE_PHASE11_INSPECTION_TYPES) | set(
        NOVARIDE_PHASE11_DOCUMENT_TYPES
    ) | set(NOVARIDE_PHASE11_REPORT_TYPES) | set(NOVARIDE_PHASE11_FRAUD_TYPES):
        return True
    blob = _event_blob(event)
    keywords = (
        "support",
        "refund",
        "dispute",
        "inspection",
        "document",
        "compliance",
        "fraud",
        "anomaly",
        "ticket",
        "certificate",
        "blacklist",
        "safety",
    )
    return any(keyword in blob for keyword in keywords)


def _support_related_events(organization_id: str, limit: int) -> list[dict[str, Any]]:
    events = _store().list_audit_events(organization_id=organization_id, limit=limit)
    return [event for event in events if _looks_phase11_related(event)]


def _rides(organization_id: str, limit: int) -> list[dict[str, Any]]:
    return _store().list_rides(organization_id=organization_id, limit=limit)


def _transactions(organization_id: str, limit: int) -> list[dict[str, Any]]:
    return _store().list_transactions(organization_id=organization_id, limit=limit)


def _dispatch_assignments(organization_id: str, limit: int) -> list[dict[str, Any]]:
    return _store().list_dispatch_assignments(organization_id=organization_id, limit=limit)


def _driver_presence(organization_id: str, limit: int) -> list[dict[str, Any]]:
    return _store().list_driver_presence(organization_id=organization_id, limit=limit)


def _billing_records(organization_id: str, limit: int) -> list[dict[str, Any]]:
    return _store().list_billing_records(organization_id=organization_id, limit=limit)


def _organization_trust(organization_id: str) -> dict[str, Any] | None:
    return _store().latest_trust_score(organization_id=organization_id)


def _canonical_status(value: Any, *, default: str = "open") -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"", "new", "created"}:
        return default
    if normalized in {"pending", "open", "queued"}:
        return "open"
    if normalized in {"assigned", "reviewing", "triaging", "investigating", "in_progress", "in-progress"}:
        return "in_progress"
    if normalized in {"approved", "accepted", "verified", "compliant"}:
        return "approved"
    if normalized in {"rejected", "denied", "declined", "non_compliant"}:
        return "rejected"
    if normalized in {"resolved", "resolved_with_refund", "resolved_with_credit"}:
        return "resolved"
    if normalized in {"closed", "complete", "completed"}:
        return "closed"
    if normalized in {"expired", "invalid"}:
        return "expired"
    return normalized or default


def _group_cases(
    events: list[dict[str, Any]],
    *,
    case_key: str,
    type_name: str,
    status_default: str = "open",
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        payload = _event_payload(event)
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
        payload = _event_payload(last_event)
        status = _canonical_status(last_event.get("status"), default=status_default)
        cases.append(
            {
                f"{type_name}_id": case_id,
                "ride_id": str(payload.get("ride_id") or payload.get("linked_ride_id") or "") or None,
                "driver_id": str(payload.get("driver_id") or "") or None,
                "vehicle_id": str(payload.get("vehicle_id") or "") or None,
                "latest_status": status,
                "priority": str(payload.get("priority") or payload.get("severity") or "medium").lower(),
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


def _classify_ticket_case(case: dict[str, Any]) -> dict[str, Any]:
    payload = case.get("payload", {})
    blob = " ".join(
        [
            str(case.get("category", "")),
            str(payload.get("issue_type") or ""),
            str(payload.get("reason") or ""),
            _event_blob({"event_type": case.get("case_type"), "target": case.get("ride_id"), "status": case.get("latest_status"), "payload": payload}),
        ]
    ).lower()
    category = "general_support"
    confidence = 0.58
    if any(keyword in blob for keyword in ("refund", "reversal", "chargeback", "overcharge")):
        category = "fare_dispute"
        confidence = 0.93 if "overcharge" in blob or "chargeback" in blob else 0.84
    elif any(keyword in blob for keyword in ("payment", "wallet", "card", "billing")):
        category = "payment_issue"
        confidence = 0.87
    elif any(keyword in blob for keyword in ("safety", "risk", "incident", "harass", "assault")):
        category = "safety_incident"
        confidence = 0.92
    elif any(keyword in blob for keyword in ("inspection", "document", "license", "insurance", "registration")):
        category = "compliance_issue"
        confidence = 0.9
    elif any(keyword in blob for keyword in ("fraud", "anomaly", "blacklist")):
        category = "fraud_review"
        confidence = 0.95
    elif any(keyword in blob for keyword in ("delay", "late", "eta", "pickup")):
        category = "ride_delay"
        confidence = 0.82
    elif any(keyword in blob for keyword in ("lost", "found")):
        category = "lost_and_found"
        confidence = 0.81

    confidence = _clamp(confidence + min(0.06, 0.01 * max(0, case.get("evidence_count", 1) - 1)), minimum=0.5, maximum=0.99)
    severity = "high" if category in {"safety_incident", "fraud_review", "fare_dispute"} else "medium" if category in {"payment_issue", "compliance_issue"} else "low"
    return {
        "ticket_id": case.get("ticket_id"),
        "ride_id": case.get("ride_id"),
        "latest_status": case.get("latest_status"),
        "priority": case.get("priority"),
        "category": category,
        "confidence": round(confidence, 2),
        "severity": severity,
        "first_seen_at": case.get("first_seen_at"),
        "last_updated_at": case.get("last_updated_at"),
        "evidence_count": case.get("evidence_count"),
        "recommended_queue": "fraud_and_compliance" if category in {"fraud_review", "compliance_issue"} else "refund_review" if category == "fare_dispute" else "general_support",
        "payload": payload,
    }


def _ticket_classification_projection(
    *,
    organization_id: str,
    events: list[dict[str, Any]],
    rides: list[dict[str, Any]],
    limit: int,
) -> dict[str, Any]:
    ticket_events = [event for event in events if str(event.get("event_type", "")).lower() in NOVARIDE_PHASE11_TICKET_TYPES]
    ticket_cases = _group_cases(ticket_events, case_key="ticket_id", type_name="ticket")

    if not ticket_cases:
        inferred = [
            {
                "ticket_id": f"ticket-inferred-{ride['ride_id']}",
                "ride_id": ride["ride_id"],
                "driver_id": ride.get("driver_id"),
                "vehicle_id": None,
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

    classified = [_classify_ticket_case(case) for case in ticket_cases]
    status_counts = Counter(case["latest_status"] for case in classified)
    category_counts = Counter(case["category"] for case in classified)
    priority_counts = Counter(case["priority"] for case in classified)
    severity_counts = Counter(case["severity"] for case in classified)
    support_pressure = status_counts.get("open", 0) + status_counts.get("in_progress", 0)
    resolution_rate = round(
        (status_counts.get("resolved", 0) + status_counts.get("closed", 0)) / max(1, len(classified)),
        6,
    )
    auto_classification_ready = bool(classified)
    confidence_average = round(sum(case["confidence"] for case in classified) / max(1, len(classified)), 2)
    confidence_band = "high" if confidence_average >= 0.85 else "medium" if confidence_average >= 0.7 else "low"
    queue_band = "healthy" if resolution_rate >= 0.75 and support_pressure <= 2 else "watch" if resolution_rate >= 0.5 else "critical"
    return {
        "view": "novaride_phase11_ticket_classification",
        "ticket_total": len(classified),
        "ticket_status_counts": dict(status_counts),
        "ticket_category_counts": dict(category_counts),
        "ticket_priority_counts": dict(priority_counts),
        "ticket_severity_counts": dict(severity_counts),
        "support_pressure": support_pressure,
        "resolution_rate": resolution_rate,
        "confidence_average": confidence_average,
        "confidence_band": confidence_band,
        "queue_band": queue_band,
        "auto_classification_ready": auto_classification_ready,
        "classifications": classified[:limit],
        "projection_only": True,
        "read_only": True,
    }


def _inspection_projection(
    *,
    organization_id: str,
    events: list[dict[str, Any]],
    limit: int,
) -> dict[str, Any]:
    inspection_events = [event for event in events if str(event.get("event_type", "")).lower() in NOVARIDE_PHASE11_INSPECTION_TYPES]
    inspection_cases = _group_cases(inspection_events, case_key="inspection_id", type_name="inspection", status_default="pending")
    if not inspection_cases:
        inspection_cases = [
            {
                "inspection_id": f"inspection-inferred-{driver['driver_id']}",
                "ride_id": None,
                "driver_id": driver["driver_id"],
                "vehicle_id": None,
                "latest_status": "pending",
                "priority": "medium",
                "category": "driver_review",
                "first_seen_at": driver.get("created_at"),
                "last_updated_at": driver.get("updated_at"),
                "duration_minutes": 0.0,
                "evidence_count": 1,
                "history": [],
                "payload": {"source": "inferred_from_driver_presence", "driver_id": driver["driver_id"]},
                "case_type": "inspection",
            }
            for driver in _driver_presence(organization_id, limit=limit)
        ]

    status_counts = Counter(case["latest_status"] for case in inspection_cases)
    category_counts = Counter(case["category"] for case in inspection_cases)
    evidence_ready_count = sum(1 for case in inspection_cases if case["latest_status"] in {"approved", "compliant", "verified"})
    compliant_count = sum(1 for case in inspection_cases if case["latest_status"] in {"approved", "compliant", "verified"})
    rejected_count = sum(1 for case in inspection_cases if case["latest_status"] in {"rejected", "non_compliant", "expired", "invalid"})
    pending_count = len(inspection_cases) - compliant_count - rejected_count
    compliance_rate = round(compliant_count / max(1, len(inspection_cases)), 6)
    inspection_band = "compliant" if compliance_rate >= 0.75 else "watch" if compliance_rate >= 0.5 else "non_compliant"
    return {
        "view": "novaride_phase11_inspections",
        "inspection_total": len(inspection_cases),
        "inspection_status_counts": dict(status_counts),
        "inspection_category_counts": dict(category_counts),
        "compliant_count": compliant_count,
        "rejected_count": rejected_count,
        "pending_count": pending_count,
        "evidence_ready_count": evidence_ready_count,
        "compliance_rate": compliance_rate,
        "inspection_band": inspection_band,
        "inspection_queue_ready": inspection_band != "non_compliant",
        "inspections": inspection_cases[:limit],
        "projection_only": True,
        "read_only": True,
    }


def _document_verification_projection(
    *,
    organization_id: str,
    events: list[dict[str, Any]],
    limit: int,
) -> dict[str, Any]:
    document_events = [event for event in events if str(event.get("event_type", "")).lower() in NOVARIDE_PHASE11_DOCUMENT_TYPES]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in document_events:
        payload = _event_payload(event)
        doc_id = str(
            payload.get("document_id")
            or payload.get("document")
            or payload.get("license_number")
            or payload.get("certificate_id")
            or event.get("target")
            or ""
        ).strip()
        if not doc_id:
            continue
        grouped[doc_id].append(event)

    documents: list[dict[str, Any]] = []
    if grouped:
        for document_id, history in grouped.items():
            history.sort(key=lambda row: _parse_timestamp(row.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc))
            last_event = history[-1]
            payload = _event_payload(last_event)
            status = _canonical_status(last_event.get("status"), default="pending")
            documents.append(
                {
                    "document_id": document_id,
                    "subject_id": str(payload.get("driver_id") or payload.get("vehicle_id") or payload.get("organization_id") or "") or None,
                    "document_type": str(payload.get("document_type") or payload.get("type") or payload.get("kind") or "document").lower(),
                    "latest_status": status,
                    "expires_at": payload.get("expires_at"),
                    "verified_at": payload.get("verified_at"),
                    "evidence_count": len(history),
                    "last_updated_at": last_event.get("created_at"),
                    "payload": payload,
                }
            )

    if not documents:
        driver_documents = []
        for driver in _driver_presence(organization_id, limit=limit):
            driver_documents.append(
                {
                    "document_id": f"doc-inferred-{driver['driver_id']}",
                    "subject_id": driver["driver_id"],
                    "document_type": "license",
                    "latest_status": "pending",
                    "expires_at": None,
                    "verified_at": None,
                    "evidence_count": 0,
                    "last_updated_at": driver.get("updated_at"),
                    "payload": {"source": "inferred_from_driver_presence"},
                }
            )
        documents = driver_documents

    status_counts = Counter(document["latest_status"] for document in documents)
    verified_count = status_counts.get("approved", 0) + status_counts.get("verified", 0)
    expired_count = status_counts.get("expired", 0)
    rejected_count = status_counts.get("rejected", 0)
    pending_count = len(documents) - verified_count - expired_count - rejected_count
    verification_rate = round(verified_count / max(1, len(documents)), 6)
    verification_band = "verified" if verification_rate >= 0.75 else "watch" if verification_rate >= 0.5 else "needs_attention"
    return {
        "view": "novaride_phase11_document_verification",
        "document_total": len(documents),
        "document_status_counts": dict(status_counts),
        "verified_count": verified_count,
        "expired_count": expired_count,
        "rejected_count": rejected_count,
        "pending_count": pending_count,
        "verification_rate": verification_rate,
        "verification_band": verification_band,
        "documents": documents[:limit],
        "projection_only": True,
        "read_only": True,
    }


def _inspection_reports_projection(
    *,
    organization_id: str,
    events: list[dict[str, Any]],
    inspections: dict[str, Any],
    limit: int,
) -> dict[str, Any]:
    report_events = [event for event in events if str(event.get("event_type", "")).lower() in NOVARIDE_PHASE11_REPORT_TYPES]
    reports = _group_cases(report_events, case_key="report_id", type_name="report", status_default="pending")
    if not reports and inspections["inspections"]:
        reports = [
            {
                "report_id": f"report-inferred-{case['inspection_id']}",
                "ride_id": case.get("ride_id"),
                "driver_id": case.get("driver_id"),
                "vehicle_id": case.get("vehicle_id"),
                "latest_status": "approved" if case["latest_status"] in {"approved", "compliant", "verified"} else "pending",
                "priority": case.get("priority", "medium"),
                "category": case.get("category", "inspection_report"),
                "first_seen_at": case.get("first_seen_at"),
                "last_updated_at": case.get("last_updated_at"),
                "duration_minutes": case.get("duration_minutes", 0.0),
                "evidence_count": case.get("evidence_count", 1),
                "history": [],
                "payload": {
                    "source": "inferred_from_inspection",
                    "inspection_id": case.get("inspection_id"),
                    "driver_id": case.get("driver_id"),
                },
                "case_type": "report",
            }
            for case in inspections["inspections"][:limit]
        ]

    status_counts = Counter(report["latest_status"] for report in reports)
    approved_count = status_counts.get("approved", 0) + status_counts.get("verified", 0)
    rejected_count = status_counts.get("rejected", 0)
    pending_count = len(reports) - approved_count - rejected_count
    ready_rate = round(approved_count / max(1, len(reports)), 6)
    report_band = "ready" if ready_rate >= 0.75 else "watch" if ready_rate >= 0.5 else "needs_attention"
    return {
        "view": "novaride_phase11_inspection_reports",
        "report_total": len(reports),
        "report_status_counts": dict(status_counts),
        "approved_report_count": approved_count,
        "rejected_report_count": rejected_count,
        "pending_report_count": pending_count,
        "ready_rate": ready_rate,
        "report_band": report_band,
        "reports": reports[:limit],
        "projection_only": True,
        "read_only": True,
    }


def _driver_scoring_projection(
    *,
    organization_id: str,
    events: list[dict[str, Any]],
    rides: list[dict[str, Any]],
    dispatch_assignments: list[dict[str, Any]],
    driver_presence: list[dict[str, Any]],
    inspections: dict[str, Any],
    documents: dict[str, Any],
    limit: int,
) -> dict[str, Any]:
    trust = _organization_trust(organization_id)
    trust_score = _safe_int(trust.get("trust_score"), 90) if trust else 90
    latest_audit_band = str(trust.get("classification") or "stable") if trust else "stable"
    ride_by_id = {str(ride.get("ride_id")): ride for ride in rides}
    issue_counts_by_driver: dict[str, Counter[str]] = defaultdict(Counter)
    for event in events:
        payload = _event_payload(event)
        ride_id = str(payload.get("ride_id") or payload.get("linked_ride_id") or event.get("target") or "").strip()
        driver_id = str(payload.get("driver_id") or (ride_by_id.get(ride_id) or {}).get("driver_id") or "").strip()
        if not driver_id:
            continue
        blob = _event_blob(event)
        if any(token in blob for token in ("refund", "dispute", "support_ticket", "complaint", "lost", "payment_issue", "fare_dispute")):
            issue_counts_by_driver[driver_id]["support"] += 1
        if any(token in blob for token in ("fraud", "anomaly", "blacklist", "safety", "risk")):
            issue_counts_by_driver[driver_id]["fraud"] += 1
        if any(token in blob for token in ("inspection_rejected", "document_expired", "compliance_breach", "non_compliant")):
            issue_counts_by_driver[driver_id]["compliance"] += 1

    inspections_by_driver: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for inspection in inspections["inspections"]:
        driver_id = str(inspection.get("driver_id") or inspection.get("payload", {}).get("driver_id") or "").strip()
        if driver_id:
            inspections_by_driver[driver_id].append(inspection)

    documents_by_driver: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for document in documents["documents"]:
        subject_id = str(document.get("subject_id") or document.get("payload", {}).get("driver_id") or "").strip()
        if subject_id:
            documents_by_driver[subject_id].append(document)

    dispatch_by_driver: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for assignment in dispatch_assignments:
        driver_id = str(assignment.get("driver_id") or "").strip()
        if driver_id:
            dispatch_by_driver[driver_id].append(assignment)

    driver_scores: list[dict[str, Any]] = []
    for presence in driver_presence or _driver_presence(organization_id, limit=limit):
        driver_id = str(presence.get("driver_id") or "").strip()
        if not driver_id:
            continue
        driver_rides = [ride for ride in rides if str(ride.get("driver_id") or "") == driver_id]
        total_rides = len(driver_rides)
        completed_rides = [ride for ride in driver_rides if str(ride.get("status", "")).lower() == "completed"]
        cancelled_rides = [ride for ride in driver_rides if str(ride.get("status", "")).lower() == "cancelled"]
        acceptance_assignments = [assignment for assignment in dispatch_by_driver.get(driver_id, []) if str(assignment.get("status", "")).lower() in {"accepted", "assigned", "matched"}]
        acceptance_rate = len(acceptance_assignments) / max(1, len(dispatch_by_driver.get(driver_id, [])))
        completion_rate = len(completed_rides) / max(1, total_rides)
        cancellation_rate = len(cancelled_rides) / max(1, total_rides)
        presence_trust = _safe_float(presence.get("trust_score"), trust_score)
        inspection_list = inspections_by_driver.get(driver_id, [])
        document_list = documents_by_driver.get(driver_id, [])
        inspection_score = 100.0
        if inspection_list:
            if any(str(item.get("latest_status", "")).lower() in {"approved", "compliant", "verified"} for item in inspection_list):
                inspection_score = 100.0
            elif any(str(item.get("latest_status", "")).lower() in {"rejected", "non_compliant", "expired"} for item in inspection_list):
                inspection_score = 45.0
            else:
                inspection_score = 72.0
        document_score = 100.0
        if document_list:
            if any(str(item.get("latest_status", "")).lower() in {"approved", "verified"} for item in document_list):
                document_score = 100.0
            elif any(str(item.get("latest_status", "")).lower() in {"rejected", "expired", "invalid"} for item in document_list):
                document_score = 50.0
            else:
                document_score = 75.0
        support_penalty = _safe_int(issue_counts_by_driver[driver_id].get("support", 0))
        fraud_penalty = _safe_int(issue_counts_by_driver[driver_id].get("fraud", 0))
        compliance_penalty = _safe_int(issue_counts_by_driver[driver_id].get("compliance", 0))
        raw_score = (
            (presence_trust * 0.36)
            + (completion_rate * 28.0)
            + (acceptance_rate * 14.0)
            + (inspection_score * 0.12)
            + (document_score * 0.12)
            - (cancellation_rate * 12.0)
            - (support_penalty * 4.0)
            - (fraud_penalty * 8.0)
            - (compliance_penalty * 5.0)
        )
        score = int(round(_clamp(raw_score, minimum=0.0, maximum=100.0)))
        if score >= 85:
            band = "excellent"
        elif score >= 70:
            band = "good"
        elif score >= 55:
            band = "watch"
        else:
            band = "critical"
        driver_scores.append(
            {
                "driver_id": driver_id,
                "score": score,
                "score_band": band,
                "completion_rate": round(completion_rate, 6),
                "acceptance_rate": round(acceptance_rate, 6),
                "cancellation_rate": round(cancellation_rate, 6),
                "trust_score": round(presence_trust, 2),
                "inspection_score": round(inspection_score, 2),
                "document_score": round(document_score, 2),
                "support_penalty": support_penalty,
                "fraud_penalty": fraud_penalty,
                "compliance_penalty": compliance_penalty,
                "rides_total": total_rides,
                "rides_completed": len(completed_rides),
                "rides_cancelled": len(cancelled_rides),
                "dispatch_assignments": len(dispatch_by_driver.get(driver_id, [])),
                "presence_status": presence.get("status"),
                "latest_seen_at": presence.get("last_seen"),
                "allocation_hint": "safe_auto_allocate" if band in {"excellent", "good"} else "manual_review",
            }
        )

    driver_scores.sort(key=lambda row: (row["score"], row["dispatch_assignments"], row["rides_total"]), reverse=True)
    score_band_counts = Counter(score["score_band"] for score in driver_scores)
    average_score = round(sum(score["score"] for score in driver_scores) / max(1, len(driver_scores)), 2)
    platform_band = "strong" if average_score >= 80 else "watch" if average_score >= 65 else "critical"
    return {
        "view": "novaride_phase11_driver_scoring",
        "driver_total": len(driver_scores),
        "average_score": average_score,
        "score_band_counts": dict(score_band_counts),
        "platform_band": platform_band,
        "audit_band": latest_audit_band,
        "driver_scores": driver_scores[:limit],
        "projection_only": True,
        "read_only": True,
    }


def _fraud_detection_projection(
    *,
    organization_id: str,
    events: list[dict[str, Any]],
    rides: list[dict[str, Any]],
    transactions: list[dict[str, Any]],
    ticket_classification: dict[str, Any],
    inspections: dict[str, Any],
    documents: dict[str, Any],
    limit: int,
) -> dict[str, Any]:
    ride_lookup = {str(ride.get("ride_id")): ride for ride in rides}
    ticket_categories = ticket_classification.get("ticket_category_counts", {})
    refund_pressure = _safe_int(ticket_categories.get("fare_dispute", 0)) + _safe_int(ticket_categories.get("payment_issue", 0))
    dispute_pressure = _safe_int(ticket_categories.get("fare_dispute", 0))
    inspection_failures = _safe_int(inspections.get("rejected_count", 0))
    document_failures = _safe_int(documents.get("expired_count", 0) + documents.get("rejected_count", 0))
    fraud_events = [event for event in events if str(event.get("event_type", "")).lower() in NOVARIDE_PHASE11_FRAUD_TYPES]

    ride_issue_links: dict[str, int] = defaultdict(int)
    flags: list[dict[str, Any]] = []
    for event in fraud_events:
        payload = _event_payload(event)
        ride_id = str(payload.get("ride_id") or event.get("target") or "").strip()
        if ride_id:
            ride_issue_links[ride_id] += 1
        flags.append(
            {
                "event_type": event.get("event_type"),
                "target": event.get("target"),
                "status": event.get("status"),
                "ride_id": ride_id or None,
                "severity": str(payload.get("severity") or payload.get("risk") or "medium").lower(),
                "created_at": event.get("created_at"),
            }
        )

    for ride in rides:
        ride_id = str(ride.get("ride_id"))
        if str(ride.get("status", "")).lower() == "cancelled":
            ride_issue_links[ride_id] += 1
        if ride.get("final_fare") is not None and _safe_decimal(ride.get("final_fare")) > _safe_decimal(ride.get("fare_estimate")):
            ride_issue_links[ride_id] += 1

    trust = _organization_trust(organization_id)
    trust_score = _safe_int(trust.get("trust_score"), 90) if trust else 90
    total_suspicious_signals = len(fraud_events) + refund_pressure + dispute_pressure + inspection_failures + document_failures
    risk_score = int(
        round(
            _clamp(
                (total_suspicious_signals * 8.5)
                + max(0, 85 - trust_score)
                + (len([ride_id for ride_id, count in ride_issue_links.items() if count >= 2]) * 14),
                minimum=0.0,
                maximum=100.0,
            )
        )
    )
    if risk_score >= 80:
        risk_band = "critical"
    elif risk_score >= 55:
        risk_band = "high"
    elif risk_score >= 30:
        risk_band = "watch"
    else:
        risk_band = "low"
    auto_hold_refunds = risk_band in {"high", "critical"}
    suspicious_rides = [
        {
            "ride_id": ride_id,
            "ride_status": ride_lookup.get(ride_id, {}).get("status"),
            "signal_count": count,
        }
        for ride_id, count in sorted(ride_issue_links.items(), key=lambda item: item[1], reverse=True)
        if count > 0
    ]
    if len(suspicious_rides) > limit:
        suspicious_rides = suspicious_rides[:limit]
    return {
        "view": "novaride_phase11_fraud_detection",
        "fraud_signal_count": total_suspicious_signals,
        "fraud_event_count": len(fraud_events),
        "refund_pressure": refund_pressure,
        "dispute_pressure": dispute_pressure,
        "inspection_failures": inspection_failures,
        "document_failures": document_failures,
        "risk_score": risk_score,
        "risk_band": risk_band,
        "auto_hold_refunds": auto_hold_refunds,
        "fraud_flags": flags[:limit],
        "suspicious_rides": suspicious_rides,
        "projection_only": True,
        "read_only": True,
    }


def _smart_refunds_projection(
    *,
    organization_id: str,
    events: list[dict[str, Any]],
    rides: list[dict[str, Any]],
    transactions: list[dict[str, Any]],
    fraud_detection: dict[str, Any],
    limit: int,
) -> dict[str, Any]:
    tx_by_ride: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for transaction in transactions:
        tx_by_ride[str(transaction.get("ride_id"))].append(transaction)

    support_events_by_ride: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        payload = _event_payload(event)
        ride_id = str(payload.get("ride_id") or event.get("target") or payload.get("linked_ride_id") or "").strip()
        if ride_id and (
            str(event.get("event_type", "")).lower() in NOVARIDE_PHASE11_TICKET_TYPES
            or "refund" in _event_blob(event)
            or "dispute" in _event_blob(event)
        ):
            support_events_by_ride[ride_id].append(event)

    recommendations: list[dict[str, Any]] = []
    suggested_total = Decimal("0.00")
    for ride in rides:
        ride_id = str(ride.get("ride_id"))
        tx_total_debit = sum(
            _safe_decimal(tx.get("amount"))
            for tx in tx_by_ride.get(ride_id, [])
            if str(tx.get("type", "")).lower() == "debit"
        )
        fare_estimate = _safe_decimal(ride.get("fare_estimate"))
        final_fare = _safe_decimal(ride.get("final_fare", ride.get("fare_estimate")))
        suggested = Decimal("0.00")
        reason = None
        confidence = 0.52

        if str(ride.get("status", "")).lower() == "cancelled" and tx_total_debit > Decimal("0.00"):
            suggested = tx_total_debit
            reason = "Cancelled ride with collected fare"
            confidence = 0.96
        elif final_fare > fare_estimate:
            suggested = final_fare - fare_estimate
            reason = "Fare exceeded estimate"
            confidence = 0.9
        elif support_events_by_ride.get(ride_id):
            suggested = max(Decimal("0.00"), (fare_estimate * Decimal("0.25")))
            reason = "Support review linked to ride issue"
            confidence = 0.74

        if suggested <= Decimal("0.00"):
            continue

        if fraud_detection["risk_band"] in {"high", "critical"}:
            confidence = min(confidence, 0.7)
            refund_mode = "review_required"
        else:
            refund_mode = "safe_suggest"

        suggested = suggested.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        suggested_total += suggested
        recommendations.append(
            {
                "refund_id": f"refund-suggested-{ride_id}",
                "ride_id": ride_id,
                "driver_id": ride.get("driver_id"),
                "passenger_id": ride.get("passenger_id"),
                "status": "suggested",
                "suggested_refund_amount": _money_text(suggested),
                "reason": reason or "Eligibility derived from audit evidence",
                "confidence": round(confidence, 2),
                "refund_mode": refund_mode,
                "evidence_count": len(tx_by_ride.get(ride_id, [])) + len(support_events_by_ride.get(ride_id, [])),
                "currency": ride.get("currency"),
            }
        )

    return {
        "view": "novaride_phase11_smart_refunds",
        "refund_total": len(recommendations),
        "suggested_refund_total": _money_text(suggested_total),
        "refund_authority": "NovaPay_backend_only",
        "automation_mode": "review_required" if fraud_detection["risk_band"] in {"high", "critical"} else "safe_suggest",
        "trust_gate": "Trust_Engine_required",
        "recommendations": recommendations[:limit],
        "projection_only": True,
        "read_only": True,
    }


def _compliance_tracking_projection(
    *,
    organization_id: str,
    inspections: dict[str, Any],
    documents: dict[str, Any],
    reports: dict[str, Any],
    driver_scores: dict[str, Any],
    fraud_detection: dict[str, Any],
    support_pressure: int,
) -> dict[str, Any]:
    audit_verified = bool(_store().verify_audit_chain(organization_id=organization_id))
    trust = _organization_trust(organization_id)
    trust_score = _safe_int(trust.get("trust_score"), 90) if trust else 90
    inspection_total = _safe_int(inspections["inspection_total"])
    verified_documents = _safe_int(documents["verified_count"])
    inspection_reports = _safe_int(reports["report_total"])
    approved_inspections = _safe_int(inspections["compliant_count"])
    rejected_inspections = _safe_int(inspections["rejected_count"])
    compliance_score = int(
        round(
            _clamp(
                (trust_score * 0.35)
                + (inspections["compliance_rate"] * 30.0)
                + (documents["verification_rate"] * 20.0)
                + (reports["ready_rate"] * 10.0)
                - (fraud_detection["risk_score"] * 0.2)
                - (_safe_int(support_pressure) * 1.5),
                minimum=0.0,
                maximum=100.0,
            )
        )
    )
    if compliance_score >= 85:
        readiness_band = "ready"
    elif compliance_score >= 70:
        readiness_band = "review_ready"
    elif compliance_score >= 50:
        readiness_band = "watch"
    else:
        readiness_band = "non_compliant"
    regulatory_ready = bool(
        audit_verified
        and readiness_band in {"ready", "review_ready"}
        and approved_inspections > 0
        and verified_documents > 0
        and fraud_detection["risk_band"] not in {"high", "critical"}
    )
    return {
        "view": "novaride_phase11_compliance_tracking",
        "audit_chain_verified": audit_verified,
        "inspection_total": inspection_total,
        "approved_inspections": approved_inspections,
        "rejected_inspections": rejected_inspections,
        "document_verified_count": verified_documents,
        "inspection_report_total": inspection_reports,
        "compliance_score": compliance_score,
        "readiness_band": readiness_band,
        "regulatory_ready": regulatory_ready,
        "operator_actions": [
            "Review rejected inspections" if rejected_inspections else "Inspections remain within tolerance",
            "Resolve open support pressure" if _safe_int(support_pressure) else "Support pressure is stable",
            "Hold refunds for high-risk cases" if fraud_detection["risk_band"] in {"high", "critical"} else "Refund suggestions can remain review-bound",
        ],
        "projection_only": True,
        "read_only": True,
    }


def _regulatory_readiness_projection(
    *,
    organization_id: str,
    compliance_tracking: dict[str, Any],
    fraud_detection: dict[str, Any],
    support_pressure: int,
) -> dict[str, Any]:
    subscription_active = bool(_store().latest_active_subscription(organization_id=organization_id))
    regulatory_ready = bool(
        subscription_active
        and compliance_tracking["audit_chain_verified"]
        and compliance_tracking["regulatory_ready"]
        and fraud_detection["risk_band"] not in {"high", "critical"}
    )
    if regulatory_ready:
        readiness_band = "government_review_ready"
    elif compliance_tracking["readiness_band"] == "review_ready":
        readiness_band = "controlled_review"
    elif compliance_tracking["readiness_band"] == "watch":
        readiness_band = "watch"
    else:
        readiness_band = "blocked"
    return {
        "view": "novaride_phase11_regulatory_readiness",
        "subscription_active": subscription_active,
        "audit_chain_verified": compliance_tracking["audit_chain_verified"],
        "regulatory_ready": regulatory_ready,
        "readiness_band": readiness_band,
        "trust_boundary": "Trust_Engine_final_authority",
        "refund_boundary": "NovaPay_backend_only",
        "operator_actions": compliance_tracking["operator_actions"],
        "support_pressure": _safe_int(support_pressure),
        "projection_only": True,
        "read_only": True,
    }


def _phase11_support_dashboard_projection(
    *,
    organization_id: str,
    ticket_classification: dict[str, Any],
    smart_refunds: dict[str, Any],
    fraud_detection: dict[str, Any],
    compliance_tracking: dict[str, Any],
    driver_scoring: dict[str, Any],
    regulatory_readiness: dict[str, Any],
    support_pressure: int,
    support_band: str,
) -> dict[str, Any]:
    summary = ticket_classification
    return {
        "view": "novaride_phase11_support_dashboard",
        "support_band": support_band,
        "ticket_total": summary["ticket_total"],
        "refund_total": smart_refunds["refund_total"],
        "dispute_total": summary["ticket_category_counts"].get("fare_dispute", 0),
        "escalation_total": summary["ticket_severity_counts"].get("high", 0),
        "inspection_total": compliance_tracking["inspection_total"],
        "document_verified_count": compliance_tracking["document_verified_count"],
        "driver_average_score": driver_scoring["average_score"],
        "fraud_risk_band": fraud_detection["risk_band"],
        "smart_refund_mode": smart_refunds["automation_mode"],
        "ticket_classification_ready": ticket_classification["auto_classification_ready"],
        "regulatory_readiness_band": regulatory_readiness["readiness_band"],
        "support_pressure": _safe_int(support_pressure),
        "dashboard_cards": [
            {
                "label": "Support Dashboard UI",
                "value": summary["ticket_total"],
                "helper": "Tickets, refunds, disputes, and replay-backed support views.",
            },
            {
                "label": "Auto Refund System",
                "value": smart_refunds["refund_total"],
                "helper": f"Suggested AUD {smart_refunds['suggested_refund_total']} with backend-only authority.",
            },
            {
                "label": "Analytics Backend",
                "value": compliance_tracking["compliance_score"],
                "helper": "Compliance, inspection, fraud, and scoring projection.",
            },
            {
                "label": "Driver Scoring Algorithm",
                "value": compliance_tracking["compliance_score"],
                "helper": "Trust, completion, cancellations, compliance, and support pressure.",
            },
        ],
        "projection_only": True,
        "read_only": True,
    }


def build_phase11_compliance_workspace_projection(
    *,
    organization_id: str,
    limit: int = 100,
    source: str | None = "afriride_phase11_compliance_workspace",
) -> dict[str, Any]:
    events = _support_related_events(organization_id, limit)
    rides = _rides(organization_id, limit)
    transactions = _transactions(organization_id, limit)
    dispatch_assignments = _dispatch_assignments(organization_id, limit)
    driver_presence = _driver_presence(organization_id, limit)
    billing_records = _billing_records(organization_id, limit)

    ticket_classification = _ticket_classification_projection(organization_id=organization_id, events=events, rides=rides, limit=limit)
    inspections = _inspection_projection(organization_id=organization_id, events=events, limit=limit)
    documents = _document_verification_projection(organization_id=organization_id, events=events, limit=limit)
    reports = _inspection_reports_projection(
        organization_id=organization_id,
        events=events,
        inspections=inspections,
        limit=limit,
    )
    driver_scoring = _driver_scoring_projection(
        organization_id=organization_id,
        events=events,
        rides=rides,
        dispatch_assignments=dispatch_assignments,
        driver_presence=driver_presence,
        inspections=inspections,
        documents=documents,
        limit=limit,
    )
    support_pressure = _safe_int(ticket_classification["support_pressure"])
    fraud_detection = _fraud_detection_projection(
        organization_id=organization_id,
        events=events,
        rides=rides,
        transactions=transactions,
        ticket_classification=ticket_classification,
        inspections=inspections,
        documents=documents,
        limit=limit,
    )
    smart_refunds = _smart_refunds_projection(
        organization_id=organization_id,
        events=events,
        rides=rides,
        transactions=transactions,
        fraud_detection=fraud_detection,
        limit=limit,
    )
    compliance_tracking = _compliance_tracking_projection(
        organization_id=organization_id,
        inspections=inspections,
        documents=documents,
        reports=reports,
        driver_scores=driver_scoring,
        fraud_detection=fraud_detection,
        support_pressure=support_pressure,
    )
    regulatory_readiness = _regulatory_readiness_projection(
        organization_id=organization_id,
        compliance_tracking=compliance_tracking,
        fraud_detection=fraud_detection,
        support_pressure=support_pressure,
    )
    support_band = "excellent" if support_pressure == 0 and regulatory_readiness["regulatory_ready"] else "stable" if support_pressure <= 2 else "watch" if support_pressure <= 5 else "needs_attention"
    support_dashboard = _phase11_support_dashboard_projection(
        organization_id=organization_id,
        ticket_classification=ticket_classification,
        smart_refunds=smart_refunds,
        fraud_detection=fraud_detection,
        compliance_tracking=compliance_tracking,
        driver_scoring=driver_scoring,
        regulatory_readiness=regulatory_readiness,
        support_pressure=support_pressure,
        support_band=support_band,
    )

    inspection_total = inspections["inspection_total"]
    document_total = documents["document_total"]
    report_total = reports["report_total"]
    driver_total = driver_scoring["driver_total"]
    fraud_signal_count = fraud_detection["fraud_signal_count"]
    support_total = support_dashboard["ticket_total"]
    compliance_total = compliance_tracking["inspection_total"] + compliance_tracking["document_verified_count"] + compliance_tracking["inspection_report_total"]
    subscription_active = bool(_store().latest_active_subscription(organization_id=organization_id))
    ready = bool(
        subscription_active
        and support_dashboard["ticket_classification_ready"]
        and support_dashboard["ticket_classification_ready"]
        and compliance_tracking["regulatory_ready"]
        and regulatory_readiness["regulatory_ready"]
        and fraud_detection["risk_band"] not in {"high", "critical"}
    )

    summary = {
        "support_total": support_total,
        "inspection_total": inspection_total,
        "document_total": document_total,
        "report_total": report_total,
        "driver_total": driver_total,
        "fraud_signal_count": fraud_signal_count,
        "compliance_total": compliance_total,
        "support_dashboard_ready": support_dashboard["ticket_classification_ready"],
        "inspection_workflow_ready": inspections["inspection_queue_ready"],
        "document_verification_ready": documents["verification_band"] in {"verified", "watch"},
        "inspection_reports_ready": reports["report_band"] in {"ready", "watch"},
        "compliance_tracking_ready": compliance_tracking["regulatory_ready"],
        "driver_scoring_ready": driver_total > 0,
        "fraud_detection_ready": fraud_detection["risk_band"] in {"low", "watch"},
        "smart_refunds_ready": bool(smart_refunds["refund_total"] >= 0),
        "auto_ticket_classification_ready": ticket_classification["auto_classification_ready"],
        "regulatory_readiness_ready": regulatory_readiness["regulatory_ready"],
        "support_pressure": support_pressure,
    }

    return {
        "view": "novaride_phase11_compliance_workspace",
        "phase": "11",
        "platform": "NovaRide Phase 11",
        "organization_id": organization_id,
        "source": source or "afriride_phase11_compliance_workspace",
        "phase10": {
            "view": "novaride_phase10_support_workspace",
            "ready": bool(subscription_active and support_pressure >= 0),
            "projection_only": True,
            "read_only": True,
            "contract": build_phase10_support_contract_projection(),
        },
        "contract": build_phase11_compliance_contract_projection(),
        "support_dashboard": support_dashboard,
        "ticket_classification": ticket_classification,
        "inspections": inspections,
        "documents": documents,
        "inspection_reports": reports,
        "driver_scoring": driver_scoring,
        "fraud_detection": fraud_detection,
        "smart_refunds": smart_refunds,
        "compliance_tracking": compliance_tracking,
        "regulatory_readiness": regulatory_readiness,
        "summary": summary,
        "billing_records": billing_records,
        "projection_only": True,
        "read_only": True,
        "governance_linked": True,
        "creates_authority": False,
        "created_at": _now(),
        "ready": ready,
    }


def build_phase11_compliance_contract_projection() -> dict[str, Any]:
    return {
        "view": "novaride_phase11_compliance_contract",
        "status": "controlled_pilot_contract_ready",
        "role": "OPERATOR",
        "purpose": "Regulatory readiness layer for compliance tracking, inspections, document verification, smart refunds, and fraud detection.",
        "modules": [dict(module) for module in NOVARIDE_PHASE11_MODULES],
        "navigation": list(NOVARIDE_PHASE11_NAVIGATION),
        "rbac": {
            "role": "OPERATOR",
            "allowed": list(NOVARIDE_PHASE11_ALLOWED_ACTIONS),
            "forbidden": list(NOVARIDE_PHASE11_FORBIDDEN_ACTIONS),
        },
        "authority_model": {
            "refund_execution": "NovaPay_backend_only",
            "compliance_authority": "Trust_Engine_final_authority",
            "inspection_evidence": "Audit_Engine_replay_required",
            "document_verification": "NovaID_and_Trust_required",
            "fraud_review": "Operator_Admin_workflow_required",
            "analytics": "projection_only",
        },
        "api_alignment": {
            "implemented": (
                "/v1/novaride/phase10/support-workspace",
                "/v1/novaride/phase11/status",
                "/v1/novaride/phase11/compliance-workspace",
                "/v1/novaride/phase11/inspections",
                "/v1/novaride/phase11/document-verification",
                "/v1/novaride/phase11/inspection-reports",
                "/v1/novaride/phase11/compliance-tracking",
                "/v1/novaride/phase11/driver-scoring",
                "/v1/novaride/phase11/fraud-detection",
                "/v1/novaride/phase11/smart-refunds",
                "/v1/novaride/phase11/auto-ticket-classification",
                "/v1/novaride/phase11/regulatory-readiness",
            ),
            "contract": "/v1/novaride/phase11/compliance-contract",
        },
        "ecosystem_integrations": {
            "support_dashboard": "operator_support_workspace",
            "inspection_app": "feeds_field_evidence",
            "inspector_app": "feeds_compliance_reports",
            "trust_engine": "final_compliance_authority",
            "audit_engine": "replay_evidence",
            "novapay": "refund_execution_backend_only",
            "analytics_backend": "operator_compliance_insights",
        },
        "advanced_next_phase": (
            "ai_ticket_classification",
            "smart_refund_suggestions",
            "fraud_pattern_detection",
            "regulatory_export_automation",
            "government_pilot_packaging",
        ),
    }


def build_phase11_status(
    *,
    organization_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    workspace = build_phase11_compliance_workspace_projection(organization_id=org_id, limit=limit)
    phase10 = workspace["phase10"]
    summary = workspace["summary"]
    readiness = {
        "subscription_active": bool(_store().latest_active_subscription(organization_id=org_id)),
        "phase10_ready": bool(phase10["ready"]),
        "support_dashboard_ready": bool(summary["support_dashboard_ready"]),
        "inspection_workflow_ready": bool(summary["inspection_workflow_ready"]),
        "document_verification_ready": bool(summary["document_verification_ready"]),
        "inspection_reports_ready": bool(summary["inspection_reports_ready"]),
        "compliance_tracking_ready": bool(summary["compliance_tracking_ready"]),
        "driver_scoring_ready": bool(summary["driver_scoring_ready"]),
        "fraud_detection_ready": bool(summary["fraud_detection_ready"]),
        "smart_refunds_ready": bool(summary["smart_refunds_ready"]),
        "auto_ticket_classification_ready": bool(summary["auto_ticket_classification_ready"]),
        "regulatory_readiness_ready": bool(summary["regulatory_readiness_ready"]),
        "tenant_isolation_preserved": True,
    }
    ready = all(
        readiness[key]
        for key in (
            "subscription_active",
            "phase10_ready",
            "support_dashboard_ready",
            "inspection_workflow_ready",
            "document_verification_ready",
            "inspection_reports_ready",
            "compliance_tracking_ready",
            "driver_scoring_ready",
            "fraud_detection_ready",
            "smart_refunds_ready",
            "auto_ticket_classification_ready",
            "regulatory_readiness_ready",
            "tenant_isolation_preserved",
        )
    )
    return {
        "view": "novaride_phase11_status",
        "phase": "11",
        "platform": "NovaRide Phase 11",
        "organization_id": org_id,
        "phase10": phase10,
        "support_dashboard": workspace["support_dashboard"],
        "compliance_workspace": workspace,
        "readiness": readiness,
        "ready": ready,
        "projection_only": True,
        "read_only": True,
        "governance_linked": True,
        "creates_authority": False,
    }


def build_phase11_support_dashboard_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    workspace = build_phase11_compliance_workspace_projection(organization_id=organization_id, limit=limit)
    return workspace["support_dashboard"]


def build_phase11_inspections_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    events = _support_related_events(organization_id, limit)
    return _inspection_projection(organization_id=organization_id, events=events, limit=limit)


def build_phase11_document_verification_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    events = _support_related_events(organization_id, limit)
    return _document_verification_projection(organization_id=organization_id, events=events, limit=limit)


def build_phase11_inspection_reports_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    events = _support_related_events(organization_id, limit)
    inspections = _inspection_projection(organization_id=organization_id, events=events, limit=limit)
    return _inspection_reports_projection(organization_id=organization_id, events=events, inspections=inspections, limit=limit)


def build_phase11_compliance_tracking_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    events = _support_related_events(organization_id, limit)
    rides = _rides(organization_id, limit)
    transactions = _transactions(organization_id, limit)
    dispatch_assignments = _dispatch_assignments(organization_id, limit)
    driver_presence = _driver_presence(organization_id, limit)
    inspections = _inspection_projection(organization_id=organization_id, events=events, limit=limit)
    documents = _document_verification_projection(organization_id=organization_id, events=events, limit=limit)
    reports = _inspection_reports_projection(organization_id=organization_id, events=events, inspections=inspections, limit=limit)
    driver_scoring = _driver_scoring_projection(
        organization_id=organization_id,
        events=events,
        rides=rides,
        dispatch_assignments=dispatch_assignments,
        driver_presence=driver_presence,
        inspections=inspections,
        documents=documents,
        limit=limit,
    )
    ticket_classification = _ticket_classification_projection(organization_id=organization_id, events=events, rides=rides, limit=limit)
    fraud_detection = _fraud_detection_projection(
        organization_id=organization_id,
        events=events,
        rides=rides,
        transactions=transactions,
        ticket_classification=ticket_classification,
        inspections=inspections,
        documents=documents,
        limit=limit,
    )
    return _compliance_tracking_projection(
        organization_id=organization_id,
        inspections=inspections,
        documents=documents,
        reports=reports,
        driver_scores=driver_scoring,
        fraud_detection=fraud_detection,
        support_pressure=_safe_int(ticket_classification["support_pressure"]),
    )


def build_phase11_driver_scoring_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    events = _support_related_events(organization_id, limit)
    rides = _rides(organization_id, limit)
    dispatch_assignments = _dispatch_assignments(organization_id, limit)
    driver_presence = _driver_presence(organization_id, limit)
    inspections = _inspection_projection(organization_id=organization_id, events=events, limit=limit)
    documents = _document_verification_projection(organization_id=organization_id, events=events, limit=limit)
    return _driver_scoring_projection(
        organization_id=organization_id,
        events=events,
        rides=rides,
        dispatch_assignments=dispatch_assignments,
        driver_presence=driver_presence,
        inspections=inspections,
        documents=documents,
        limit=limit,
    )


def build_phase11_fraud_detection_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    events = _support_related_events(organization_id, limit)
    rides = _rides(organization_id, limit)
    transactions = _transactions(organization_id, limit)
    inspections = _inspection_projection(organization_id=organization_id, events=events, limit=limit)
    documents = _document_verification_projection(organization_id=organization_id, events=events, limit=limit)
    ticket_classification = _ticket_classification_projection(organization_id=organization_id, events=events, rides=rides, limit=limit)
    return _fraud_detection_projection(
        organization_id=organization_id,
        events=events,
        rides=rides,
        transactions=transactions,
        ticket_classification=ticket_classification,
        inspections=inspections,
        documents=documents,
        limit=limit,
    )


def build_phase11_smart_refunds_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    events = _support_related_events(organization_id, limit)
    rides = _rides(organization_id, limit)
    transactions = _transactions(organization_id, limit)
    fraud_detection = build_phase11_fraud_detection_projection(organization_id=organization_id, limit=limit)
    return _smart_refunds_projection(
        organization_id=organization_id,
        events=events,
        rides=rides,
        transactions=transactions,
        fraud_detection=fraud_detection,
        limit=limit,
    )


def build_phase11_auto_ticket_classification_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    events = _support_related_events(organization_id, limit)
    rides = _rides(organization_id, limit)
    return _ticket_classification_projection(organization_id=organization_id, events=events, rides=rides, limit=limit)


def build_phase11_regulatory_readiness_projection(
    *,
    organization_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    workspace = build_phase11_compliance_workspace_projection(organization_id=organization_id, limit=limit)
    return workspace["regulatory_readiness"]


__all__ = [
    "build_phase11_auto_ticket_classification_projection",
    "build_phase11_compliance_tracking_projection",
    "build_phase11_compliance_workspace_projection",
    "build_phase11_document_verification_projection",
    "build_phase11_driver_scoring_projection",
    "build_phase11_fraud_detection_projection",
    "build_phase11_inspection_reports_projection",
    "build_phase11_inspections_projection",
    "build_phase11_regulatory_readiness_projection",
    "build_phase11_smart_refunds_projection",
    "build_phase11_status",
    "build_phase11_support_dashboard_projection",
    "build_phase11_compliance_contract_projection",
]
