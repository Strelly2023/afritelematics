"""NovaRide Universal Mobility Super Platform Runtime API."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from afritech.novaride_runtime.common.geography import AddressRef, GeoPoint
from afritech.novaride_runtime.common.money import Money
from afritech.novaride_runtime.models import ActorType, BookingIntent, RuntimeContext, TripState
from afritech.novaride_runtime.services import create_runtime
from afritech.novaride_runtime.events.replay_planner import ReplayMode
from afritech.novaride_runtime.replay import (
    InvalidReplayTransition,
    ReplayPlanRepository,
    ReplayPlanRecord,
    ReplayService,
    get_replay_plan_repository,
    get_replay_service,
)
from afritech.novaride_runtime.replay.hashing import replay_plan_hash
from afritech.novaride_runtime.security import (
    NovaRideRuntimeContext,
    require_driver_ownership_or_operations,
    require_permissions,
    require_runtime_context,
)


_RUNTIME = create_runtime()
RuntimeReadContext = Annotated[
    NovaRideRuntimeContext,
    Depends(
        require_permissions(
            "novaride.runtime.read",
            allowed_roles={
                "PLATFORM_OWNER",
                "PLATFORM_ADMIN",
                "OPERATIONS_TEAM",
                "QA_ENGINEER",
                "SECURITY_ENGINEER",
                "AUDIT_TEAM",
            },
        )
    ),
]

ReplayCreateContext = Annotated[
    NovaRideRuntimeContext,
    Depends(
        require_permissions(
            "novaride.replay.create",
            allowed_roles={"PLATFORM_ADMIN", "OPERATIONS_TEAM", "QA_ENGINEER"},
        )
    ),
]

ReplayReviewContext = Annotated[
    NovaRideRuntimeContext,
    Depends(
        require_permissions(
            "novaride.replay.review",
            allowed_roles={"PLATFORM_ADMIN", "OPERATIONS_TEAM", "QA_ENGINEER", "AUDIT_TEAM"},
        )
    ),
]

ReplayValidateContext = Annotated[
    NovaRideRuntimeContext,
    Depends(
        require_permissions(
            "novaride.replay.validate",
            allowed_roles={"PLATFORM_ADMIN", "OPERATIONS_TEAM", "QA_ENGINEER"},
        )
    ),
]

ReplayExecuteContext = Annotated[
    NovaRideRuntimeContext,
    Depends(
        require_permissions(
            "novaride.replay.execute",
            allowed_roles={"PLATFORM_ADMIN", "OPERATIONS_TEAM", "QA_ENGINEER"},
        )
    ),
]

ReplayApproveContext = Annotated[
    NovaRideRuntimeContext,
    Depends(
        require_permissions(
            "novaride.replay.approve",
            allowed_roles={"PLATFORM_ADMIN", "PROJECT_MANAGER", "OPERATIONS_TEAM", "QA_ENGINEER", "SECURITY_ENGINEER"},
        )
    ),
]

ReplayPromoteContext = Annotated[
    NovaRideRuntimeContext,
    Depends(
        require_permissions(
            "novaride.replay.promote",
            allowed_roles={"PLATFORM_ADMIN", "DEVOPS_ENGINEER", "OPERATIONS_TEAM"},
        )
    ),
]

DriverShiftContext = Annotated[
    NovaRideRuntimeContext,
    Depends(
        require_permissions(
            "novaride.driver.shift.manage",
            allowed_roles={"PLATFORM_ADMIN", "OPERATIONS_TEAM", "INCIDENT_RESPONSE_TEAM"},
        )
    ),
]

DriverAvailabilityContext = Annotated[
    NovaRideRuntimeContext,
    Depends(
        require_permissions(
            "novaride.driver.availability.manage",
            allowed_roles={"PLATFORM_ADMIN", "OPERATIONS_TEAM", "INCIDENT_RESPONSE_TEAM"},
        )
    ),
]

DispatchContext = Annotated[
    NovaRideRuntimeContext,
    Depends(
        require_permissions(
            "novaride.dispatch.manage",
            allowed_roles={"PLATFORM_ADMIN", "OPERATIONS_TEAM"},
        )
    ),
]

OperatorCommandContext = Annotated[
    NovaRideRuntimeContext,
    Depends(
        require_permissions(
            "novaride.operator.command.execute",
            allowed_roles={"PLATFORM_ADMIN", "OPERATIONS_TEAM", "INCIDENT_RESPONSE_TEAM"},
        )
    ),
]

FleetContext = Annotated[
    NovaRideRuntimeContext,
    Depends(
        require_permissions(
            "novaride.fleet.manage",
            allowed_roles={"PLATFORM_ADMIN", "OPERATIONS_TEAM"},
        )
    ),
]

LogisticsContext = Annotated[
    NovaRideRuntimeContext,
    Depends(
        require_permissions(
            "novaride.logistics.manage",
            allowed_roles={"PLATFORM_ADMIN", "OPERATIONS_TEAM"},
        )
    ),
]

CorporateContext = Annotated[
    NovaRideRuntimeContext,
    Depends(
        require_permissions(
            "novaride.corporate.manage",
            allowed_roles={"PLATFORM_ADMIN", "CORPORATE_ADMIN", "OPERATIONS_TEAM"},
        )
    ),
]


class RuntimeContextHeaders(BaseModel):
    tenant_id: str = "tenant_novaride"
    organization_id: str = "org_novatech"
    region_code: str = "AU"
    actor_type: ActorType = ActorType.SYSTEM
    actor_id: str = "system"
    correlation_id: str = "corr_api"


class AddressPayload(BaseModel):
    label: str
    lat: float | None = None
    lng: float | None = None
    landmark: str | None = None
    airport_terminal: str | None = None

    def to_ref(self) -> AddressRef:
        point = GeoPoint(self.lat, self.lng) if self.lat is not None and self.lng is not None else None
        return AddressRef(self.label, point, self.landmark, self.airport_terminal)


class RiderOnboardingRequest(BaseModel):
    display_name: str = "NovaRide Rider"
    identity_id: str = "novaid_rider"


class DriverOnboardingRequest(BaseModel):
    display_name: str = "NovaRide Driver"
    identity_id: str = "novaid_driver"
    vehicle_id: str | None = "vehicle_runtime"


class FareQuoteRequest(BaseModel):
    pickup: AddressPayload = Field(default_factory=lambda: AddressPayload(label="Pickup"))
    destination: AddressPayload = Field(default_factory=lambda: AddressPayload(label="Destination"))
    service_type: str = "economy"
    currency: str = "AUD"


class BookingRequest(BaseModel):
    rider_id: str
    pickup: AddressPayload = Field(default_factory=lambda: AddressPayload(label="Pickup"))
    destination: AddressPayload = Field(default_factory=lambda: AddressPayload(label="Destination"))
    service_type: str = "economy"
    quote_id: str | None = None
    payment_preference: str = "NovaPay Wallet"


class EmergencyRequest(BaseModel):
    source_id: str
    trip_id: str | None = None


class OperatorCommandRequest(BaseModel):
    command_type: str
    target_id: str
    reason: str
    high_risk: bool = False
    approval_reference: str | None = None


class FleetRequest(BaseModel):
    name: str


class VehicleAssignmentRequest(BaseModel):
    vehicle_id: str


class LogisticsOrderRequest(BaseModel):
    sender_id: str
    recipient_name: str
    pickup: AddressPayload = Field(default_factory=lambda: AddressPayload(label="Pickup"))
    dropoff: AddressPayload = Field(default_factory=lambda: AddressPayload(label="Dropoff"))
    package_metadata: dict[str, Any] = Field(default_factory=dict)


class CorporateAccountRequest(BaseModel):
    name: str


class CorporateBookingRequest(BaseModel):
    account_id: str
    employee_id: str
    booking_id: str
    cost_center_id: str | None = None


class ReplayPlanRequest(BaseModel):
    mode: ReplayMode
    scope: dict[str, str]
    reason: str
    approval_reference: str | None = None
    rollback_plan: str = "shadow_rebuild_no_source_mutation"


def _region_code(region: str) -> str:
    normalized = region.strip().upper()
    if normalized in {"AU", "US", "CA", "UK", "EU", "IN", "KE", "TZ", "UG", "RW", "BI", "DRC", "NG", "GH", "ZM", "ZA"}:
        return normalized
    if "AUSTRALIA" in normalized:
        return "AU"
    return normalized[:2] if len(normalized) > 2 else normalized


def _context(
    x_tenant_id: str = "tenant_novaride",
    x_organization_id: str = "org_novatech",
    x_region_code: str = "AU",
    x_actor_type: str = "SYSTEM",
    x_actor_id: str = "system",
    x_correlation_id: str = "corr_api",
) -> RuntimeContext:
    try:
        actor_type = ActorType(x_actor_type.upper())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid_actor_type") from exc
    return RuntimeContext(
        tenant_id=x_tenant_id,
        organization_id=x_organization_id,
        region_code=_region_code(x_region_code),
        actor_type=actor_type,
        actor_id=x_actor_id,
        correlation_id=x_correlation_id,
    )


def _json(value: Any) -> Any:
    from afritech.novaride_runtime.services import _json as runtime_json

    return runtime_json(value)


def build_novaride_runtime_router() -> APIRouter:
    router = APIRouter(
        prefix="/v1",
        tags=["NovaRide Runtime"],
        dependencies=[Depends(require_runtime_context)],
    )

    @router.get("/novaride/runtime/status")
    def runtime_status(context: RuntimeReadContext) -> dict[str, Any]:
        return _RUNTIME.status()

    @router.get("/novaride/runtime/events")
    def runtime_events(context: RuntimeReadContext) -> dict[str, Any]:
        return {"events": [event.as_dict() for event in _RUNTIME.repositories.events.all()]}

    @router.get("/novaride/runtime/events/aggregate/{aggregate_id}")
    def runtime_events_by_aggregate(aggregate_id: str, context: RuntimeReadContext) -> dict[str, Any]:
        return {"events": [event.as_dict() for event in _RUNTIME.repositories.events.by_aggregate(aggregate_id)]}

    @router.get("/novaride/runtime/events/correlation/{correlation_id}")
    def runtime_events_by_correlation(correlation_id: str, context: RuntimeReadContext) -> dict[str, Any]:
        return {"events": [event.as_dict() for event in _RUNTIME.repositories.events.by_correlation(correlation_id)]}

    @router.get("/novaride/runtime/guards")
    def runtime_guards(context: RuntimeReadContext) -> dict[str, Any]:
        return {**_RUNTIME.policy.ga_guard(), **_RUNTIME.policy.real_payment_guard()}

    @router.post("/operator/replay/plans", status_code=status.HTTP_201_CREATED)
    async def operator_replay_plan(
        payload: ReplayPlanRequest,
        context: ReplayCreateContext,
        service: Annotated[ReplayService, Depends(get_replay_service)],
        idempotency_key: str = Header(..., alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        plan = await service.create_plan(payload=payload, actor=context, idempotency_key=idempotency_key)
        return {
            "replay_id": plan.id,
            "mode": payload.mode.value,
            "scope": payload.scope,
            "state": plan.status,
            "rollback_plan": payload.rollback_plan,
            "plan_hash": plan.plan_hash,
            "version": plan.version,
        }

    @router.get("/operator/replay/plans/{replay_id}")
    async def operator_replay_get(
        replay_id: str,
        context: ReplayReviewContext,
        service: Annotated[ReplayService, Depends(get_replay_service)],
    ) -> dict[str, Any]:
        plan = await service.get_plan(tenant_id=context.tenant_id, plan_id=replay_id)
        if plan is None:
            raise HTTPException(status_code=404, detail="replay_plan_not_found")
        return {"replay_id": plan.id, "state": plan.status, "plan_hash": plan.plan_hash, "version": plan.version}

    @router.post("/operator/replay/{replay_id}/validate")
    async def operator_replay_validate(
        replay_id: str,
        context: ReplayValidateContext,
        service: Annotated[ReplayService, Depends(get_replay_service)],
    ) -> dict[str, Any]:
        plan = await service.get_plan(tenant_id=context.tenant_id, plan_id=replay_id)
        if plan is None:
            raise HTTPException(status_code=404, detail="replay_plan_not_found")
        try:
            result = await service.execute_plan(plan=plan, actor=context, validate_only=True)
        except InvalidReplayTransition as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        return result.result_payload

    @router.post("/operator/replay/{replay_id}/execute")
    async def operator_replay_execute(
        replay_id: str,
        context: ReplayExecuteContext,
        service: Annotated[ReplayService, Depends(get_replay_service)],
    ) -> dict[str, Any]:
        plan = await service.get_plan(tenant_id=context.tenant_id, plan_id=replay_id)
        if plan is None:
            raise HTTPException(status_code=404, detail="replay_plan_not_found")
        try:
            result = await service.execute_plan(plan=plan, actor=context, validate_only=False)
        except InvalidReplayTransition as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        return result.result_payload

    @router.get("/operator/replay/{replay_id}/comparison")
    async def operator_replay_comparison(
        replay_id: str,
        context: ReplayReviewContext,
        service: Annotated[ReplayService, Depends(get_replay_service)],
    ) -> dict[str, Any]:
        result = await service.repository.get_result(tenant_id=context.tenant_id, plan_id=replay_id)
        if result is None:
            raise HTTPException(status_code=404, detail="replay_result_not_found")
        return result.result_payload

    @router.post("/operator/replay/{replay_id}/approve-promotion")
    async def operator_replay_approve(
        replay_id: str,
        approval_reference: str,
        context: ReplayApproveContext,
        service: Annotated[ReplayService, Depends(get_replay_service)],
    ) -> dict[str, Any]:
        plan = await service.get_plan(tenant_id=context.tenant_id, plan_id=replay_id)
        if plan is None:
            raise HTTPException(status_code=404, detail="replay_plan_not_found")
        try:
            vote = await service.record_approval_vote(plan=plan, actor=context, decision="APPROVE", reason=approval_reference)
        except InvalidReplayTransition as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        approvals = await service.repository.get_approvals(tenant_id=context.tenant_id, plan_id=replay_id)
        approved_votes = [item for item in approvals if item.status == "APPROVED" and item.plan_hash == plan.plan_hash and item.plan_version == plan.version]
        status_value = "APPROVED" if len(approved_votes) >= 2 else "APPROVAL_REQUIRED"
        return {
            "approval_id": vote.id,
            "status": status_value,
            "quorum": len(approved_votes),
            "required_quorum": vote.required_quorum,
        }

    @router.post("/operator/replay/{replay_id}/promote")
    async def operator_replay_promote(
        replay_id: str,
        context: ReplayPromoteContext,
        service: Annotated[ReplayService, Depends(get_replay_service)],
    ) -> dict[str, Any]:
        plan = await service.get_plan(tenant_id=context.tenant_id, plan_id=replay_id)
        if plan is None:
            raise HTTPException(status_code=404, detail="replay_result_not_found")
        result = await service.repository.get_result(tenant_id=context.tenant_id, plan_id=replay_id)
        if result is None:
            raise HTTPException(status_code=404, detail="replay_result_not_found")
        try:
            promoted = await service.promote_plan(plan=plan, actor=context)
        except InvalidReplayTransition as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        return {"replay_id": promoted.id, "state": promoted.status, "version": promoted.version}

    @router.get("/operator/replay/history")
    async def operator_replay_history(
        context: ReplayReviewContext,
        service: Annotated[ReplayService, Depends(get_replay_service)],
    ) -> dict[str, Any]:
        plans = await service.list_plans(tenant_id=context.tenant_id)
        return {"plans": [{"replay_id": plan.id, "state": plan.status, "plan_hash": plan.plan_hash, "version": plan.version} for plan in plans]}

    @router.get("/novaride/runtime/command-center")
    def runtime_command_center(context: RuntimeReadContext) -> dict[str, Any]:
        return _RUNTIME.read_models.command_center(context.tenant_id)

    @router.post("/riders/onboarding")
    def rider_onboarding(payload: RiderOnboardingRequest, context: RuntimeReadContext) -> dict[str, Any]:
        from afritech.novaride_runtime.models import RiderProfile

        rider = RiderProfile(
            id=context.subject_id,
            tenant_id=context.tenant_id,
            organization_id=context.organization_id,
            region_code=context.region,
            identity_id=payload.identity_id,
            display_name=payload.display_name,
        )
        _RUNTIME.repositories.riders.save(rider)
        return _json(rider)

    @router.post("/drivers/onboarding")
    def driver_onboarding(payload: DriverOnboardingRequest, context: RuntimeReadContext) -> dict[str, Any]:
        return _json(_RUNTIME.driver.onboard(_context(x_tenant_id=context.tenant_id, x_organization_id=context.organization_id, x_region_code=context.region, x_actor_type="DRIVER", x_actor_id=context.subject_id, x_correlation_id="corr_api"), identity_id=payload.identity_id, display_name=payload.display_name, vehicle_id=payload.vehicle_id))

    @router.post("/driver/shifts/start")
    @router.post("/novaride/runtime/driver/shifts/start")
    def driver_shift_start(context: DriverShiftContext) -> dict[str, Any]:
        ctx = _context(x_tenant_id=context.tenant_id, x_organization_id=context.organization_id, x_region_code=context.region, x_actor_type="DRIVER", x_actor_id=context.subject_id, x_correlation_id="corr_api")
        require_driver_ownership_or_operations(context=context, driver_identity_id=context.subject_id)
        return _json(_RUNTIME.driver.start_shift(ctx, context.subject_id))

    @router.put("/driver/{driver_id}/availability")
    @router.put("/novaride/runtime/driver/{driver_id}/availability")
    def driver_availability(context: DriverAvailabilityContext, driver_id: str, location_fresh: bool = True) -> dict[str, Any]:
        require_driver_ownership_or_operations(context=context, driver_identity_id=driver_id)
        ctx = _context(x_tenant_id=context.tenant_id, x_organization_id=context.organization_id, x_region_code=context.region, x_actor_type="DRIVER", x_actor_id=context.subject_id, x_correlation_id="corr_api")
        availability = _RUNTIME.driver.set_available(ctx, driver_id, location_fresh=location_fresh)
        return {
            "driver_id": availability.driver_id,
            "requested_state": availability.requested_state.value,
            "authoritative_state": availability.authoritative_state.value,
            "eligible": availability.dispatchable,
            "dispatchable": availability.dispatchable,
            "eligibility_reasons": ["identity_valid", "vehicle_compliant", "region_enabled"] if availability.dispatchable else ["server_confirmation_required"],
            "active_shift_id": availability.active_shift_id,
            "vehicle_id": availability.vehicle_id,
            "location_fresh": availability.location_fresh,
            "server_confirmed_at": availability.server_confirmed_at.isoformat() if availability.server_confirmed_at else None,
            "aggregate_version": availability.aggregate_version,
            "correlation_id": ctx.correlation_id,
        }

    @router.get("/driver/{driver_id}/ride-queue")
    def driver_ride_queue(driver_id: str, context: RuntimeReadContext) -> dict[str, Any]:
        return {"offers": _RUNTIME.read_models.driver_queue(context.tenant_id, driver_id)}

    @router.post("/rider/fares/quote")
    def rider_fare_quote(payload: FareQuoteRequest, context: RuntimeReadContext) -> dict[str, Any]:
        ctx = _context(x_tenant_id=context.tenant_id, x_organization_id=context.organization_id, x_region_code=context.region, x_actor_type="RIDER", x_actor_id=context.subject_id, x_correlation_id="corr_api")
        return _json(_RUNTIME.booking.create_quote(ctx, service_type=payload.service_type, currency=payload.currency))

    @router.post("/rider/bookings")
    def rider_booking(payload: BookingRequest, context: RuntimeReadContext, idempotency_key: str = Header(..., alias="Idempotency-Key")) -> dict[str, Any]:
        ctx = _context(x_tenant_id=context.tenant_id, x_organization_id=context.organization_id, x_region_code=context.region, x_actor_type="RIDER", x_actor_id=context.subject_id, x_correlation_id="corr_api")
        intent = BookingIntent(context.subject_id, payload.pickup.to_ref(), payload.destination.to_ref(), payload.service_type, payload.payment_preference)
        return _json(_RUNTIME.booking.create_booking(ctx, intent, quote_id=payload.quote_id, idempotency_key=idempotency_key))

    @router.post("/novaride/runtime/dispatch/{booking_id}")
    def runtime_dispatch(booking_id: str, context: DispatchContext) -> dict[str, Any]:
        ctx = _context(x_tenant_id=context.tenant_id, x_organization_id=context.organization_id, x_region_code=context.region, x_actor_type="OPERATOR", x_actor_id=context.subject_id, x_correlation_id="corr_api")
        return _json(_RUNTIME.dispatch.start_dispatch(ctx, booking_id))

    @router.post("/driver/offers/{offer_id}/accept")
    def driver_offer_accept(offer_id: str, context: DriverShiftContext) -> dict[str, Any]:
        ctx = _context(x_tenant_id=context.tenant_id, x_organization_id=context.organization_id, x_region_code=context.region, x_actor_type="DRIVER", x_actor_id=context.subject_id, x_correlation_id="corr_api")
        return _json(_RUNTIME.dispatch.accept_offer(ctx, offer_id))

    @router.post("/driver/trips/{trip_id}/arrive")
    def driver_trip_arrive(trip_id: str, context: DriverShiftContext) -> dict[str, Any]:
        ctx = _context(x_tenant_id=context.tenant_id, x_organization_id=context.organization_id, x_region_code=context.region, x_actor_type="DRIVER", x_actor_id=context.subject_id, x_correlation_id="corr_api")
        return _json(_RUNTIME.trip.transition(ctx, trip_id, TripState.DRIVER_ARRIVED))

    @router.post("/driver/trips/{trip_id}/verify-passenger")
    def driver_trip_verify(trip_id: str, context: DriverShiftContext) -> dict[str, Any]:
        ctx = _context(x_tenant_id=context.tenant_id, x_organization_id=context.organization_id, x_region_code=context.region, x_actor_type="DRIVER", x_actor_id=context.subject_id, x_correlation_id="corr_api")
        return _json(_RUNTIME.trip.transition(ctx, trip_id, TripState.PICKUP_VERIFIED))

    @router.post("/driver/trips/{trip_id}/start")
    def driver_trip_start(trip_id: str, context: DriverShiftContext) -> dict[str, Any]:
        ctx = _context(x_tenant_id=context.tenant_id, x_organization_id=context.organization_id, x_region_code=context.region, x_actor_type="DRIVER", x_actor_id=context.subject_id, x_correlation_id="corr_api")
        return _json(_RUNTIME.trip.transition(ctx, trip_id, TripState.IN_PROGRESS))

    @router.post("/driver/trips/{trip_id}/complete")
    def driver_trip_complete(trip_id: str, context: DriverShiftContext) -> dict[str, Any]:
        ctx = _context(x_tenant_id=context.tenant_id, x_organization_id=context.organization_id, x_region_code=context.region, x_actor_type="DRIVER", x_actor_id=context.subject_id, x_correlation_id="corr_api")
        trip = _RUNTIME.repositories.trips.get(trip_id)
        if trip and trip.lifecycle_state == TripState.IN_PROGRESS:
            _RUNTIME.trip.transition(ctx, trip_id, TripState.COMPLETING)
        return _json(_RUNTIME.trip.transition(ctx, trip_id, TripState.COMPLETED))

    @router.post("/driver/trips/{trip_id}/location")
    def driver_trip_location(trip_id: str, lat: float, lng: float, context: DriverShiftContext) -> dict[str, Any]:
        ctx = _context(x_tenant_id=context.tenant_id, x_organization_id=context.organization_id, x_region_code=context.region, x_actor_type="DRIVER", x_actor_id=context.subject_id, x_correlation_id="corr_api")
        _RUNTIME.trip.location(ctx, trip_id, GeoPoint(lat, lng))
        return {"status": "RECORDED"}

    @router.post("/driver/emergency")
    @router.post("/rider/trips/{trip_id}/emergency")
    def emergency(context: RuntimeReadContext, payload: EmergencyRequest, trip_id: str | None = None, idempotency_key: str = Header(..., alias="Idempotency-Key")) -> dict[str, Any]:
        ctx = _context(x_tenant_id=context.tenant_id, x_organization_id=context.organization_id, x_region_code=context.region, x_actor_type="RIDER", x_actor_id=context.subject_id, x_correlation_id="corr_api")
        return _json(_RUNTIME.safety.activate_emergency(ctx, source_id=context.subject_id, trip_id=trip_id or payload.trip_id, idempotency_key=idempotency_key))

    @router.get("/operator/command-center")
    def operator_command_center(context: RuntimeReadContext) -> dict[str, Any]:
        return _RUNTIME.read_models.command_center(context.tenant_id)

    @router.post("/operator/emergencies/{emergency_id}/acknowledge")
    def operator_emergency_ack(emergency_id: str, context: OperatorCommandContext) -> dict[str, Any]:
        ctx = _context(x_tenant_id=context.tenant_id, x_organization_id=context.organization_id, x_region_code=context.region, x_actor_type="OPERATOR", x_actor_id=context.subject_id, x_correlation_id="corr_api")
        return _json(_RUNTIME.safety.acknowledge(ctx, emergency_id))

    @router.post("/operator/commands")
    def operator_command(payload: OperatorCommandRequest, context: OperatorCommandContext) -> dict[str, Any]:
        ctx = _context(x_tenant_id=context.tenant_id, x_organization_id=context.organization_id, x_region_code=context.region, x_actor_type="OPERATOR", x_actor_id=context.subject_id, x_correlation_id="corr_api")
        return _json(_RUNTIME.operator.command(ctx, command_type=payload.command_type, target_id=payload.target_id, reason=payload.reason, high_risk=payload.high_risk, approval_reference=payload.approval_reference))

    @router.post("/fleets")
    def fleet_create(payload: FleetRequest, context: FleetContext) -> dict[str, Any]:
        ctx = _context(x_tenant_id=context.tenant_id, x_organization_id=context.organization_id, x_region_code=context.region, x_actor_type="OPERATOR", x_actor_id=context.subject_id, x_correlation_id="corr_api")
        return _json(_RUNTIME.fleet.create_fleet(ctx, payload.name))

    @router.post("/fleets/{fleet_id}/vehicles")
    def fleet_vehicle_assign(fleet_id: str, payload: VehicleAssignmentRequest, context: FleetContext) -> dict[str, Any]:
        ctx = _context(x_tenant_id=context.tenant_id, x_organization_id=context.organization_id, x_region_code=context.region, x_actor_type="OPERATOR", x_actor_id=context.subject_id, x_correlation_id="corr_api")
        return _json(_RUNTIME.fleet.assign_vehicle(ctx, fleet_id, payload.vehicle_id))

    @router.post("/logistics/orders")
    def logistics_order(payload: LogisticsOrderRequest, context: LogisticsContext) -> dict[str, Any]:
        ctx = _context(x_tenant_id=context.tenant_id, x_organization_id=context.organization_id, x_region_code=context.region, x_actor_type="RIDER", x_actor_id=context.subject_id, x_correlation_id="corr_api")
        return _json(_RUNTIME.logistics.create_order(ctx, context.subject_id, payload.recipient_name, payload.pickup.to_ref(), payload.dropoff.to_ref(), payload.package_metadata))

    @router.post("/logistics/orders/{order_id}/pickup")
    def logistics_pickup(order_id: str, context: DriverShiftContext) -> dict[str, Any]:
        ctx = _context(x_tenant_id=context.tenant_id, x_organization_id=context.organization_id, x_region_code=context.region, x_actor_type="DRIVER", x_actor_id=context.subject_id, x_correlation_id="corr_api")
        return _json(_RUNTIME.logistics.pickup(ctx, order_id))

    @router.post("/logistics/orders/{order_id}/deliver")
    def logistics_deliver(order_id: str, context: DriverShiftContext) -> dict[str, Any]:
        ctx = _context(x_tenant_id=context.tenant_id, x_organization_id=context.organization_id, x_region_code=context.region, x_actor_type="DRIVER", x_actor_id=context.subject_id, x_correlation_id="corr_api")
        return _json(_RUNTIME.logistics.deliver(ctx, order_id))

    @router.post("/corporate/accounts")
    def corporate_account(payload: CorporateAccountRequest, context: CorporateContext) -> dict[str, Any]:
        ctx = _context(x_tenant_id=context.tenant_id, x_organization_id=context.organization_id, x_region_code=context.region, x_actor_type="OPERATOR", x_actor_id=context.subject_id, x_correlation_id="corr_api")
        return _json(_RUNTIME.corporate.create_account(ctx, payload.name))

    @router.post("/corporate/bookings")
    def corporate_booking(payload: CorporateBookingRequest, context: CorporateContext) -> dict[str, Any]:
        ctx = _context(x_tenant_id=context.tenant_id, x_organization_id=context.organization_id, x_region_code=context.region, x_actor_type="OPERATOR", x_actor_id=context.subject_id, x_correlation_id="corr_api")
        return _json(_RUNTIME.corporate.create_booking(ctx, payload.account_id, payload.employee_id, payload.booking_id, payload.cost_center_id))

    @router.post("/transit/journeys/plan")
    def transit_plan(context: RuntimeReadContext) -> dict[str, Any]:
        ctx = _context(x_tenant_id=context.tenant_id, x_organization_id=context.organization_id, x_region_code=context.region, x_actor_type="RIDER", x_actor_id=context.subject_id, x_correlation_id="corr_api")
        return _json(_RUNTIME.transit.plan(ctx, context.subject_id))

    @router.get("/novaride/wallets/me/summary")
    def wallet_summary(context: RuntimeReadContext) -> dict[str, Any]:
        ctx = _context(x_tenant_id=context.tenant_id, x_organization_id=context.organization_id, x_region_code=context.region, x_actor_type="RIDER", x_actor_id=context.subject_id, x_correlation_id="corr_api")
        return _RUNTIME.novapay.wallet_summary(ctx)

    @router.post("/novaride/payment-intents")
    def payment_intent(context: RuntimeReadContext, amount: str = "19.80", currency: str = "AUD") -> dict[str, Any]:
        ctx = _context(x_tenant_id=context.tenant_id, x_organization_id=context.organization_id, x_region_code=context.region, x_actor_type="RIDER", x_actor_id=context.subject_id, x_correlation_id="corr_api")
        return _json(_RUNTIME.novapay.create_payment_intent_reference(Money.of(amount, currency), ctx))

    return router


__all__ = ["build_novaride_runtime_router"]
