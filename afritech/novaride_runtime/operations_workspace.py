"""Operational workspace service for NovaRide Operations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from afritech.novaride_runtime.common.clocks import utc_now
from afritech.novaride_runtime.common.errors import AuthorityDenied
from afritech.novaride_runtime.common.geography import AddressRef, GeoPoint
from afritech.novaride_runtime.common.identifiers import new_id
from afritech.novaride_runtime.common.money import Money
from afritech.novaride_runtime.events.envelope import MobilityEvent
from afritech.novaride_runtime.events.hashing import canonical_hash
from afritech.novaride_runtime.models import (
    ActorType,
    DriverAvailability,
    DriverAvailabilityState,
    DriverOffer,
    DriverProfile,
    EmergencyCase,
    EmergencyState,
    Incident,
    IncidentState as RuntimeIncidentState,
    OfferState,
    Trip,
    TripState,
)
from afritech.novaride_runtime.services import NovaRideRuntime


class IncidentState(StrEnum):
    DETECTED = "detected"
    DECLARED = "declared"
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    MITIGATING = "mitigating"
    MONITORING = "monitoring"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class SafetyCaseState(StrEnum):
    NEW = "new"
    TRIAGED = "triaged"
    ASSIGNED = "assigned"
    ESCALATED = "escalated"
    RESPONDING = "responding"
    MONITORING = "monitoring"
    RESOLVED = "resolved"
    CLOSED = "closed"


class SupportCaseState(StrEnum):
    NEW = "new"
    TRIAGED = "triaged"
    ASSIGNED = "assigned"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class RefundState(StrEnum):
    REQUESTED = "requested"
    EVALUATED = "evaluated"
    APPROVAL_PENDING = "approval_pending"
    APPROVED = "approved"
    EXECUTING = "executing"
    VERIFIED = "verified"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"
    CANCELLED = "cancelled"
    VERIFICATION_FAILED = "verification_failed"


class InvestigationState(StrEnum):
    OPEN = "open"
    TRIAGED = "triaged"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    CLOSED = "closed"


class DisputeState(StrEnum):
    OPEN = "open"
    ASSIGNED = "assigned"
    REQUEST_EVIDENCE = "request_evidence"
    DECIDED = "decided"
    APPEALED = "appealed"
    CLOSED = "closed"


class OperationalActionState(StrEnum):
    REQUESTED = "requested"
    EVALUATED = "evaluated"
    APPROVAL_PENDING = "approval_pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    VERIFIED = "verified"
    CANCELLED = "cancelled"


def _iso_now() -> str:
    return utc_now().isoformat()


def _serialise(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _serialise(item) for key, item in asdict(value).items()}
    if isinstance(value, tuple):
        return [_serialise(item) for item in value]
    if isinstance(value, list):
        return [_serialise(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialise(item) for key, item in value.items()}
    if hasattr(value, "value"):
        return value.value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    return value


@dataclass(slots=True)
class TimelineEntry:
    id: str
    event_type: str
    occurred_at: datetime
    actor_id: str
    request_id: str
    trace_id: str
    correlation_id: str
    message: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DependencyStatus:
    name: str
    status: str
    observed_at: datetime
    latency_ms: int | None = None
    message: str = ""
    source: str = "novaride_runtime"
    degraded_reason: str | None = None


@dataclass(slots=True)
class OperationalIncident:
    incident_id: str
    tenant_id: str
    region_id: str
    title: str
    severity: str
    status: IncidentState = IncidentState.DETECTED
    description: str = ""
    affected_trips: tuple[str, ...] = ()
    affected_services: tuple[str, ...] = ()
    assigned_to: str | None = None
    commander: str | None = None
    created_by: str = ""
    updated_by: str = ""
    request_id: str = ""
    trace_id: str = ""
    correlation_id: str = ""
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    timeline: list[TimelineEntry] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SafetyCase:
    case_id: str
    tenant_id: str
    region_id: str
    status: SafetyCaseState
    severity: str
    linked_trip_id: str | None = None
    linked_driver_id: str | None = None
    linked_rider_id: str | None = None
    linked_vehicle_id: str | None = None
    incident_id: str | None = None
    assigned_to: str | None = None
    created_by: str = ""
    updated_by: str = ""
    request_id: str = ""
    trace_id: str = ""
    correlation_id: str = ""
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    timeline: list[TimelineEntry] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SupportCase:
    case_id: str
    tenant_id: str
    region_id: str
    case_type: str
    status: SupportCaseState = SupportCaseState.NEW
    trip_id: str | None = None
    rider_id: str | None = None
    driver_id: str | None = None
    payment_id: str | None = None
    receipt_id: str | None = None
    phone: str | None = None
    email: str | None = None
    assigned_to: str | None = None
    created_by: str = ""
    updated_by: str = ""
    request_id: str = ""
    trace_id: str = ""
    correlation_id: str = ""
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    timeline: list[TimelineEntry] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RefundRequest:
    refund_id: str
    tenant_id: str
    region_id: str
    amount: Decimal
    currency: str
    payment_id: str | None = None
    receipt_id: str | None = None
    trip_id: str | None = None
    support_case_id: str | None = None
    status: RefundState = RefundState.REQUESTED
    approval_required: bool = False
    requester_id: str = ""
    approver_id: str | None = None
    verified_by: str | None = None
    updated_by: str = ""
    idempotency_key: str = ""
    reason: str = ""
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    timeline: list[TimelineEntry] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PaymentInvestigation:
    investigation_id: str
    tenant_id: str
    region_id: str
    payment_id: str
    status: InvestigationState = InvestigationState.OPEN
    reason: str = ""
    created_by: str = ""
    assigned_to: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    timeline: list[TimelineEntry] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DisputeRecord:
    dispute_id: str
    tenant_id: str
    region_id: str
    trip_id: str | None = None
    payment_id: str | None = None
    support_case_id: str | None = None
    status: DisputeState = DisputeState.OPEN
    policy_version: str = "2026.2"
    reviewer_id: str | None = None
    appeal_state: str = "none"
    created_by: str = ""
    updated_by: str = ""
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    timeline: list[TimelineEntry] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class OperationalAction:
    action_id: str
    tenant_id: str
    region_id: str
    action_type: str
    target_id: str
    status: OperationalActionState = OperationalActionState.REQUESTED
    requested_by: str = ""
    approved_by: str | None = None
    executed_by: str | None = None
    verified_by: str | None = None
    reason: str = ""
    approval_reference: str | None = None
    approval_required: bool = True
    risk_level: str = "medium"
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    timeline: list[TimelineEntry] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class EvidenceRecord:
    evidence_id: str
    evidence_type: str
    subject_type: str
    subject_id: str
    tenant_id: str
    region_id: str
    actor_id: str
    correlation_id: str
    integrity_status: str
    created_at: datetime = field(default_factory=utc_now)
    source_records: list[str] = field(default_factory=list)
    timeline: list[TimelineEntry] = field(default_factory=list)
    verification_status: str = "pending"
    redacted: bool = True


def _timeline_entry(
    *,
    event_type: str,
    actor_id: str,
    request_id: str,
    trace_id: str,
    correlation_id: str,
    message: str,
    payload: dict[str, Any] | None = None,
) -> TimelineEntry:
    return TimelineEntry(
        id=new_id("timeline"),
        event_type=event_type,
        occurred_at=utc_now(),
        actor_id=actor_id,
        request_id=request_id,
        trace_id=trace_id,
        correlation_id=correlation_id,
        message=message,
        payload=payload or {},
    )


class OperationsWorkspaceService:
    def __init__(
        self,
        runtime: NovaRideRuntime,
        *,
        support_record_repository: Any | None = None,
    ) -> None:
        self.runtime = runtime
        self._support_record_repository = support_record_repository
        self.incidents: dict[str, OperationalIncident] = {}
        self.safety_cases: dict[str, SafetyCase] = {}
        self.support_cases: dict[str, SupportCase] = {}
        self.refunds: dict[str, RefundRequest] = {}
        self.investigations: dict[str, PaymentInvestigation] = {}
        self.disputes: dict[str, DisputeRecord] = {}
        self.actions: dict[str, OperationalAction] = {}
        self.evidence: dict[str, EvidenceRecord] = {}
        self._idempotency_index: dict[tuple[str, str, str], dict[str, str]] = {}
        self._browser_fixture_seeded = False

    def _tenant_scope(self, context) -> tuple[str, str, str]:
        return context.tenant_id, self._region_code(context), context.subject_id

    def _region_code(self, context) -> str:
        return str(getattr(context, "region_code", getattr(context, "region", "AU")))

    def _idempotency_record(self, operation: str, tenant_id: str, key: str) -> dict[str, str] | None:
        if not key:
            return None
        return self._idempotency_index.get((operation, tenant_id, key))

    def _register_idempotency(self, operation: str, tenant_id: str, key: str, *, record_id: str, payload_hash: str) -> None:
        if key:
            self._idempotency_index[(operation, tenant_id, key)] = {
                "record_id": record_id,
                "payload_hash": payload_hash,
            }

    def _idempotency_record_id(self, operation: str, tenant_id: str, key: str, payload_hash: str) -> str | None:
        record = self._idempotency_record(operation, tenant_id, key)
        if record is None:
            return None
        if record.get("payload_hash") != payload_hash:
            raise ValueError("idempotency_conflict")
        return record.get("record_id")

    def _request_meta(self, context, request) -> dict[str, str]:
        return {
            "actor_id": context.subject_id,
            "request_id": request.headers.get("X-Request-Id") or new_id("req"),
            "trace_id": request.headers.get("X-Trace-Id") or new_id("trace"),
            "correlation_id": request.headers.get("X-Correlation-Id")
            or context.correlation_id
            or new_id("corr"),
        }

    def _evidence_record(
        self,
        *,
        tenant_id: str,
        region_id: str,
        actor_id: str,
        subject_type: str,
        subject_id: str,
        source_records: list[str],
        timeline: list[TimelineEntry],
        correlation_id: str,
        integrity_status: str = "verified",
        verification_status: str = "verified",
    ) -> EvidenceRecord:
        record = EvidenceRecord(
            evidence_id=new_id("evidence"),
            evidence_type=f"{subject_type}.lifecycle",
            subject_type=subject_type,
            subject_id=subject_id,
            tenant_id=tenant_id,
            region_id=region_id,
            actor_id=actor_id,
            correlation_id=correlation_id,
            integrity_status=integrity_status,
            source_records=source_records,
            timeline=timeline,
            verification_status=verification_status,
            redacted=True,
        )
        self.evidence[record.evidence_id] = record
        return record

    def _store_timeline(
        self,
        record: Any,
        *,
        event_type: str,
        actor_id: str,
        request_id: str,
        trace_id: str,
        correlation_id: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> TimelineEntry:
        entry = _timeline_entry(
            event_type=event_type,
            actor_id=actor_id,
            request_id=request_id,
            trace_id=trace_id,
            correlation_id=correlation_id,
            message=message,
            payload=payload,
        )
        record.timeline.append(entry)
        record.updated_at = utc_now()
        return entry

    def dependency_statuses(self) -> list[dict[str, Any]]:
        resilience = self.runtime.resilience.status()
        statuses = [
            DependencyStatus(
                name="PostgreSQL",
                status="unknown",
                observed_at=utc_now(),
                message="No live database probe configured in this runtime",
                source="runtime_configuration",
                degraded_reason=None if resilience.get("core_journey_preserved_under_degradation") else "runtime_degraded",
            ),
            DependencyStatus(
                name="Redis",
                status="unknown",
                observed_at=utc_now(),
                message="No live cache probe configured in this runtime",
                source="runtime_configuration",
                degraded_reason="probe_not_configured",
            ),
            DependencyStatus(
                name="Event transport",
                status="unknown",
                observed_at=utc_now(),
                message="No live broker probe configured in this runtime",
                source="runtime_configuration",
                degraded_reason="probe_not_configured",
            ),
            DependencyStatus(
                name="Trace backend",
                status="unknown",
                observed_at=utc_now(),
                message="Trace ingestion not verified from this process",
                source="runtime_configuration",
                degraded_reason="trace_ingestion_not_verified",
            ),
            DependencyStatus(
                name="Evidence store",
                status="unknown",
                observed_at=utc_now(),
                message="Evidence persistence not externally verified from this process",
                source="runtime_configuration",
                degraded_reason="evidence_store_not_verified",
            ),
        ]
        return [_serialise(item) for item in statuses]

    def overview(self, context) -> dict[str, Any]:
        tenant_id = context.tenant_id
        trips = self.runtime.repositories.trips.list(tenant_id=tenant_id)
        availabilities = self.runtime.repositories.availability.list(tenant_id=tenant_id)
        incidents = self._all_incidents(tenant_id)
        safety_cases = self._all_safety_cases(tenant_id)
        support_cases = self._all_support_cases(tenant_id)
        refunds = self._all_refunds(tenant_id)
        actions = self._all_actions(tenant_id)
        investigations = self._all_investigations(tenant_id)
        recent_activity = self._recent_activity(tenant_id, limit=8)
        alerts = self._alerts(tenant_id)
        dependencies = self.dependency_statuses()
        return {
            "generated_at": _iso_now(),
            "environment": "production",
            "summary": {
                "active_trips": len([trip for trip in trips if trip.lifecycle_state not in {TripState.COMPLETED, TripState.CANCELLED}]),
                "drivers_online": len([item for item in availabilities if item.authoritative_state != DriverAvailabilityState.OFFLINE]),
                "drivers_available": len([item for item in availabilities if item.dispatchable]),
                "riders_active": len({trip.rider_id for trip in trips if trip.lifecycle_state not in {TripState.COMPLETED, TripState.CANCELLED}}),
                "open_incidents": len([incident for incident in incidents if incident.status not in {IncidentState.RESOLVED, IncidentState.CLOSED, IncidentState.CANCELLED}]),
                "critical_incidents": len([incident for incident in incidents if incident.severity in {"SEV0", "SEV1"} and incident.status not in {IncidentState.RESOLVED, IncidentState.CLOSED, IncidentState.CANCELLED}]),
                "open_safety_cases": len([case for case in safety_cases if case.status not in {SafetyCaseState.RESOLVED, SafetyCaseState.CLOSED}]),
                "open_support_cases": len([case for case in support_cases if case.status not in {SupportCaseState.RESOLVED, SupportCaseState.CLOSED}]),
                "pending_refunds": len([refund for refund in refunds if refund.status in {RefundState.REQUESTED, RefundState.EVALUATED, RefundState.APPROVAL_PENDING, RefundState.APPROVED, RefundState.EXECUTING}]),
                "payment_failures": len([investigation for investigation in investigations if investigation.status in {InvestigationState.OPEN, InvestigationState.TRIAGED, InvestigationState.IN_REVIEW}]),
                "pending_approvals": len([action for action in actions if action.status == OperationalActionState.APPROVAL_PENDING]) + len([refund for refund in refunds if refund.status == RefundState.APPROVAL_PENDING]),
            },
            "dependencies": dependencies,
            "recent_activity": recent_activity,
            "alerts": alerts,
        }

    def live_trips(self, context, *, limit: int = 50) -> dict[str, Any]:
        trips = self.runtime.repositories.trips.list(tenant_id=context.tenant_id)
        offers = {offer.trip_id: offer for offer in self.runtime.repositories.offers.list(tenant_id=context.tenant_id)}
        items = []
        for trip in trips[:limit]:
            last_event = self._latest_trip_location(trip.id)
            offer = offers.get(trip.id)
            items.append(
                {
                    "trip_id": trip.id,
                    "driver_id": trip.driver_id,
                    "rider_id": trip.rider_id,
                    "vehicle_id": trip.vehicle_id,
                    "status": trip.lifecycle_state.value,
                    "pickup": _serialise(trip.pickup),
                    "destination": _serialise(trip.destination),
                    "current_location": last_event["current_location"] if last_event else None,
                    "heading": last_event["heading"] if last_event else None,
                    "speed": last_event["speed"] if last_event else None,
                    "last_location_at": last_event["last_location_at"] if last_event else None,
                    "region": trip.region_code,
                    "service_area": f"region:{trip.region_code}",
                    "incident_status": self._incident_status_for_trip(context.tenant_id, trip.id),
                    "safety_status": self._safety_status_for_trip(context.tenant_id, trip.id),
                    "offer_status": offer.state.value if offer else None,
                }
            )
        return {"generated_at": _iso_now(), "items": items}

    def live_drivers(self, context, *, limit: int = 50) -> dict[str, Any]:
        availabilities = self.runtime.repositories.availability.list(tenant_id=context.tenant_id)
        drivers = self.runtime.repositories.drivers.list(tenant_id=context.tenant_id)
        driver_map = {driver.id: driver for driver in drivers}
        items = []
        for availability in availabilities[:limit]:
            driver = driver_map.get(availability.driver_id)
            items.append(
                {
                    "driver_id": availability.driver_id,
                    "vehicle_id": availability.vehicle_id,
                    "status": availability.authoritative_state.value,
                    "dispatchable": availability.dispatchable,
                    "region": availability.region_code,
                    "last_location_at": availability.server_confirmed_at.isoformat() if availability.server_confirmed_at else None,
                    "last_seen": availability.server_confirmed_at.isoformat() if availability.server_confirmed_at else None,
                    "driver_name": driver.display_name if driver else None,
                    "trust_status": "verified" if driver else "unknown",
                    "location_precision": "unknown",
                }
            )
        return {"generated_at": _iso_now(), "items": items}

    def live_map(self, context, *, limit: int = 100) -> dict[str, Any]:
        trips = self.runtime.repositories.trips.list(tenant_id=context.tenant_id)
        items = []
        for trip in trips[:limit]:
            location = self._latest_trip_location(trip.id)
            items.append(
                {
                    "trip_id": trip.id,
                    "driver_id": trip.driver_id,
                    "rider_id": trip.rider_id,
                    "vehicle_id": trip.vehicle_id,
                    "status": trip.lifecycle_state.value,
                    "pickup": _serialise(trip.pickup),
                    "destination": _serialise(trip.destination),
                    "current_location": location["current_location"] if location else None,
                    "heading": location["heading"] if location else None,
                    "speed": location["speed"] if location else None,
                    "last_location_at": location["last_location_at"] if location else None,
                    "region": trip.region_code,
                    "service_area": f"region:{trip.region_code}",
                    "incident_status": self._incident_status_for_trip(context.tenant_id, trip.id),
                    "safety_status": self._safety_status_for_trip(context.tenant_id, trip.id),
                }
            )
        return {"generated_at": _iso_now(), "items": items}

    def dispatch_queue(self, context, *, limit: int = 50) -> dict[str, Any]:
        offers = self.runtime.repositories.offers.list(tenant_id=context.tenant_id)
        availabilities = self.runtime.repositories.availability.list(tenant_id=context.tenant_id)
        items = []
        for offer in offers[:limit]:
            availability = next((item for item in availabilities if item.driver_id == offer.driver_id), None)
            items.append(
                {
                    "offer_id": offer.id,
                    "trip_id": offer.trip_id,
                    "driver_id": offer.driver_id,
                    "state": offer.state.value,
                    "estimated_earnings": _serialise(offer.estimated_earnings),
                    "dispatchable": bool(availability.dispatchable) if availability else False,
                    "queue_position": 1,
                    "last_updated_at": offer.updated_at.isoformat(),
                }
            )
        return {"generated_at": _iso_now(), "items": items}

    def dispatch_health(self, context) -> dict[str, Any]:
        queue = self.dispatch_queue(context)
        resilience = self.runtime.resilience.status()
        return {
            "generated_at": _iso_now(),
            "status": "degraded" if queue["items"] and resilience["provider_fallback_total"] else "healthy" if queue["items"] else "unknown",
            "message": "Dispatch queue sourced from runtime repositories",
            "queue_depth": len(queue["items"]),
            "driver_supply": len(self.runtime.repositories.availability.list(tenant_id=context.tenant_id)),
            "trip_backlog": len(self.runtime.repositories.trips.list(tenant_id=context.tenant_id)),
            "source": "runtime.repositories",
            "degraded_reason": None if queue["items"] else "dispatch_queue_empty",
        }

    def create_incident(self, context, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        idempotency_key = str(payload.pop("idempotency_key", "")).strip()
        payload_hash = canonical_hash(payload)
        existing = self._idempotency_record_id("incident", context.tenant_id, idempotency_key, payload_hash)
        if existing:
            incident = self._require_incident(context.tenant_id, existing)
            if incident:
                return self._incident_payload(incident)
        incident = OperationalIncident(
            incident_id=new_id("incident"),
            tenant_id=context.tenant_id,
            region_id=self._region_code(context),
            title=str(payload.get("title", "Operational incident")),
            severity=str(payload.get("severity", "SEV3")),
            status=IncidentState.DETECTED,
            description=str(payload.get("description", "")),
            affected_trips=tuple(str(item) for item in payload.get("affected_trips", []) if item),
            affected_services=tuple(str(item) for item in payload.get("affected_services", []) if item),
            created_by=context.subject_id,
            updated_by=context.subject_id,
            request_id=request_meta["request_id"],
            trace_id=request_meta["trace_id"],
            correlation_id=request_meta["correlation_id"],
        )
        self._store_timeline(
            incident,
            event_type="incident_created",
            actor_id=context.subject_id,
            request_id=request_meta["request_id"],
            trace_id=request_meta["trace_id"],
            correlation_id=request_meta["correlation_id"],
            message="Incident created",
            payload={"severity": incident.severity},
        )
        self.incidents[incident.incident_id] = incident
        self._register_idempotency("incident", context.tenant_id, idempotency_key, record_id=incident.incident_id, payload_hash=payload_hash)
        self._create_evidence(incident=incident, request_meta=request_meta)
        return self._incident_payload(incident)

    def list_incidents(self, context, *, limit: int = 100) -> list[dict[str, Any]]:
        items = self._all_incidents(context.tenant_id)[:limit]
        return [self._incident_payload(item) for item in items]

    def get_incident(self, context, incident_id: str) -> dict[str, Any]:
        incident = self._get_incident(context.tenant_id, incident_id)
        if incident is None:
            raise KeyError("incident_not_found")
        return self._incident_payload(incident)

    def patch_incident(self, context, incident_id: str, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        incident = self._require_incident(context.tenant_id, incident_id)
        if "title" in payload:
            incident.title = str(payload["title"])
        if "description" in payload:
            incident.description = str(payload["description"])
        if "severity" in payload:
            incident.severity = str(payload["severity"])
        if "status" in payload:
            self.transition_incident(context, incident_id, {"status": payload["status"]}, request_meta)
            incident = self._require_incident(context.tenant_id, incident_id)
        incident.updated_by = context.subject_id
        self._store_timeline(
            incident,
            event_type="incident_updated",
            actor_id=context.subject_id,
            request_id=request_meta["request_id"],
            trace_id=request_meta["trace_id"],
            correlation_id=request_meta["correlation_id"],
            message="Incident updated",
            payload={"patch": payload},
        )
        self._create_evidence(incident=incident, request_meta=request_meta)
        return self._incident_payload(incident)

    def transition_incident(self, context, incident_id: str, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        incident = self._require_incident(context.tenant_id, incident_id)
        target = IncidentState(str(payload.get("status") or payload.get("transition") or "")).value
        allowed = {
            IncidentState.DETECTED: {IncidentState.DECLARED, IncidentState.CANCELLED},
            IncidentState.DECLARED: {IncidentState.INVESTIGATING, IncidentState.IDENTIFIED, IncidentState.CANCELLED},
            IncidentState.INVESTIGATING: {IncidentState.IDENTIFIED, IncidentState.MITIGATING, IncidentState.RESOLVED, IncidentState.CANCELLED},
            IncidentState.IDENTIFIED: {IncidentState.MITIGATING, IncidentState.MONITORING, IncidentState.RESOLVED, IncidentState.CANCELLED},
            IncidentState.MITIGATING: {IncidentState.MONITORING, IncidentState.RESOLVED, IncidentState.CANCELLED},
            IncidentState.MONITORING: {IncidentState.RESOLVED, IncidentState.CLOSED, IncidentState.CANCELLED},
            IncidentState.RESOLVED: {IncidentState.CLOSED},
            IncidentState.CLOSED: set(),
            IncidentState.CANCELLED: set(),
        }
        target_state = IncidentState(target)
        if target_state not in allowed[incident.status]:
            raise ValueError("invalid_incident_transition")
        incident.status = target_state
        incident.updated_by = context.subject_id
        self._store_timeline(
            incident,
            event_type="incident_transitioned",
            actor_id=context.subject_id,
            request_id=request_meta["request_id"],
            trace_id=request_meta["trace_id"],
            correlation_id=request_meta["correlation_id"],
            message=f"Incident transitioned to {target_state.value}",
            payload={"status": target_state.value},
        )
        self._create_evidence(incident=incident, request_meta=request_meta)
        return self._incident_payload(incident)

    def assign_incident(self, context, incident_id: str, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        incident = self._require_incident(context.tenant_id, incident_id)
        incident.assigned_to = str(payload.get("assigned_to") or context.subject_id)
        incident.commander = str(payload.get("commander") or incident.assigned_to)
        if incident.status == IncidentState.DETECTED:
            incident.status = IncidentState.DECLARED
        incident.updated_by = context.subject_id
        self._store_timeline(
            incident,
            event_type="incident_assigned",
            actor_id=context.subject_id,
            request_id=request_meta["request_id"],
            trace_id=request_meta["trace_id"],
            correlation_id=request_meta["correlation_id"],
            message="Incident assigned",
            payload={"assigned_to": incident.assigned_to, "commander": incident.commander},
        )
        self._create_evidence(incident=incident, request_meta=request_meta)
        return self._incident_payload(incident)

    def incident_timeline(self, context, incident_id: str) -> list[dict[str, Any]]:
        incident = self._require_incident(context.tenant_id, incident_id)
        return [_serialise(item) for item in incident.timeline]

    def incident_evidence(self, context, incident_id: str) -> list[dict[str, Any]]:
        incident = self._require_incident(context.tenant_id, incident_id)
        return [self._evidence_payload(record) for record in self.evidence.values() if record.subject_type == "incident" and record.subject_id == incident.incident_id]

    def list_safety_cases(self, context, *, limit: int = 100) -> list[dict[str, Any]]:
        cases = self._all_safety_cases(context.tenant_id)[:limit]
        return [self._safety_payload(case) for case in cases]

    def get_safety_case(self, context, case_id: str) -> dict[str, Any]:
        case = self._get_safety_case(context.tenant_id, case_id)
        if case is None:
            raise KeyError("safety_case_not_found")
        return self._safety_payload(case)

    def assign_safety_case(self, context, case_id: str, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        case = self._require_safety_case(context.tenant_id, case_id)
        case.assigned_to = str(payload.get("assigned_to") or context.subject_id)
        case.status = SafetyCaseState.ASSIGNED
        case.updated_by = context.subject_id
        self._store_timeline(
            case,
            event_type="safety_case_assigned",
            actor_id=context.subject_id,
            request_id=request_meta["request_id"],
            trace_id=request_meta["trace_id"],
            correlation_id=request_meta["correlation_id"],
            message="Safety case assigned",
            payload={"assigned_to": case.assigned_to},
        )
        self._create_evidence(safety_case=case, request_meta=request_meta)
        return self._safety_payload(case)

    def escalate_safety_case(self, context, case_id: str, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        case = self._require_safety_case(context.tenant_id, case_id)
        case.status = SafetyCaseState.ESCALATED
        case.updated_by = context.subject_id
        self._store_timeline(
            case,
            event_type="safety_case_escalated",
            actor_id=context.subject_id,
            request_id=request_meta["request_id"],
            trace_id=request_meta["trace_id"],
            correlation_id=request_meta["correlation_id"],
            message="Safety case escalated",
            payload={"reason": str(payload.get("reason", ""))},
        )
        self._create_evidence(safety_case=case, request_meta=request_meta)
        return self._safety_payload(case)

    def timeline_safety_case(self, context, case_id: str) -> list[dict[str, Any]]:
        case = self._require_safety_case(context.tenant_id, case_id)
        return [_serialise(item) for item in case.timeline]

    def resolve_safety_case(self, context, case_id: str, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        case = self._require_safety_case(context.tenant_id, case_id)
        case.status = SafetyCaseState.RESOLVED if str(payload.get("status", "")).lower() != "closed" else SafetyCaseState.CLOSED
        case.updated_by = context.subject_id
        self._store_timeline(
            case,
            event_type="safety_case_resolved",
            actor_id=context.subject_id,
            request_id=request_meta["request_id"],
            trace_id=request_meta["trace_id"],
            correlation_id=request_meta["correlation_id"],
            message="Safety case resolved",
            payload={"resolution": str(payload.get("resolution", ""))},
        )
        self._create_evidence(safety_case=case, request_meta=request_meta)
        return self._safety_payload(case)

    def safety_case_evidence(self, context, case_id: str) -> list[dict[str, Any]]:
        case = self._require_safety_case(context.tenant_id, case_id)
        return [self._evidence_payload(record) for record in self.evidence.values() if record.subject_type == "safety_case" and record.subject_id == case.case_id]

    def list_support_cases(self, context, query: dict[str, Any] | None = None, *, limit: int = 100) -> list[dict[str, Any]]:
        cases = self._all_support_cases(context.tenant_id)
        if query:
            cases = [case for case in cases if self._support_match(case, query, context)]
        return [self._support_payload(case) for case in cases[:limit]]

    def create_support_case(self, context, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        idempotency_key = str(payload.pop("idempotency_key", "")).strip()
        payload_hash = canonical_hash(payload)
        existing = self._support_idempotency_record_id("support_case", context.tenant_id, idempotency_key, payload_hash)
        if existing:
            case = self._require_support_case(context.tenant_id, existing)
            if case:
                return self._support_payload(case)
        case = SupportCase(
            case_id=new_id("support"),
            tenant_id=context.tenant_id,
            region_id=self._region_code(context),
            case_type=str(payload.get("case_type", "booking_problem")),
            status=SupportCaseState.NEW,
            trip_id=payload.get("trip_id"),
            rider_id=payload.get("rider_id"),
            driver_id=payload.get("driver_id"),
            payment_id=payload.get("payment_id"),
            receipt_id=payload.get("receipt_id"),
            phone=payload.get("phone"),
            email=payload.get("email"),
            created_by=context.subject_id,
            updated_by=context.subject_id,
            request_id=request_meta["request_id"],
            trace_id=request_meta["trace_id"],
            correlation_id=request_meta["correlation_id"],
        )
        self._store_timeline(
            case,
            event_type="support_case_created",
            actor_id=context.subject_id,
            request_id=request_meta["request_id"],
            trace_id=request_meta["trace_id"],
            correlation_id=request_meta["correlation_id"],
            message="Support case created",
            payload={"case_type": case.case_type},
        )
        self.support_cases[case.case_id] = case
        self._register_idempotency("support_case", context.tenant_id, idempotency_key, record_id=case.case_id, payload_hash=payload_hash)
        self._persist_support_idempotency(
            case=case,
            operation="support_case",
            key=idempotency_key,
            payload_hash=payload_hash,
        )
        evidence = self._create_evidence(support_case=case, request_meta=request_meta)
        self._persist_support_evidence(evidence)
        self._persist_support_case(case)
        return self._support_payload(case)

    def get_support_case(self, context, case_id: str) -> dict[str, Any]:
        case = self._require_support_case(context.tenant_id, case_id)
        return self._support_payload(case)

    def patch_support_case(self, context, case_id: str, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        case = self._require_support_case(context.tenant_id, case_id)
        for field_name in ("case_type", "trip_id", "rider_id", "driver_id", "payment_id", "receipt_id"):
            if field_name in payload:
                setattr(case, field_name, payload[field_name])
        case.updated_by = context.subject_id
        self._store_timeline(
            case,
            event_type="support_case_updated",
            actor_id=context.subject_id,
            request_id=request_meta["request_id"],
            trace_id=request_meta["trace_id"],
            correlation_id=request_meta["correlation_id"],
            message="Support case updated",
            payload={"patch": payload},
        )
        evidence = self._create_evidence(support_case=case, request_meta=request_meta)
        self._persist_support_evidence(evidence)
        self._persist_support_case(case)
        return self._support_payload(case)

    def assign_support_case(self, context, case_id: str, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        case = self._require_support_case(context.tenant_id, case_id)
        case.assigned_to = str(payload.get("assigned_to") or context.subject_id)
        case.status = SupportCaseState.ASSIGNED
        case.updated_by = context.subject_id
        self._store_timeline(
            case,
            event_type="support_case_assigned",
            actor_id=context.subject_id,
            request_id=request_meta["request_id"],
            trace_id=request_meta["trace_id"],
            correlation_id=request_meta["correlation_id"],
            message="Support case assigned",
            payload={"assigned_to": case.assigned_to},
        )
        evidence = self._create_evidence(support_case=case, request_meta=request_meta)
        self._persist_support_evidence(evidence)
        self._persist_support_case(case)
        return self._support_payload(case)

    def escalate_support_case(self, context, case_id: str, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        case = self._require_support_case(context.tenant_id, case_id)
        case.status = SupportCaseState.ESCALATED
        case.updated_by = context.subject_id
        self._store_timeline(
            case,
            event_type="support_case_escalated",
            actor_id=context.subject_id,
            request_id=request_meta["request_id"],
            trace_id=request_meta["trace_id"],
            correlation_id=request_meta["correlation_id"],
            message="Support case escalated",
            payload={"reason": str(payload.get("reason", ""))},
        )
        evidence = self._create_evidence(support_case=case, request_meta=request_meta)
        self._persist_support_evidence(evidence)
        self._persist_support_case(case)
        return self._support_payload(case)

    def resolve_support_case(self, context, case_id: str, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        case = self._require_support_case(context.tenant_id, case_id)
        case.status = SupportCaseState.RESOLVED
        case.updated_by = context.subject_id
        self._store_timeline(
            case,
            event_type="support_case_resolved",
            actor_id=context.subject_id,
            request_id=request_meta["request_id"],
            trace_id=request_meta["trace_id"],
            correlation_id=request_meta["correlation_id"],
            message="Support case resolved",
            payload={"resolution": str(payload.get("resolution", ""))},
        )
        evidence = self._create_evidence(support_case=case, request_meta=request_meta)
        self._persist_support_evidence(evidence)
        self._persist_support_case(case)
        return self._support_payload(case)

    def support_case_timeline(self, context, case_id: str) -> list[dict[str, Any]]:
        case = self._require_support_case(context.tenant_id, case_id)
        return [_serialise(item) for item in case.timeline]

    def support_case_evidence(
        self,
        context,
        case_id: str,
    ) -> list[dict[str, Any]]:
        case = self._require_support_case(
            context.tenant_id,
            case_id,
        )

        repository = (
            self._support_record_repository
        )

        if repository is not None:
            records = repository.list(
                tenant_id=context.tenant_id,
                record_type="support_evidence",
                region_id=case.region_id,
                limit=1000,
            )

            for durable_record in records:
                payload = dict(
                    durable_record.payload
                )

                if (
                    str(
                        payload.get(
                            "subject_type",
                            "",
                        )
                    )
                    != "support_case"
                ):
                    continue

                if (
                    str(
                        payload.get(
                            "subject_id",
                            "",
                        )
                    )
                    != case.case_id
                ):
                    continue

                evidence = (
                    self._support_evidence_from_record(
                        durable_record
                    )
                )

                self.evidence[
                    evidence.evidence_id
                ] = evidence

        return [
            self._evidence_payload(record)
            for record
            in self.evidence.values()
            if (
                record.tenant_id
                == context.tenant_id
                and record.subject_type
                == "support_case"
                and record.subject_id
                == case.case_id
            )
        ]

    def create_refund(self, context, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        amount = Decimal(str(payload.get("amount", "0")))
        currency = str(payload.get("currency", "AUD")).upper()
        if amount <= 0:
            raise ValueError("refund_amount_invalid")
        idempotency_key = str(payload.get("idempotency_key", "")).strip()
        canonical_payload = {key: value for key, value in payload.items() if key != "idempotency_key"}
        canonical_payload["amount"] = format(amount.normalize(), "f")
        canonical_payload["currency"] = currency
        payload_hash = canonical_hash(canonical_payload)
        existing = self._idempotency_record_id("refund", context.tenant_id, idempotency_key, payload_hash)
        if existing:
            refund = self._require_refund(context.tenant_id, existing)
            if refund:
                return self._refund_payload(refund)
        refund = RefundRequest(
            refund_id=new_id("refund"),
            tenant_id=context.tenant_id,
            region_id=self._region_code(context),
            amount=amount,
            currency=currency,
            payment_id=payload.get("payment_id"),
            receipt_id=payload.get("receipt_id"),
            trip_id=payload.get("trip_id"),
            support_case_id=payload.get("support_case_id"),
            approval_required=bool(amount >= Decimal("50")),
            requester_id=context.subject_id,
            idempotency_key=str(payload.get("idempotency_key", "")),
            reason=str(payload.get("reason", "")),
        )
        refund.status = RefundState.APPROVAL_PENDING if refund.approval_required else RefundState.APPROVED
        self._store_timeline(
            refund,
            event_type="refund_requested",
            actor_id=context.subject_id,
            request_id=request_meta["request_id"],
            trace_id=request_meta["trace_id"],
            correlation_id=request_meta["correlation_id"],
            message="Refund requested",
            payload={"amount": format(amount, "f"), "currency": currency},
        )
        self.refunds[refund.refund_id] = refund
        self._register_idempotency("refund", context.tenant_id, idempotency_key, record_id=refund.refund_id, payload_hash=payload_hash)
        self._create_evidence(refund=refund, request_meta=request_meta)
        return self._refund_payload(refund)

    def list_refunds(self, context, *, limit: int = 100) -> list[dict[str, Any]]:
        return [self._refund_payload(item) for item in self._all_refunds(context.tenant_id)[:limit]]

    def get_refund(self, context, refund_id: str) -> dict[str, Any]:
        refund = self._require_refund(context.tenant_id, refund_id)
        return self._refund_payload(refund)

    def evaluate_refund(self, context, refund_id: str, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        refund = self._require_refund(context.tenant_id, refund_id)
        refund.status = RefundState.EVALUATED
        refund.approval_required = bool(payload.get("approval_required", refund.approval_required))
        refund.updated_by = context.subject_id
        self._store_timeline(
            refund,
            event_type="refund_evaluated",
            actor_id=context.subject_id,
            request_id=request_meta["request_id"],
            trace_id=request_meta["trace_id"],
            correlation_id=request_meta["correlation_id"],
            message="Refund evaluated",
            payload={"approval_required": refund.approval_required},
        )
        if refund.approval_required:
            refund.status = RefundState.APPROVAL_PENDING
        else:
            refund.status = RefundState.APPROVED
        self._create_evidence(refund=refund, request_meta=request_meta)
        return self._refund_payload(refund)

    def request_refund_approval(self, context, refund_id: str, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        refund = self._require_refund(context.tenant_id, refund_id)
        if refund.requester_id == context.subject_id:
            raise AuthorityDenied("refund_self_approval_forbidden")
        refund.status = RefundState.APPROVAL_PENDING
        refund.updated_by = context.subject_id
        self._store_timeline(
            refund,
            event_type="refund_approval_requested",
            actor_id=context.subject_id,
            request_id=request_meta["request_id"],
            trace_id=request_meta["trace_id"],
            correlation_id=request_meta["correlation_id"],
            message="Refund approval requested",
            payload={"reason": str(payload.get("reason", ""))},
        )
        self._create_evidence(refund=refund, request_meta=request_meta)
        return self._refund_payload(refund)

    def approve_refund(self, context, refund_id: str, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        refund = self._require_refund(context.tenant_id, refund_id)
        if refund.requester_id == context.subject_id:
            raise AuthorityDenied("refund_self_approval_forbidden")
        refund.approver_id = context.subject_id
        refund.status = RefundState.APPROVED
        self._store_timeline(
            refund,
            event_type="refund_approved",
            actor_id=context.subject_id,
            request_id=request_meta["request_id"],
            trace_id=request_meta["trace_id"],
            correlation_id=request_meta["correlation_id"],
            message="Refund approved",
            payload={"approval_reference": str(payload.get("approval_reference", ""))},
        )
        self._create_evidence(refund=refund, request_meta=request_meta)
        return self._refund_payload(refund)

    def reject_refund(self, context, refund_id: str, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        refund = self._require_refund(context.tenant_id, refund_id)
        refund.status = RefundState.REJECTED
        refund.updated_by = context.subject_id
        self._store_timeline(
            refund,
            event_type="refund_rejected",
            actor_id=context.subject_id,
            request_id=request_meta["request_id"],
            trace_id=request_meta["trace_id"],
            correlation_id=request_meta["correlation_id"],
            message="Refund rejected",
            payload={"reason": str(payload.get("reason", ""))},
        )
        self._create_evidence(refund=refund, request_meta=request_meta)
        return self._refund_payload(refund)

    def execute_refund(self, context, refund_id: str, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        refund = self._require_refund(context.tenant_id, refund_id)
        if refund.status != RefundState.APPROVED:
            raise ValueError("refund_not_approved")
        refund.status = RefundState.EXECUTING
        refund.verified_by = context.subject_id
        self._store_timeline(
            refund,
            event_type="refund_executing",
            actor_id=context.subject_id,
            request_id=request_meta["request_id"],
            trace_id=request_meta["trace_id"],
            correlation_id=request_meta["correlation_id"],
            message="Refund executing",
            payload={"provider_reference": str(payload.get("provider_reference", ""))},
        )
        refund.status = RefundState.VERIFIED
        refund.status = RefundState.COMPLETED
        self._create_evidence(refund=refund, request_meta=request_meta)
        return self._refund_payload(refund)

    def refund_evidence(self, context, refund_id: str) -> list[dict[str, Any]]:
        refund = self._require_refund(context.tenant_id, refund_id)
        return [self._evidence_payload(record) for record in self.evidence.values() if record.subject_type == "refund" and record.subject_id == refund.refund_id]

    def list_payment_investigations(self, context, *, limit: int = 100) -> list[dict[str, Any]]:
        return [self._investigation_payload(item) for item in self._all_investigations(context.tenant_id)[:limit]]

    def get_payment_investigation(self, context, investigation_id: str) -> dict[str, Any]:
        investigation = self._require_investigation(context.tenant_id, investigation_id)
        return self._investigation_payload(investigation)

    def create_payment_investigation(self, context, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        idempotency_key = str(payload.pop("idempotency_key", "")).strip()
        payload_hash = canonical_hash(payload)
        existing = self._idempotency_record_id("investigation", context.tenant_id, idempotency_key, payload_hash)
        if existing:
            investigation = self._require_investigation(context.tenant_id, existing)
            if investigation:
                return self._investigation_payload(investigation)
        investigation = PaymentInvestigation(
            investigation_id=new_id("investigation"),
            tenant_id=context.tenant_id,
            region_id=self._region_code(context),
            payment_id=str(payload.get("payment_id", "")),
            reason=str(payload.get("reason", "")),
            created_by=context.subject_id,
        )
        investigation.timeline.append(
            _timeline_entry(
                event_type="payment_investigation_created",
                actor_id=context.subject_id,
                request_id=request_meta["request_id"],
                trace_id=request_meta["trace_id"],
                correlation_id=request_meta["correlation_id"],
                message="Payment investigation opened",
                payload={"payment_id": investigation.payment_id},
            )
        )
        self.investigations[investigation.investigation_id] = investigation
        self._register_idempotency("investigation", context.tenant_id, idempotency_key, record_id=investigation.investigation_id, payload_hash=payload_hash)
        self._create_evidence(investigation=investigation, request_meta=request_meta)
        return self._investigation_payload(investigation)

    def list_disputes(self, context, *, limit: int = 100) -> list[dict[str, Any]]:
        return [self._dispute_payload(item) for item in self._all_disputes(context.tenant_id)[:limit]]

    def get_dispute(self, context, dispute_id: str) -> dict[str, Any]:
        dispute = self._require_dispute(context.tenant_id, dispute_id)
        return self._dispute_payload(dispute)

    def assign_dispute(self, context, dispute_id: str, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        dispute = self._require_dispute(context.tenant_id, dispute_id)
        dispute.reviewer_id = str(payload.get("assigned_to") or context.subject_id)
        dispute.status = DisputeState.ASSIGNED
        dispute.updated_by = context.subject_id
        self._store_timeline(
            dispute,
            event_type="dispute_assigned",
            actor_id=context.subject_id,
            request_id=request_meta["request_id"],
            trace_id=request_meta["trace_id"],
            correlation_id=request_meta["correlation_id"],
            message="Dispute assigned",
            payload={"assigned_to": dispute.reviewer_id},
        )
        self._create_evidence(dispute=dispute, request_meta=request_meta)
        return self._dispute_payload(dispute)

    def request_dispute_evidence(self, context, dispute_id: str, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        dispute = self._require_dispute(context.tenant_id, dispute_id)
        dispute.status = DisputeState.REQUEST_EVIDENCE
        self._store_timeline(
            dispute,
            event_type="dispute_evidence_requested",
            actor_id=context.subject_id,
            request_id=request_meta["request_id"],
            trace_id=request_meta["trace_id"],
            correlation_id=request_meta["correlation_id"],
            message="Evidence requested for dispute",
            payload={"reason": str(payload.get("reason", ""))},
        )
        self._create_evidence(dispute=dispute, request_meta=request_meta)
        return self._dispute_payload(dispute)

    def decide_dispute(self, context, dispute_id: str, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        dispute = self._require_dispute(context.tenant_id, dispute_id)
        dispute.status = DisputeState.DECIDED
        dispute.reviewer_id = context.subject_id
        dispute.updated_by = context.subject_id
        dispute.timeline.append(
            _timeline_entry(
                event_type="dispute_decided",
                actor_id=context.subject_id,
                request_id=request_meta["request_id"],
                trace_id=request_meta["trace_id"],
                correlation_id=request_meta["correlation_id"],
                message="Dispute decided",
                payload={"decision": str(payload.get("decision", "")), "policy_version": dispute.policy_version},
            )
        )
        self._create_evidence(dispute=dispute, request_meta=request_meta)
        return self._dispute_payload(dispute)

    def appeal_dispute(self, context, dispute_id: str, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        dispute = self._require_dispute(context.tenant_id, dispute_id)
        dispute.status = DisputeState.APPEALED
        dispute.appeal_state = "requested"
        dispute.timeline.append(
            _timeline_entry(
                event_type="dispute_appealed",
                actor_id=context.subject_id,
                request_id=request_meta["request_id"],
                trace_id=request_meta["trace_id"],
                correlation_id=request_meta["correlation_id"],
                message="Dispute appealed",
                payload={"reason": str(payload.get("reason", ""))},
            )
        )
        self._create_evidence(dispute=dispute, request_meta=request_meta)
        return self._dispute_payload(dispute)

    def dispute_evidence(self, context, dispute_id: str) -> list[dict[str, Any]]:
        dispute = self._require_dispute(context.tenant_id, dispute_id)
        return [self._evidence_payload(record) for record in self.evidence.values() if record.subject_type == "dispute" and record.subject_id == dispute.dispute_id]

    def list_actions(self, context, *, limit: int = 100) -> list[dict[str, Any]]:
        return [self._action_payload(item) for item in self._all_actions(context.tenant_id)[:limit]]

    def get_action(self, context, action_id: str) -> dict[str, Any]:
        action = self._require_action(context.tenant_id, action_id)
        return self._action_payload(action)

    def create_action(self, context, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        idempotency_key = str(payload.pop("idempotency_key", "")).strip()
        payload_hash = canonical_hash(payload)
        existing = self._idempotency_record_id("action", context.tenant_id, idempotency_key, payload_hash)
        if existing:
            action = self._require_action(context.tenant_id, existing)
            if action:
                return self._action_payload(action)
        action_type = str(payload.get("action_type", "manual_dispatch"))
        target_id = str(payload.get("target_id", ""))
        if action_type not in {
            "manual_dispatch",
            "reassign_driver",
            "cancel_trip",
            "pause_dispatch_region",
            "resume_dispatch_region",
            "suppress_surge",
            "restore_surge",
            "enable_maintenance_mode",
            "disable_maintenance_mode",
            "request_service_restart",
            "request_deployment_rollback",
            "preserve_trip_evidence",
            "freeze_driver_account",
            "freeze_rider_account",
            "update_pricing_policy",
            "send_governed_notification",
            "record_shift_handover",
        }:
            raise ValueError("action_type_not_allowed")
        action = OperationalAction(
            action_id=new_id("action"),
            tenant_id=context.tenant_id,
            region_id=self._region_code(context),
            action_type=action_type,
            target_id=target_id,
            requested_by=context.subject_id,
            reason=str(payload.get("reason", "")),
            approval_reference=payload.get("approval_reference"),
            approval_required=bool(payload.get("approval_required", True)),
            risk_level=str(payload.get("risk_level", "medium")),
        )
        self._store_timeline(
            action,
            event_type="action_requested",
            actor_id=context.subject_id,
            request_id=request_meta["request_id"],
            trace_id=request_meta["trace_id"],
            correlation_id=request_meta["correlation_id"],
            message="Operational action requested",
            payload={"action_type": action.action_type, "target_id": target_id},
        )
        self.actions[action.action_id] = action
        self._register_idempotency("action", context.tenant_id, idempotency_key, record_id=action.action_id, payload_hash=payload_hash)
        self._create_evidence(action=action, request_meta=request_meta)
        return self._action_payload(action)

    def evaluate_action(self, context, action_id: str, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        action = self._require_action(context.tenant_id, action_id)
        action.status = OperationalActionState.EVALUATED
        if action.approval_required:
            action.status = OperationalActionState.APPROVAL_PENDING
        action.timeline.append(
            _timeline_entry(
                event_type="action_evaluated",
                actor_id=context.subject_id,
                request_id=request_meta["request_id"],
                trace_id=request_meta["trace_id"],
                correlation_id=request_meta["correlation_id"],
                message="Operational action evaluated",
                payload={"risk": str(payload.get("risk_level", action.risk_level))},
            )
        )
        self._create_evidence(action=action, request_meta=request_meta)
        return self._action_payload(action)

    def approve_action(self, context, action_id: str, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        action = self._require_action(context.tenant_id, action_id)
        if action.requested_by == context.subject_id:
            raise AuthorityDenied("self_approval_forbidden")
        action.approved_by = context.subject_id
        action.status = OperationalActionState.APPROVED
        action.approval_reference = str(payload.get("approval_reference") or action.approval_reference or "")
        self._store_timeline(
            action,
            event_type="action_approved",
            actor_id=context.subject_id,
            request_id=request_meta["request_id"],
            trace_id=request_meta["trace_id"],
            correlation_id=request_meta["correlation_id"],
            message="Operational action approved",
            payload={"approval_reference": action.approval_reference},
        )
        self._create_evidence(action=action, request_meta=request_meta)
        return self._action_payload(action)

    def reject_action(self, context, action_id: str, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        action = self._require_action(context.tenant_id, action_id)
        action.status = OperationalActionState.REJECTED
        self._store_timeline(
            action,
            event_type="action_rejected",
            actor_id=context.subject_id,
            request_id=request_meta["request_id"],
            trace_id=request_meta["trace_id"],
            correlation_id=request_meta["correlation_id"],
            message="Operational action rejected",
            payload={"reason": str(payload.get("reason", ""))},
        )
        self._create_evidence(action=action, request_meta=request_meta)
        return self._action_payload(action)

    def execute_action(self, context, action_id: str, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        action = self._require_action(context.tenant_id, action_id)
        if action.status not in {OperationalActionState.APPROVED, OperationalActionState.EVALUATED, OperationalActionState.APPROVAL_PENDING}:
            raise ValueError("action_not_approved")
        action.status = OperationalActionState.EXECUTING
        action.executed_by = context.subject_id
        action.timeline.append(
            _timeline_entry(
                event_type="action_executed",
                actor_id=context.subject_id,
                request_id=request_meta["request_id"],
                trace_id=request_meta["trace_id"],
                correlation_id=request_meta["correlation_id"],
                message="Operational action executed",
                payload={"adapter": str(payload.get("adapter", "allowlisted_adapter"))},
            )
        )
        self._create_evidence(action=action, request_meta=request_meta)
        return self._action_payload(action)

    def verify_action(self, context, action_id: str, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        action = self._require_action(context.tenant_id, action_id)
        action.status = OperationalActionState.VERIFIED
        action.verified_by = context.subject_id
        action.timeline.append(
            _timeline_entry(
                event_type="action_verified",
                actor_id=context.subject_id,
                request_id=request_meta["request_id"],
                trace_id=request_meta["trace_id"],
                correlation_id=request_meta["correlation_id"],
                message="Operational action verified",
                payload={"result": str(payload.get("result", "verified"))},
            )
        )
        self._create_evidence(action=action, request_meta=request_meta)
        return self._action_payload(action)

    def cancel_action(self, context, action_id: str, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        action = self._require_action(context.tenant_id, action_id)
        action.status = OperationalActionState.CANCELLED
        action.timeline.append(
            _timeline_entry(
                event_type="action_cancelled",
                actor_id=context.subject_id,
                request_id=request_meta["request_id"],
                trace_id=request_meta["trace_id"],
                correlation_id=request_meta["correlation_id"],
                message="Operational action cancelled",
                payload={"reason": str(payload.get("reason", ""))},
            )
        )
        self._create_evidence(action=action, request_meta=request_meta)
        return self._action_payload(action)

    def action_evidence(self, context, action_id: str) -> list[dict[str, Any]]:
        action = self._require_action(context.tenant_id, action_id)
        return [self._evidence_payload(record) for record in self.evidence.values() if record.subject_type == "action" and record.subject_id == action.action_id]

    def list_evidence(self, context, *, limit: int = 100) -> list[dict[str, Any]]:
        items = [self._evidence_payload(item) for item in list(self.evidence.values()) if item.tenant_id == context.tenant_id]
        return items[:limit]

    def get_evidence(self, context, evidence_id: str) -> dict[str, Any]:
        record = self.evidence.get(evidence_id)
        if record is None or record.tenant_id != context.tenant_id:
            raise KeyError("evidence_not_found")
        return self._evidence_payload(record)

    def trip_evidence(self, context, trip_id: str) -> list[dict[str, Any]]:
        return [self._evidence_payload(record) for record in self.evidence.values() if record.subject_type == "trip" and record.subject_id == trip_id and record.tenant_id == context.tenant_id]

    def case_evidence(self, context, case_id: str) -> list[dict[str, Any]]:
        return [self._evidence_payload(record) for record in self.evidence.values() if record.subject_id == case_id and record.tenant_id == context.tenant_id]

    def _create_evidence(self, *, request_meta: dict[str, str], incident: OperationalIncident | None = None, safety_case: SafetyCase | None = None, support_case: SupportCase | None = None, refund: RefundRequest | None = None, investigation: PaymentInvestigation | None = None, dispute: DisputeRecord | None = None, action: OperationalAction | None = None) -> EvidenceRecord:
        if incident is not None:
            return self._evidence_record(
                tenant_id=incident.tenant_id,
                region_id=incident.region_id,
                actor_id=incident.updated_by or incident.created_by,
                subject_type="incident",
                subject_id=incident.incident_id,
                source_records=[incident.incident_id],
                timeline=list(incident.timeline),
                correlation_id=request_meta["correlation_id"],
            )
        if safety_case is not None:
            return self._evidence_record(
                tenant_id=safety_case.tenant_id,
                region_id=safety_case.region_id,
                actor_id=safety_case.updated_by or safety_case.created_by,
                subject_type="safety_case",
                subject_id=safety_case.case_id,
                source_records=[safety_case.case_id],
                timeline=list(safety_case.timeline),
                correlation_id=request_meta["correlation_id"],
            )
        if support_case is not None:
            return self._evidence_record(
                tenant_id=support_case.tenant_id,
                region_id=support_case.region_id,
                actor_id=support_case.updated_by or support_case.created_by,
                subject_type="support_case",
                subject_id=support_case.case_id,
                source_records=[support_case.case_id],
                timeline=list(support_case.timeline),
                correlation_id=request_meta["correlation_id"],
            )
        if refund is not None:
            return self._evidence_record(
                tenant_id=refund.tenant_id,
                region_id=refund.region_id,
                actor_id=refund.requester_id,
                subject_type="refund",
                subject_id=refund.refund_id,
                source_records=[refund.refund_id, refund.payment_id or "", refund.support_case_id or ""],
                timeline=list(refund.timeline),
                correlation_id=request_meta["correlation_id"],
            )
        if investigation is not None:
            return self._evidence_record(
                tenant_id=investigation.tenant_id,
                region_id=investigation.region_id,
                actor_id=investigation.created_by,
                subject_type="payment_investigation",
                subject_id=investigation.investigation_id,
                source_records=[investigation.investigation_id, investigation.payment_id],
                timeline=list(investigation.timeline),
                correlation_id=request_meta["correlation_id"],
            )
        if dispute is not None:
            return self._evidence_record(
                tenant_id=dispute.tenant_id,
                region_id=dispute.region_id,
                actor_id=dispute.updated_by or dispute.created_by,
                subject_type="dispute",
                subject_id=dispute.dispute_id,
                source_records=[dispute.dispute_id],
                timeline=list(dispute.timeline),
                correlation_id=request_meta["correlation_id"],
            )
        if action is not None:
            return self._evidence_record(
                tenant_id=action.tenant_id,
                region_id=action.region_id,
                actor_id=action.executed_by or action.requested_by,
                subject_type="action",
                subject_id=action.action_id,
                source_records=[action.action_id, action.target_id],
                timeline=list(action.timeline),
                correlation_id=request_meta["correlation_id"],
            )
        raise ValueError("evidence_subject_missing")

    def _get_incident(self, tenant_id: str, incident_id: str) -> OperationalIncident | None:
        item = self.incidents.get(incident_id)
        if item is not None and item.tenant_id == tenant_id:
            return item
        return None

    def _require_incident(self, tenant_id: str, incident_id: str) -> OperationalIncident:
        incident = self._get_incident(tenant_id, incident_id)
        if incident is None:
            raise KeyError("incident_not_found")
        return incident

    def _get_safety_case(self, tenant_id: str, case_id: str) -> SafetyCase | None:
        item = self.safety_cases.get(case_id)
        if item is not None and item.tenant_id == tenant_id:
            return item
        return None

    def _require_safety_case(self, tenant_id: str, case_id: str) -> SafetyCase:
        case = self._get_safety_case(tenant_id, case_id)
        if case is None:
            raise KeyError("safety_case_not_found")
        return case

    def _persist_support_evidence(
        self,
        evidence: EvidenceRecord,
    ) -> None:
        repository = (
            self._support_record_repository
        )

        if repository is None:
            return

        repository.save_values(
            record_id=evidence.evidence_id,
            tenant_id=evidence.tenant_id,
            region_id=evidence.region_id,
            record_type="support_evidence",
            record_key=evidence.evidence_id,
            state=evidence.verification_status,
            payload=_serialise(
                asdict(evidence)
            ),
            created_at=evidence.created_at,
            updated_at=evidence.created_at,
        )

    def _support_evidence_from_record(
        self,
        record: Any,
    ) -> EvidenceRecord:
        payload = dict(
            record.payload
        )

        timeline = [
            TimelineEntry(
                id=str(
                    item["id"]
                ),
                event_type=str(
                    item["event_type"]
                ),
                occurred_at=datetime.fromisoformat(
                    str(
                        item["occurred_at"]
                    )
                ),
                actor_id=str(
                    item["actor_id"]
                ),
                request_id=str(
                    item["request_id"]
                ),
                trace_id=str(
                    item["trace_id"]
                ),
                correlation_id=str(
                    item["correlation_id"]
                ),
                message=str(
                    item["message"]
                ),
                payload=dict(
                    item.get(
                        "payload"
                    )
                    or {}
                ),
            )
            for item
            in payload.get(
                "timeline",
                [],
            )
        ]

        return EvidenceRecord(
            evidence_id=str(
                payload["evidence_id"]
            ),
            evidence_type=str(
                payload["evidence_type"]
            ),
            subject_type=str(
                payload["subject_type"]
            ),
            subject_id=str(
                payload["subject_id"]
            ),
            tenant_id=str(
                payload["tenant_id"]
            ),
            region_id=str(
                payload["region_id"]
            ),
            actor_id=str(
                payload["actor_id"]
            ),
            correlation_id=str(
                payload["correlation_id"]
            ),
            integrity_status=str(
                payload["integrity_status"]
            ),
            created_at=datetime.fromisoformat(
                str(
                    payload["created_at"]
                )
            ),
            source_records=[
                str(value)
                for value
                in payload.get(
                    "source_records",
                    [],
                )
            ],
            timeline=timeline,
            verification_status=str(
                payload.get(
                    "verification_status",
                    "pending",
                )
            ),
            redacted=bool(
                payload.get(
                    "redacted",
                    True,
                )
            ),
        )

    def _support_idempotency_record_id(
        self,
        operation: str,
        tenant_id: str,
        key: str,
        payload_hash: str,
    ) -> str | None:
        existing = self._idempotency_record_id(
            operation,
            tenant_id,
            key,
            payload_hash,
        )

        if existing is not None or not key:
            return existing

        repository = (
            self._support_record_repository
        )

        if repository is None:
            return None

        record = repository.get(
            tenant_id=tenant_id,
            record_type="support_idempotency",
            record_key=f"{operation}:{key}",
        )

        if record is None:
            return None

        payload = dict(
            record.payload
        )

        durable_hash = str(
            payload.get(
                "payload_hash",
                "",
            )
        )

        if durable_hash != payload_hash:
            raise ValueError(
                "idempotency_conflict"
            )

        record_id = str(
            payload.get(
                "record_id",
                "",
            )
        )

        self._idempotency_index[
            (
                operation,
                tenant_id,
                key,
            )
        ] = {
            "record_id": record_id,
            "payload_hash": durable_hash,
        }

        return record_id or None

    def _persist_support_idempotency(
        self,
        *,
        case: SupportCase,
        operation: str,
        key: str,
        payload_hash: str,
    ) -> None:
        if not key:
            return

        repository = (
            self._support_record_repository
        )

        if repository is None:
            return

        repository.save_values(
            record_id=(
                f"idempotency:"
                f"{operation}:"
                f"{case.case_id}"
            ),
            tenant_id=case.tenant_id,
            region_id=case.region_id,
            record_type="support_idempotency",
            record_key=f"{operation}:{key}",
            state="registered",
            payload={
                "operation": operation,
                "key": key,
                "record_id": case.case_id,
                "payload_hash": payload_hash,
            },
            created_at=case.created_at,
            updated_at=case.updated_at,
        )

    def _persist_support_case(
        self,
        case: SupportCase,
    ) -> None:
        repository = (
            self._support_record_repository
        )

        if repository is None:
            return

        repository.save_values(
            record_id=case.case_id,
            tenant_id=case.tenant_id,
            region_id=case.region_id,
            record_type="support_case",
            record_key=case.case_id,
            state=case.status.value,
            payload=_serialise(
                asdict(case)
            ),
            created_at=case.created_at,
            updated_at=case.updated_at,
        )

    def _support_case_from_record(
        self,
        record: Any,
    ) -> SupportCase:
        payload = dict(
            record.payload
        )

        timeline = [
            TimelineEntry(
                id=str(
                    item["id"]
                ),
                event_type=str(
                    item["event_type"]
                ),
                occurred_at=datetime.fromisoformat(
                    str(
                        item["occurred_at"]
                    )
                ),
                actor_id=str(
                    item["actor_id"]
                ),
                request_id=str(
                    item["request_id"]
                ),
                trace_id=str(
                    item["trace_id"]
                ),
                correlation_id=str(
                    item["correlation_id"]
                ),
                message=str(
                    item["message"]
                ),
                payload=dict(
                    item.get(
                        "payload"
                    )
                    or {}
                ),
            )
            for item
            in payload.get(
                "timeline",
                [],
            )
        ]

        return SupportCase(
            case_id=str(
                payload["case_id"]
            ),
            tenant_id=str(
                payload["tenant_id"]
            ),
            region_id=str(
                payload["region_id"]
            ),
            case_type=str(
                payload["case_type"]
            ),
            status=SupportCaseState(
                str(
                    payload["status"]
                )
            ),
            trip_id=payload.get(
                "trip_id"
            ),
            rider_id=payload.get(
                "rider_id"
            ),
            driver_id=payload.get(
                "driver_id"
            ),
            payment_id=payload.get(
                "payment_id"
            ),
            receipt_id=payload.get(
                "receipt_id"
            ),
            phone=payload.get(
                "phone"
            ),
            email=payload.get(
                "email"
            ),
            assigned_to=payload.get(
                "assigned_to"
            ),
            created_by=str(
                payload.get(
                    "created_by",
                    "",
                )
            ),
            updated_by=str(
                payload.get(
                    "updated_by",
                    "",
                )
            ),
            request_id=str(
                payload.get(
                    "request_id",
                    "",
                )
            ),
            trace_id=str(
                payload.get(
                    "trace_id",
                    "",
                )
            ),
            correlation_id=str(
                payload.get(
                    "correlation_id",
                    "",
                )
            ),
            created_at=datetime.fromisoformat(
                str(
                    payload[
                        "created_at"
                    ]
                )
            ),
            updated_at=datetime.fromisoformat(
                str(
                    payload[
                        "updated_at"
                    ]
                )
            ),
            timeline=timeline,
            evidence_refs=[
                str(value)
                for value
                in payload.get(
                    "evidence_refs",
                    [],
                )
            ],
        )

    def _get_support_case(
        self,
        tenant_id: str,
        case_id: str,
    ) -> SupportCase | None:
        item = self.support_cases.get(
            case_id
        )

        if (
            item is not None
            and item.tenant_id == tenant_id
        ):
            return item

        repository = (
            self._support_record_repository
        )

        if repository is None:
            return None

        record = repository.get(
            tenant_id=tenant_id,
            record_type="support_case",
            record_key=case_id,
        )

        if record is None:
            return None

        case = (
            self._support_case_from_record(
                record
            )
        )

        self.support_cases[
            case.case_id
        ] = case

        return case

    def _require_support_case(self, tenant_id: str, case_id: str) -> SupportCase:
        case = self._get_support_case(tenant_id, case_id)
        if case is None:
            raise KeyError("support_case_not_found")
        return case

    def _get_refund(self, tenant_id: str, refund_id: str) -> RefundRequest | None:
        item = self.refunds.get(refund_id)
        if item is not None and item.tenant_id == tenant_id:
            return item
        return None

    def _require_refund(self, tenant_id: str, refund_id: str) -> RefundRequest:
        refund = self._get_refund(tenant_id, refund_id)
        if refund is None:
            raise KeyError("refund_not_found")
        return refund

    def _get_investigation(self, tenant_id: str, investigation_id: str) -> PaymentInvestigation | None:
        item = self.investigations.get(investigation_id)
        if item is not None and item.tenant_id == tenant_id:
            return item
        return None

    def _require_investigation(self, tenant_id: str, investigation_id: str) -> PaymentInvestigation:
        investigation = self._get_investigation(tenant_id, investigation_id)
        if investigation is None:
            raise KeyError("payment_investigation_not_found")
        return investigation

    def _get_dispute(self, tenant_id: str, dispute_id: str) -> DisputeRecord | None:
        item = self.disputes.get(dispute_id)
        if item is not None and item.tenant_id == tenant_id:
            return item
        return None

    def _require_dispute(self, tenant_id: str, dispute_id: str) -> DisputeRecord:
        dispute = self._get_dispute(tenant_id, dispute_id)
        if dispute is None:
            raise KeyError("dispute_not_found")
        return dispute

    def _get_action(self, tenant_id: str, action_id: str) -> OperationalAction | None:
        item = self.actions.get(action_id)
        if item is not None and item.tenant_id == tenant_id:
            return item
        return None

    def _require_action(self, tenant_id: str, action_id: str) -> OperationalAction:
        action = self._get_action(tenant_id, action_id)
        if action is None:
            raise KeyError("action_not_found")
        return action

    def _incident_payload(self, incident: OperationalIncident) -> dict[str, Any]:
        return _serialise(
            {
                **asdict(incident),
                "current_state": incident.status.value,
                "evidence_count": len([record for record in self.evidence.values() if record.subject_type == "incident" and record.subject_id == incident.incident_id]),
            }
        )

    def _safety_payload(self, case: SafetyCase) -> dict[str, Any]:
        return _serialise(
            {
                **asdict(case),
                "current_state": case.status.value,
                "evidence_count": len([record for record in self.evidence.values() if record.subject_type == "safety_case" and record.subject_id == case.case_id]),
            }
        )

    def _support_payload(self, case: SupportCase) -> dict[str, Any]:
        return _serialise(
            {
                **asdict(case),
                "current_state": case.status.value,
                "evidence_count": len([record for record in self.evidence.values() if record.subject_type == "support_case" and record.subject_id == case.case_id]),
            }
        )

    def _refund_payload(self, refund: RefundRequest) -> dict[str, Any]:
        return _serialise(
            {
                **asdict(refund),
                "current_state": refund.status.value,
                "amount": format(refund.amount, "f"),
                "evidence_count": len([record for record in self.evidence.values() if record.subject_type == "refund" and record.subject_id == refund.refund_id]),
            }
        )

    def _investigation_payload(self, investigation: PaymentInvestigation) -> dict[str, Any]:
        return _serialise(
            {
                **asdict(investigation),
                "current_state": investigation.status.value,
                "evidence_count": len([record for record in self.evidence.values() if record.subject_type == "payment_investigation" and record.subject_id == investigation.investigation_id]),
            }
        )

    def _dispute_payload(self, dispute: DisputeRecord) -> dict[str, Any]:
        return _serialise(
            {
                **asdict(dispute),
                "current_state": dispute.status.value,
                "evidence_count": len([record for record in self.evidence.values() if record.subject_type == "dispute" and record.subject_id == dispute.dispute_id]),
            }
        )

    def _action_payload(self, action: OperationalAction) -> dict[str, Any]:
        return _serialise(
            {
                **asdict(action),
                "current_state": action.status.value,
                "evidence_count": len([record for record in self.evidence.values() if record.subject_type == "action" and record.subject_id == action.action_id]),
            }
        )

    def _evidence_payload(self, record: EvidenceRecord) -> dict[str, Any]:
        return _serialise(
            {
                **asdict(record),
                "current_state": record.verification_status,
                "timeline": [asdict(item) for item in record.timeline],
                "source_records": [item for item in record.source_records if item],
            }
        )

    def _all_incidents(self, tenant_id: str) -> list[OperationalIncident]:
        items = [incident for incident in self.incidents.values() if incident.tenant_id == tenant_id]
        for incident in self.runtime.repositories.incidents.list(tenant_id=tenant_id):
            derived = OperationalIncident(
                incident_id=incident.id,
                tenant_id=incident.tenant_id,
                region_id=incident.region_code,
                title=incident.category,
                severity=incident.severity,
                status=IncidentState(incident.state.value.lower()) if incident.state.value.lower() in IncidentState._value2member_map_ else IncidentState.DETECTED,
                description=incident.category,
                created_by=incident.id,
                updated_by=incident.id,
            )
            if all(existing.incident_id != derived.incident_id for existing in items):
                items.append(derived)
        return sorted(items, key=lambda item: item.updated_at, reverse=True)

    def _all_safety_cases(self, tenant_id: str) -> list[SafetyCase]:
        items = [case for case in self.safety_cases.values() if case.tenant_id == tenant_id]
        for emergency in self.runtime.repositories.emergencies.list(tenant_id=tenant_id):
            status = {
                EmergencyState.TRIGGERED: SafetyCaseState.NEW,
                EmergencyState.ACKNOWLEDGED: SafetyCaseState.TRIAGED,
                EmergencyState.TRIAGED: SafetyCaseState.ASSIGNED,
                EmergencyState.RESPONDING: SafetyCaseState.RESPONDING,
                EmergencyState.ESCALATED: SafetyCaseState.ESCALATED,
                EmergencyState.STABILIZED: SafetyCaseState.MONITORING,
                EmergencyState.RESOLVED: SafetyCaseState.RESOLVED,
                EmergencyState.REVIEW_REQUIRED: SafetyCaseState.TRIAGED,
                EmergencyState.CLOSED: SafetyCaseState.CLOSED,
            }.get(emergency.state, SafetyCaseState.NEW)
            derived = SafetyCase(
                case_id=emergency.id,
                tenant_id=emergency.tenant_id,
                region_id=emergency.region_code,
                status=status,
                severity="SEV1" if emergency.state in {EmergencyState.TRIGGERED, EmergencyState.ESCALATED} else "SEV3",
                linked_trip_id=emergency.trip_id,
                created_by=emergency.source_id,
                updated_by=emergency.source_id,
                incident_id=emergency.id,
            )
            if all(existing.case_id != derived.case_id for existing in items):
                items.append(derived)
        return sorted(items, key=lambda item: item.updated_at, reverse=True)

    def _all_support_cases(
        self,
        tenant_id: str,
    ) -> list[SupportCase]:
        repository = (
            self._support_record_repository
        )

        if repository is not None:
            for record in repository.list(
                tenant_id=tenant_id,
                record_type="support_case",
            ):
                case = (
                    self._support_case_from_record(
                        record
                    )
                )

                self.support_cases[
                    case.case_id
                ] = case

        return sorted(
            [
                case
                for case
                in self.support_cases.values()
                if case.tenant_id == tenant_id
            ],
            key=lambda item: item.updated_at,
            reverse=True,
        )

    def _all_refunds(self, tenant_id: str) -> list[RefundRequest]:
        return sorted([refund for refund in self.refunds.values() if refund.tenant_id == tenant_id], key=lambda item: item.updated_at, reverse=True)

    def _all_investigations(self, tenant_id: str) -> list[PaymentInvestigation]:
        return sorted([investigation for investigation in self.investigations.values() if investigation.tenant_id == tenant_id], key=lambda item: item.updated_at, reverse=True)

    def _all_disputes(self, tenant_id: str) -> list[DisputeRecord]:
        return sorted([dispute for dispute in self.disputes.values() if dispute.tenant_id == tenant_id], key=lambda item: item.updated_at, reverse=True)

    def _all_actions(self, tenant_id: str) -> list[OperationalAction]:
        return sorted([action for action in self.actions.values() if action.tenant_id == tenant_id], key=lambda item: item.updated_at, reverse=True)

    def _recent_activity(self, tenant_id: str, *, limit: int) -> list[dict[str, Any]]:
        timeline: list[dict[str, Any]] = []
        for collection in (
            self._all_incidents(tenant_id),
            self._all_safety_cases(tenant_id),
            self._all_support_cases(tenant_id),
            self._all_refunds(tenant_id),
            self._all_actions(tenant_id),
        ):
            for item in collection:
                for entry in item.timeline[-3:]:
                    timeline.append(
                        {
                            "subject_id": getattr(item, "incident_id", None)
                            or getattr(item, "case_id", None)
                            or getattr(item, "refund_id", None)
                            or getattr(item, "action_id", None),
                            "event_type": entry.event_type,
                            "occurred_at": entry.occurred_at.isoformat(),
                            "actor_id": entry.actor_id,
                            "message": entry.message,
                        }
                    )
        timeline.sort(key=lambda item: item["occurred_at"], reverse=True)
        return timeline[:limit]

    def _alerts(self, tenant_id: str) -> list[dict[str, Any]]:
        alerts = []
        for incident in self._all_incidents(tenant_id):
            if incident.severity in {"SEV0", "SEV1"} and incident.status not in {IncidentState.RESOLVED, IncidentState.CLOSED, IncidentState.CANCELLED}:
                alerts.append(
                    {
                        "type": "incident",
                        "severity": incident.severity,
                        "message": incident.title,
                        "subject_id": incident.incident_id,
                    }
                )
        if not self.runtime.resilience.status()["core_journey_preserved_under_degradation"]:
            alerts.append(
                {
                    "type": "runtime",
                    "severity": "warning",
                    "message": "Runtime resilience is degraded",
                    "subject_id": "runtime",
                }
            )
        return alerts

    def _latest_trip_location(self, trip_id: str) -> dict[str, Any] | None:
        events = [event for event in self.runtime.repositories.events.by_aggregate(trip_id) if event.event_type == "TripLocationUpdated"]
        if not events:
            return None
        latest = events[-1]
        payload = latest.payload if isinstance(latest.payload, dict) else {}
        point = payload.get("point") or payload
        return {
            "current_location": point,
            "heading": point.get("heading") if isinstance(point, dict) else None,
            "speed": point.get("speed") if isinstance(point, dict) else None,
            "last_location_at": latest.occurred_at.isoformat(),
        }

    def _incident_status_for_trip(self, tenant_id: str, trip_id: str) -> str:
        for incident in self._all_incidents(tenant_id):
            if trip_id in incident.affected_trips:
                return incident.status.value
        return "none"

    def _safety_status_for_trip(self, tenant_id: str, trip_id: str) -> str:
        for case in self._all_safety_cases(tenant_id):
            if case.linked_trip_id == trip_id:
                return case.status.value
        return "none"

    def _support_match(self, case: SupportCase, query: dict[str, Any], context) -> bool:
        text = " ".join(str(value).lower() for value in query.values() if value)
        if not text:
            return True
        haystack = " ".join(
            [
                case.case_id,
                case.case_type,
                case.trip_id or "",
                case.rider_id or "",
                case.driver_id or "",
                case.payment_id or "",
                case.receipt_id or "",
                case.phone or "",
                case.email or "",
            ]
        ).lower()
        return all(token in haystack for token in text.split())

    def create_dispute(self, context, payload: dict[str, Any], request_meta: dict[str, str]) -> dict[str, Any]:
        idempotency_key = str(payload.pop("idempotency_key", "")).strip()
        payload_hash = canonical_hash(payload)
        existing = self._idempotency_record_id("dispute", context.tenant_id, idempotency_key, payload_hash)
        if existing:
            dispute = self._require_dispute(context.tenant_id, existing)
            if dispute:
                return self._dispute_payload(dispute)
        dispute = DisputeRecord(
            dispute_id=new_id("dispute"),
            tenant_id=context.tenant_id,
            region_id=self._region_code(context),
            trip_id=payload.get("trip_id"),
            payment_id=payload.get("payment_id"),
            support_case_id=payload.get("support_case_id"),
            created_by=context.subject_id,
            updated_by=context.subject_id,
        )
        dispute.timeline.append(
            _timeline_entry(
                event_type="dispute_created",
                actor_id=context.subject_id,
                request_id=request_meta["request_id"],
                trace_id=request_meta["trace_id"],
                correlation_id=request_meta["correlation_id"],
                message="Dispute created",
                payload={"policy_version": dispute.policy_version},
            )
        )
        self.disputes[dispute.dispute_id] = dispute
        self._register_idempotency("dispute", context.tenant_id, idempotency_key, record_id=dispute.dispute_id, payload_hash=payload_hash)
        self._create_evidence(dispute=dispute, request_meta=request_meta)
        return self._dispute_payload(dispute)

    def seed_browser_fixture(self, context) -> dict[str, Any]:
        if self._browser_fixture_seeded:
            return {
                "status": "already_seeded",
                "incident_ids": list(self.incidents),
                "safety_case_ids": list(self.safety_cases),
                "support_case_ids": list(self.support_cases),
                "refund_ids": list(self.refunds),
                "investigation_ids": list(self.investigations),
                "dispute_ids": list(self.disputes),
                "action_ids": list(self.actions),
                "trip_ids": ["trip_browser_1"],
                "driver_ids": ["driver_browser_1"],
            }

        tenant_id = context.tenant_id
        organization_id = context.organization_id
        region_id = self._region_code(context)

        self.runtime.repositories.drivers.save(
            DriverProfile(
                id="driver_browser_1",
                tenant_id=tenant_id,
                organization_id=organization_id,
                region_code=region_id,
                identity_id="identity_driver_browser_1",
                display_name="Amina Browser Driver",
                vehicle_id="vehicle_browser_1",
            )
        )
        self.runtime.repositories.availability.save(
            DriverAvailability(
                id="availability_browser_1",
                tenant_id=tenant_id,
                organization_id=organization_id,
                region_code=region_id,
                driver_id="driver_browser_1",
                requested_state=DriverAvailabilityState.AVAILABLE,
                authoritative_state=DriverAvailabilityState.AVAILABLE,
                dispatchable=True,
                vehicle_id="vehicle_browser_1",
                location_fresh=True,
                server_confirmed_at=utc_now(),
            )
        )
        self.runtime.repositories.trips.save(
            Trip(
                id="trip_browser_1",
                tenant_id=tenant_id,
                organization_id=organization_id,
                region_code=region_id,
                booking_id="booking_browser_1",
                rider_id="rider_browser_1",
                driver_id="driver_browser_1",
                vehicle_id="vehicle_browser_1",
                service_type="economy",
                pickup=AddressRef("Browser Pickup", GeoPoint(-37.8136, 144.9631)),
                destination=AddressRef("Browser Destination", GeoPoint(-37.816, 144.97)),
                lifecycle_state=TripState.IN_PROGRESS,
                safety_state="NORMAL",
            )
        )
        self.runtime.repositories.offers.save(
            DriverOffer(
                id="offer_browser_1",
                tenant_id=tenant_id,
                organization_id=organization_id,
                region_code=region_id,
                driver_id="driver_browser_1",
                trip_id="trip_browser_1",
                estimated_earnings=Money.of("12.50", "AUD"),
                state=OfferState.CREATED,
            )
        )
        self.runtime.repositories.events.append(
            MobilityEvent(
                event_type="TripLocationUpdated",
                aggregate_id="trip_browser_1",
                aggregate_type="Trip",
                aggregate_version=1,
                tenant_id=tenant_id,
                region=region_id,
                actor_type=ActorType.SYSTEM.value,
                actor_id="system",
                correlation_id="browser-seed-corr",
                causation_id=None,
                payload={
                    "point": {
                        "lat": -37.8135,
                        "lng": 144.965,
                        "heading": 90,
                        "speed": 32,
                        "label": "Browser live route",
                    }
                },
            )
        )
        self.runtime.repositories.emergencies.save(
            EmergencyCase(
                id="emergency_browser_1",
                tenant_id=tenant_id,
                organization_id=organization_id,
                region_code=region_id,
                source=ActorType.RIDER,
                source_id="rider_browser_1",
                trip_id="trip_browser_1",
                state=EmergencyState.TRIGGERED,
                evidence_locked=True,
                visible_reference="safety-browser-1",
            )
        )
        self.runtime.repositories.incidents.save(
            Incident(
                id="runtime_incident_browser_1",
                tenant_id=tenant_id,
                organization_id=organization_id,
                region_code=region_id,
                category="Dispatch delay",
                state=RuntimeIncidentState.REPORTED,
                severity="SEV2",
                owner_id="ops_browser",
            )
        )
        request_meta = {
            "actor_id": context.subject_id,
            "request_id": "browser-seed-req",
            "trace_id": "browser-seed-trace",
            "correlation_id": "browser-seed-corr",
        }
        self.create_incident(
            context,
            {
                "title": "Browser dispatch delay",
                "severity": "SEV2",
                "description": "Seeded operations incident for browser certification",
                "affected_trips": ["trip_browser_1"],
                "idempotency_key": "browser-incident",
            },
            request_meta,
        )
        self.incidents["ops_browser_1"] = OperationalIncident(
            incident_id="ops_browser_1",
            tenant_id=tenant_id,
            region_id=region_id,
            title="Browser dispatch delay",
            severity="SEV2",
            status=IncidentState.DETECTED,
            description="Trip linked incident for browser testing",
            affected_trips=("trip_browser_1",),
            created_by=context.subject_id,
            updated_by=context.subject_id,
        )
        self.safety_cases["safety_browser_1"] = SafetyCase(
            case_id="safety_browser_1",
            tenant_id=tenant_id,
            region_id=region_id,
            linked_trip_id="trip_browser_1",
            linked_driver_id="driver_browser_1",
            linked_rider_id="rider_browser_1",
            severity="high",
            status=SafetyCaseState.TRIAGED,
            incident_id="runtime_incident_browser_1",
            created_by=context.subject_id,
            updated_by=context.subject_id,
        )
        self.create_support_case(
            context,
            {
                "case_type": "booking_problem",
                "trip_id": "trip_browser_1",
                "rider_id": "rider_browser_1",
                "driver_id": "driver_browser_1",
                "payment_id": "payment_browser_1",
                "receipt_id": "receipt_browser_1",
                "phone": "+61 400 000 001",
                "email": "rider@example.com",
                "idempotency_key": "browser-support",
            },
            request_meta,
        )
        self.create_refund(
            context,
            {
                "amount": "75",
                "currency": "AUD",
                "payment_id": "payment_browser_1",
                "trip_id": "trip_browser_1",
                "support_case_id": next(iter(self.support_cases)),
                "reason": "Seeded browser refund",
                "idempotency_key": "browser-refund",
            },
            request_meta,
        )
        self.create_payment_investigation(
            context,
            {
                "payment_id": "payment_browser_1",
                "reason": "Seeded browser investigation",
                "idempotency_key": "browser-investigation",
            },
            request_meta,
        )
        self.create_dispute(
            context,
            {
                "trip_id": "trip_browser_1",
                "payment_id": "payment_browser_1",
                "support_case_id": next(iter(self.support_cases)),
                "idempotency_key": "browser-dispute",
            },
            request_meta,
        )
        self.create_action(
            context,
            {
                "action_type": "manual_dispatch",
                "target_id": "trip_browser_1",
                "reason": "Seeded browser action",
                "risk_level": "medium",
                "approval_required": True,
                "idempotency_key": "browser-action",
            },
            request_meta,
        )
        self._browser_fixture_seeded = True
        return {
            "status": "seeded",
            "incident_ids": list(self.incidents),
            "safety_case_ids": list(self.safety_cases),
            "support_case_ids": list(self.support_cases),
            "refund_ids": list(self.refunds),
            "investigation_ids": list(self.investigations),
            "dispute_ids": list(self.disputes),
            "action_ids": list(self.actions),
            "trip_ids": ["trip_browser_1"],
            "driver_ids": ["driver_browser_1"],
        }
