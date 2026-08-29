"""NovaRide Operations API backed by live runtime repositories."""

from __future__ import annotations

from typing import Any, Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from afritech.api.auth.jwt_device_auth import JWTClaims
from afritech.novaride_runtime.common.identifiers import new_id
from afritech.novaride_runtime.common.errors import AuthorityDenied
from afritech.novaride_runtime.config import create_runtime_from_environment
from afritech.novaride_runtime.operations_workspace import OperationsWorkspaceService
from afritech.novaride_runtime.security import NovaRideRuntimeContext, require_permissions, require_runtime_context


_RUNTIME = create_runtime_from_environment()
_WORKSPACE = OperationsWorkspaceService(_RUNTIME)


def _raise_not_found(exc: Exception) -> HTTPException:
    return HTTPException(status_code=404, detail=str(exc))


def _raise_bad_request(exc: Exception) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


def _raise_conflict(exc: Exception) -> HTTPException:
    return HTTPException(status_code=409, detail=str(exc))


def _request_meta(context: NovaRideRuntimeContext, request: Request) -> dict[str, str]:
    return {
        "actor_id": context.subject_id,
        "request_id": request.headers.get("X-Request-Id")
        or request.headers.get("X-Request-ID")
        or new_id("req"),
        "trace_id": request.headers.get("X-Trace-Id") or request.headers.get("X-Trace-ID") or new_id("trace"),
        "correlation_id": request.headers.get("X-Correlation-Id") or new_id("corr"),
    }


def _context_from_verified(context: NovaRideRuntimeContext) -> dict[str, Any]:
    return {
        "tenant_id": context.tenant_id,
        "organization_id": context.organization_id,
        "region_code": context.region,
        "actor_id": context.subject_id,
    }


READ_ROLES = {
    "PLATFORM_ADMIN",
    "OPERATIONS_TEAM",
    "INCIDENT_RESPONSE_TEAM",
    "SAFETY_SPECIALIST",
    "SUPPORT_AGENT",
    "SUPPORT_SUPERVISOR",
    "FINANCE_OPS",
    "FINANCE_OPERATION",
    "REFUND_APPROVER",
    "COMPLIANCE_OFFICER",
    "AUDITOR",
    "EXECUTIVE_VIEWER",
}

MANAGE_ROLES = {
    "PLATFORM_ADMIN",
    "OPERATIONS_TEAM",
    "INCIDENT_RESPONSE_TEAM",
    "SAFETY_SPECIALIST",
    "SUPPORT_SUPERVISOR",
    "FINANCE_OPS",
    "REFUND_APPROVER",
    "COMPLIANCE_OFFICER",
}

OverviewContext = Annotated[
    NovaRideRuntimeContext,
    Depends(
        require_permissions(
            "novaride.operations.overview.read",
            allowed_roles=READ_ROLES,
        )
    ),
]

ReadContext = Annotated[
    NovaRideRuntimeContext,
    Depends(
        require_permissions(
            "novaride.operations.audit.read",
            allowed_roles=READ_ROLES,
        )
    ),
]

ManageContext = Annotated[
    NovaRideRuntimeContext,
    Depends(
        require_permissions(
            "novaride.operations.action.request",
            allowed_roles=MANAGE_ROLES,
        )
    ),
]


class IncidentPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    title: str = Field(default="Operational incident")
    severity: str = Field(default="SEV3")
    description: str = ""
    affected_trips: list[str] = Field(default_factory=list)
    affected_services: list[str] = Field(default_factory=list)


class CasePayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    case_type: str = Field(default="booking_problem")
    trip_id: str | None = None
    rider_id: str | None = None
    driver_id: str | None = None
    payment_id: str | None = None
    receipt_id: str | None = None
    phone: str | None = None
    email: str | None = None


class RefundPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    amount: str = Field(min_length=1)
    currency: str = Field(default="AUD", min_length=1)
    payment_id: str | None = None
    receipt_id: str | None = None
    trip_id: str | None = None
    support_case_id: str | None = None
    reason: str = ""


class InvestigationPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    payment_id: str = Field(min_length=1)
    reason: str = ""


class DisputePayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    trip_id: str | None = None
    payment_id: str | None = None
    support_case_id: str | None = None


class ActionPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    action_type: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    reason: str = ""
    risk_level: str = "medium"
    approval_required: bool = True
    approval_reference: str | None = None


class PricingPayload(BaseModel):
    policy_id: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    approval_reference: str | None = None


class NotificationPayload(BaseModel):
    audience: str = Field(min_length=1)
    message: str = Field(min_length=1, max_length=2000)


class HandoverPayload(BaseModel):
    incoming_operator_id: str = Field(min_length=1)
    summary: str = Field(min_length=1, max_length=4000)


def build_novaride_operations_router(workspace: OperationsWorkspaceService | None = None) -> APIRouter:
    workspace = workspace or _WORKSPACE
    router = APIRouter(
        prefix="/api/v1/novaride/operations",
        tags=["novaride-operations"],
        dependencies=[Depends(require_runtime_context)],
    )

    @router.get("/overview")
    def overview(context: OverviewContext) -> dict[str, Any]:
        return workspace.overview(context)

    @router.get("/dependencies")
    def dependencies(context: ReadContext) -> dict[str, Any]:
        return {"generated_at": workspace.overview(context)["generated_at"], "dependencies": workspace.dependency_statuses()}

    @router.get("/map")
    def live_map(context: ReadContext, limit: int = 100) -> dict[str, Any]:
        return workspace.live_map(context, limit=limit)

    @router.get("/trips/live")
    def live_trips(context: ReadContext, limit: int = 50) -> dict[str, Any]:
        return workspace.live_trips(context, limit=limit)

    @router.get("/drivers/live")
    def live_drivers(context: ReadContext, limit: int = 50) -> dict[str, Any]:
        return workspace.live_drivers(context, limit=limit)

    @router.get("/dispatch/queue")
    def dispatch_queue(context: ReadContext, limit: int = 50) -> dict[str, Any]:
        return workspace.dispatch_queue(context, limit=limit)

    @router.get("/dispatch/health")
    def dispatch_health(context: ReadContext) -> dict[str, Any]:
        return workspace.dispatch_health(context)

    @router.post("/incidents", status_code=201)
    def create_incident(
        payload: IncidentPayload,
        request: Request,
        context: ManageContext,
        idempotency_key: str = Header(default="", alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        try:
            return workspace.create_incident(
                context,
                payload.model_dump(exclude_none=True) | {"idempotency_key": idempotency_key},
                _request_meta(context, request),
            )
        except ValueError as exc:
            if str(exc) == "idempotency_conflict":
                raise _raise_conflict(exc) from exc
            raise _raise_bad_request(exc) from exc

    @router.get("/incidents")
    def list_incidents(context: ReadContext, limit: int = 100) -> dict[str, Any]:
        return {"items": workspace.list_incidents(context, limit=limit), "generated_at": workspace.overview(context)["generated_at"]}

    @router.get("/incidents/{incident_id}")
    def get_incident(incident_id: str, context: ReadContext) -> dict[str, Any]:
        try:
            return workspace.get_incident(context, incident_id)
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.patch("/incidents/{incident_id}")
    def patch_incident(incident_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            return workspace.patch_incident(context, incident_id, payload, _request_meta(context, request))
        except KeyError as exc:
            raise _raise_not_found(exc) from exc
        except ValueError as exc:
            raise _raise_bad_request(exc) from exc

    @router.post("/incidents/{incident_id}/transition")
    def transition_incident(incident_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            return workspace.transition_incident(context, incident_id, payload, _request_meta(context, request))
        except KeyError as exc:
            raise _raise_not_found(exc) from exc
        except ValueError as exc:
            raise _raise_bad_request(exc) from exc

    @router.post("/incidents/{incident_id}/assign")
    def assign_incident(incident_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            return workspace.assign_incident(context, incident_id, payload, _request_meta(context, request))
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.get("/incidents/{incident_id}/timeline")
    def incident_timeline(incident_id: str, context: ReadContext) -> dict[str, Any]:
        try:
            return {"items": workspace.incident_timeline(context, incident_id)}
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.post("/incidents/{incident_id}/timeline")
    def append_incident_timeline(incident_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            incident = workspace.get_incident(context, incident_id)
        except KeyError as exc:
            raise _raise_not_found(exc) from exc
        record = workspace.incidents[incident["incident_id"]]
        workspace._store_timeline(
            record,
            event_type=str(payload.get("event_type", "incident_note")),
            actor_id=context.subject_id,
            request_id=_request_meta(context, request)["request_id"],
            trace_id=_request_meta(context, request)["trace_id"],
            correlation_id=_request_meta(context, request)["correlation_id"],
            message=str(payload.get("message", "")),
            payload=dict(payload),
        )
        workspace._create_evidence(incident=record, request_meta=_request_meta(context, request))
        return {"incident_id": record.incident_id, "timeline": workspace.incident_timeline(context, incident_id)}

    @router.get("/incidents/{incident_id}/evidence")
    def incident_evidence(incident_id: str, context: ReadContext) -> dict[str, Any]:
        try:
            return {"items": workspace.incident_evidence(context, incident_id)}
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.get("/safety/cases")
    def list_safety_cases(context: ReadContext, limit: int = 100) -> dict[str, Any]:
        return {"items": workspace.list_safety_cases(context, limit=limit), "generated_at": workspace.overview(context)["generated_at"]}

    @router.get("/safety/cases/{case_id}")
    def get_safety_case(case_id: str, context: ReadContext) -> dict[str, Any]:
        try:
            return workspace.get_safety_case(context, case_id)
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.post("/safety/cases/{case_id}/assign")
    def assign_safety_case(case_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            return workspace.assign_safety_case(context, case_id, payload, _request_meta(context, request))
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.post("/safety/cases/{case_id}/escalate")
    def escalate_safety_case(case_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            return workspace.escalate_safety_case(context, case_id, payload, _request_meta(context, request))
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.post("/safety/cases/{case_id}/timeline")
    def append_safety_timeline(case_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            authorized_case = workspace.get_safety_case(context, case_id)
            case = workspace.safety_cases[authorized_case["case_id"]]
            workspace._store_timeline(
                case,
                event_type=str(payload.get("event_type", "case_note")),
                actor_id=context.subject_id,
                request_id=_request_meta(context, request)["request_id"],
                trace_id=_request_meta(context, request)["trace_id"],
                correlation_id=_request_meta(context, request)["correlation_id"],
                message=str(payload.get("message", "")),
                payload=dict(payload),
            )
            workspace._create_evidence(safety_case=case, request_meta=_request_meta(context, request))
            return {"case_id": case.case_id, "timeline": workspace.timeline_safety_case(context, case_id)}
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.post("/safety/cases/{case_id}/resolve")
    def resolve_safety_case(case_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            return workspace.resolve_safety_case(context, case_id, payload, _request_meta(context, request))
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.get("/safety/cases/{case_id}/evidence")
    def safety_case_evidence(case_id: str, context: ReadContext) -> dict[str, Any]:
        try:
            return {"items": workspace.safety_case_evidence(context, case_id)}
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.get("/support/cases")
    def list_support_cases(
        context: ReadContext,
        limit: int = 100,
        trip_id: str | None = None,
        rider_id: str | None = None,
        driver_id: str | None = None,
        payment_id: str | None = None,
        receipt_id: str | None = None,
        case_id: str | None = None,
        phone: str | None = None,
        email: str | None = None,
    ) -> dict[str, Any]:
        if (phone or email) and not context.roles.intersection({"PLATFORM_ADMIN", "SUPPORT_SUPERVISOR"}):
            raise HTTPException(status_code=403, detail="sensitive_search_permission_required")
        query = {
            "trip_id": trip_id,
            "rider_id": rider_id,
            "driver_id": driver_id,
            "payment_id": payment_id,
            "receipt_id": receipt_id,
            "case_id": case_id,
            "phone": phone,
            "email": email,
        }
        return {"items": workspace.list_support_cases(context, query=query, limit=limit), "generated_at": workspace.overview(context)["generated_at"]}

    @router.post("/support/cases", status_code=201)
    def create_support_case(payload: CasePayload, request: Request, context: ManageContext, idempotency_key: str = Header(default="", alias="Idempotency-Key")) -> dict[str, Any]:
        try:
            return workspace.create_support_case(
                context,
                payload.model_dump(exclude_none=True) | {"idempotency_key": idempotency_key},
                _request_meta(context, request),
            )
        except ValueError as exc:
            if str(exc) == "idempotency_conflict":
                raise _raise_conflict(exc) from exc
            raise _raise_bad_request(exc) from exc

    @router.get("/support/cases/{case_id}")
    def get_support_case(case_id: str, context: ReadContext) -> dict[str, Any]:
        try:
            return workspace.get_support_case(context, case_id)
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.patch("/support/cases/{case_id}")
    def patch_support_case(case_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            return workspace.patch_support_case(context, case_id, payload, _request_meta(context, request))
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.post("/support/cases/{case_id}/assign")
    def assign_support_case(case_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            return workspace.assign_support_case(context, case_id, payload, _request_meta(context, request))
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.post("/support/cases/{case_id}/escalate")
    def escalate_support_case(case_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            return workspace.escalate_support_case(context, case_id, payload, _request_meta(context, request))
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.post("/support/cases/{case_id}/resolve")
    def resolve_support_case(case_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            return workspace.resolve_support_case(context, case_id, payload, _request_meta(context, request))
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.get("/support/cases/{case_id}/timeline")
    def support_timeline(case_id: str, context: ReadContext) -> dict[str, Any]:
        try:
            return {"items": workspace.support_case_timeline(context, case_id)}
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.get("/support/cases/{case_id}/evidence")
    def support_evidence(case_id: str, context: ReadContext) -> dict[str, Any]:
        try:
            return {"items": workspace.support_case_evidence(context, case_id)}
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.get("/refunds")
    def list_refunds(context: ReadContext, limit: int = 100) -> dict[str, Any]:
        return {"items": workspace.list_refunds(context, limit=limit), "generated_at": workspace.overview(context)["generated_at"]}

    @router.post("/refunds", status_code=201)
    def create_refund(payload: RefundPayload, request: Request, context: ManageContext, idempotency_key: str = Header(default="", alias="Idempotency-Key")) -> dict[str, Any]:
        try:
            return workspace.create_refund(
                context,
                payload.model_dump(exclude_none=True) | {"idempotency_key": idempotency_key},
                _request_meta(context, request),
            )
        except ValueError as exc:
            if str(exc) == "idempotency_conflict":
                raise _raise_conflict(exc) from exc
            raise _raise_bad_request(exc) from exc

    @router.get("/refunds/{refund_id}")
    def get_refund(refund_id: str, context: ReadContext) -> dict[str, Any]:
        try:
            return workspace.get_refund(context, refund_id)
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.post("/refunds/{refund_id}/evaluate")
    def evaluate_refund(refund_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            return workspace.evaluate_refund(context, refund_id, payload, _request_meta(context, request))
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.post("/refunds/{refund_id}/approval-requests")
    def request_refund_approval(refund_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            return workspace.request_refund_approval(context, refund_id, payload, _request_meta(context, request))
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.post("/refunds/{refund_id}/approve")
    def approve_refund(refund_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            return workspace.approve_refund(context, refund_id, payload, _request_meta(context, request))
        except KeyError as exc:
            raise _raise_not_found(exc) from exc
        except AuthorityDenied as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise _raise_bad_request(exc) from exc

    @router.post("/refunds/{refund_id}/reject")
    def reject_refund(refund_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            return workspace.reject_refund(context, refund_id, payload, _request_meta(context, request))
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.post("/refunds/{refund_id}/execute")
    def execute_refund(refund_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            return workspace.execute_refund(context, refund_id, payload, _request_meta(context, request))
        except KeyError as exc:
            raise _raise_not_found(exc) from exc
        except ValueError as exc:
            raise _raise_bad_request(exc) from exc

    @router.get("/refunds/{refund_id}/evidence")
    def refund_evidence(refund_id: str, context: ReadContext) -> dict[str, Any]:
        try:
            return {"items": workspace.refund_evidence(context, refund_id)}
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.get("/payments/investigations")
    def list_payment_investigations(context: ReadContext, limit: int = 100) -> dict[str, Any]:
        return {"items": workspace.list_payment_investigations(context, limit=limit), "generated_at": workspace.overview(context)["generated_at"]}

    @router.get("/payments/investigations/{investigation_id}")
    def get_payment_investigation(investigation_id: str, context: ReadContext) -> dict[str, Any]:
        try:
            return workspace.get_payment_investigation(context, investigation_id)
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.post("/payments/investigations", status_code=201)
    def create_payment_investigation(
        payload: InvestigationPayload,
        request: Request,
        context: ManageContext,
        idempotency_key: str = Header(default="", alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        try:
            return workspace.create_payment_investigation(
                context,
                payload.model_dump(exclude_none=True) | {"idempotency_key": idempotency_key},
                _request_meta(context, request),
            )
        except ValueError as exc:
            if str(exc) == "idempotency_conflict":
                raise _raise_conflict(exc) from exc
            raise _raise_bad_request(exc) from exc

    @router.get("/disputes")
    def list_disputes(context: ReadContext, limit: int = 100) -> dict[str, Any]:
        return {"items": workspace.list_disputes(context, limit=limit), "generated_at": workspace.overview(context)["generated_at"]}

    @router.get("/disputes/{dispute_id}")
    def get_dispute(dispute_id: str, context: ReadContext) -> dict[str, Any]:
        try:
            return workspace.get_dispute(context, dispute_id)
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.post("/disputes", status_code=201)
    def create_dispute(
        payload: DisputePayload,
        request: Request,
        context: ManageContext,
        idempotency_key: str = Header(default="", alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        try:
            return workspace.create_dispute(
                context,
                payload.model_dump(exclude_none=True) | {"idempotency_key": idempotency_key},
                _request_meta(context, request),
            )
        except ValueError as exc:
            if str(exc) == "idempotency_conflict":
                raise _raise_conflict(exc) from exc
            raise _raise_bad_request(exc) from exc

    @router.post("/disputes/{dispute_id}/assign")
    def assign_dispute(dispute_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            return workspace.assign_dispute(context, dispute_id, payload, _request_meta(context, request))
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.post("/disputes/{dispute_id}/request-evidence")
    def request_dispute_evidence(dispute_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            return workspace.request_dispute_evidence(context, dispute_id, payload, _request_meta(context, request))
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.post("/disputes/{dispute_id}/decide")
    def decide_dispute(dispute_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            return workspace.decide_dispute(context, dispute_id, payload, _request_meta(context, request))
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.post("/disputes/{dispute_id}/appeal")
    def appeal_dispute(dispute_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            return workspace.appeal_dispute(context, dispute_id, payload, _request_meta(context, request))
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.get("/actions")
    def list_actions(context: ReadContext, limit: int = 100) -> dict[str, Any]:
        return {"items": workspace.list_actions(context, limit=limit), "generated_at": workspace.overview(context)["generated_at"]}

    def _workflow_items(context: ReadContext, action_type: str, limit: int) -> dict[str, Any]:
        items = [item for item in workspace.list_actions(context, limit=1000) if item["action_type"] == action_type]
        return {"items": items[:limit], "generated_at": workspace.overview(context)["generated_at"]}

    @router.get("/pricing")
    def list_pricing_changes(context: ReadContext, limit: int = 100) -> dict[str, Any]:
        return _workflow_items(context, "update_pricing_policy", limit)

    @router.post("/pricing", status_code=201)
    def request_pricing_change(payload: PricingPayload, request: Request, context: ManageContext, idempotency_key: str = Header(default="", alias="Idempotency-Key")) -> dict[str, Any]:
        return workspace.create_action(context, {
            "action_type": "update_pricing_policy", "target_id": payload.policy_id,
            "reason": payload.reason, "risk_level": "high", "approval_required": True,
            "approval_reference": payload.approval_reference, "idempotency_key": idempotency_key,
        }, _request_meta(context, request))

    @router.get("/notifications")
    def list_notifications(context: ReadContext, limit: int = 100) -> dict[str, Any]:
        return _workflow_items(context, "send_governed_notification", limit)

    @router.post("/notifications", status_code=201)
    def request_notification(payload: NotificationPayload, request: Request, context: ManageContext, idempotency_key: str = Header(default="", alias="Idempotency-Key")) -> dict[str, Any]:
        return workspace.create_action(context, {
            "action_type": "send_governed_notification", "target_id": payload.audience,
            "reason": payload.message, "risk_level": "medium", "approval_required": True,
            "idempotency_key": idempotency_key,
        }, _request_meta(context, request))

    @router.get("/handover")
    def list_handovers(context: ReadContext, limit: int = 100) -> dict[str, Any]:
        return _workflow_items(context, "record_shift_handover", limit)

    @router.post("/handover", status_code=201)
    def record_handover(payload: HandoverPayload, request: Request, context: ManageContext, idempotency_key: str = Header(default="", alias="Idempotency-Key")) -> dict[str, Any]:
        return workspace.create_action(context, {
            "action_type": "record_shift_handover", "target_id": payload.incoming_operator_id,
            "reason": payload.summary, "risk_level": "low", "approval_required": False,
            "idempotency_key": idempotency_key,
        }, _request_meta(context, request))

    @router.post("/actions", status_code=201)
    def create_action(payload: ActionPayload, request: Request, context: ManageContext, idempotency_key: str = Header(default="", alias="Idempotency-Key")) -> dict[str, Any]:
        try:
            return workspace.create_action(
                context,
                payload.model_dump(exclude_none=True) | {"idempotency_key": idempotency_key},
                _request_meta(context, request),
            )
        except ValueError as exc:
            if str(exc) == "idempotency_conflict":
                raise _raise_conflict(exc) from exc
            raise _raise_bad_request(exc) from exc

    @router.get("/actions/{action_id}")
    def get_action(action_id: str, context: ReadContext) -> dict[str, Any]:
        try:
            return workspace.get_action(context, action_id)
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.post("/actions/{action_id}/evaluate")
    def evaluate_action(action_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            return workspace.evaluate_action(context, action_id, payload, _request_meta(context, request))
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.post("/actions/{action_id}/approve")
    def approve_action(action_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            return workspace.approve_action(context, action_id, payload, _request_meta(context, request))
        except KeyError as exc:
            raise _raise_not_found(exc) from exc
        except AuthorityDenied as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise _raise_bad_request(exc) from exc

    @router.post("/actions/{action_id}/reject")
    def reject_action(action_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            return workspace.reject_action(context, action_id, payload, _request_meta(context, request))
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.post("/actions/{action_id}/execute")
    def execute_action(action_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            return workspace.execute_action(context, action_id, payload, _request_meta(context, request))
        except KeyError as exc:
            raise _raise_not_found(exc) from exc
        except ValueError as exc:
            raise _raise_bad_request(exc) from exc

    @router.post("/actions/{action_id}/verify")
    def verify_action(action_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            return workspace.verify_action(context, action_id, payload, _request_meta(context, request))
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.post("/actions/{action_id}/cancel")
    def cancel_action(action_id: str, payload: dict[str, Any], request: Request, context: ManageContext) -> dict[str, Any]:
        try:
            return workspace.cancel_action(context, action_id, payload, _request_meta(context, request))
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.get("/actions/{action_id}/evidence")
    def action_evidence(action_id: str, context: ReadContext) -> dict[str, Any]:
        try:
            return {"items": workspace.action_evidence(context, action_id)}
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.get("/evidence")
    def list_evidence(context: ReadContext, limit: int = 100) -> dict[str, Any]:
        return {"items": workspace.list_evidence(context, limit=limit), "generated_at": workspace.overview(context)["generated_at"]}

    @router.get("/evidence/{evidence_id}")
    def get_evidence(evidence_id: str, context: ReadContext) -> dict[str, Any]:
        try:
            return workspace.get_evidence(context, evidence_id)
        except KeyError as exc:
            raise _raise_not_found(exc) from exc

    @router.get("/trips/{trip_id}/evidence")
    def trip_evidence(trip_id: str, context: ReadContext) -> dict[str, Any]:
        return {"items": workspace.trip_evidence(context, trip_id)}

    @router.get("/cases/{case_id}/evidence")
    def case_evidence(case_id: str, context: ReadContext) -> dict[str, Any]:
        return {"items": workspace.case_evidence(context, case_id)}

    @router.get("/audit")
    def audit(context: ReadContext) -> dict[str, Any]:
        overview = workspace.overview(context)
        return {
            "generated_at": overview["generated_at"],
            "items": overview["recent_activity"],
            "dependencies": overview["dependencies"],
        }

    @router.post("/bootstrap")
    def bootstrap_fixture(context: ManageContext) -> dict[str, Any]:
        return workspace.seed_browser_fixture(context)

    return router


__all__ = ["build_novaride_operations_router", "OperationsWorkspaceService"]
