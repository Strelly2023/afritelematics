"""Protected NovaID audit replay APIs."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.novaid.audit_replay import (
    AuditReplayError,
    AuditReplayService,
    get_default_audit_replay_service,
)


class ReplayRequestBody(BaseModel):
    event_type_filters: list[str] = Field(default_factory=list)
    aggregate_filters: dict[str, object] = Field(default_factory=dict)
    subject_filters: dict[str, object] = Field(default_factory=dict)
    start_time: datetime | None = None
    end_time: datetime | None = None
    source_checkpoint: str | None = None
    target_checkpoint: str | None = None
    replay_mode: str = Field(default="dry_run")
    dry_run: bool = True
    reason: str = Field(min_length=3, max_length=500)
    risk_level: str = Field(default="moderate")
    maximum_events: int = Field(default=100, ge=1, le=10_000)
    correlation_id: str = Field(default="")
    request_id: str = Field(default="")


class DecisionBody(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


def _authorize(claims: JWTClaims, permission: str) -> None:
    if permission in claims.permissions or claims.role == "ADMIN":
        return
    raise HTTPException(status_code=403, detail={"code": "AUDIT_PERMISSION_DENIED"})


def _service(service: AuditReplayService | None) -> AuditReplayService:
    return service or get_default_audit_replay_service()


def build_novaid_audit_replay_router(
    service: AuditReplayService | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/audit", tags=["novaid-audit"])
    service = _service(service)

    reader = require_roles("ADMIN", "OPERATOR", "OBSERVER")
    replayer = require_roles("ADMIN", "OPERATOR")

    @router.post("/replay/requests")
    def create_replay_request(
        payload: ReplayRequestBody,
        claims: JWTClaims = Depends(replayer),
    ) -> dict[str, object]:
        _authorize(claims, "audit.replay.request")
        try:
            return service.create_request(
                tenant_id=claims.tenant_id or claims.organization_id,
                organization_id=claims.organization_id,
                requested_by=claims.sub,
                event_type_filters=payload.event_type_filters,
                aggregate_filters=payload.aggregate_filters,
                subject_filters=payload.subject_filters,
                start_time=payload.start_time,
                end_time=payload.end_time,
                source_checkpoint=payload.source_checkpoint,
                target_checkpoint=payload.target_checkpoint,
                replay_mode=payload.replay_mode,
                dry_run=payload.dry_run,
                reason=payload.reason,
                risk_level=payload.risk_level,
                maximum_events=payload.maximum_events,
                correlation_id=payload.correlation_id,
                request_id=payload.request_id,
            )
        except AuditReplayError as exc:
            raise HTTPException(status_code=400, detail={"code": str(exc)}) from None

    @router.get("/replay/requests")
    def list_replay_requests(
        claims: JWTClaims = Depends(reader), limit: int = 100
    ) -> list[dict[str, object]]:
        _authorize(claims, "audit.events.read")
        return service.list_requests(
            tenant_id=claims.tenant_id or claims.organization_id, limit=limit
        )

    @router.get("/replay/requests/{replay_request_id}")
    def get_replay_request(
        replay_request_id: str, claims: JWTClaims = Depends(reader)
    ) -> dict[str, object]:
        _authorize(claims, "audit.events.read")
        try:
            request = service.get_request(replay_request_id)
        except AuditReplayError as exc:
            raise HTTPException(status_code=404, detail={"code": str(exc)}) from None
        if request["tenant_id"] != (claims.tenant_id or claims.organization_id):
            raise HTTPException(status_code=403, detail={"code": "AUDIT_TENANT_DENIED"})
        return request

    @router.post("/replay/requests/{replay_request_id}/evaluate")
    def evaluate_replay_request(
        replay_request_id: str, claims: JWTClaims = Depends(replayer)
    ) -> dict[str, object]:
        _authorize(claims, "audit.replay.request")
        try:
            request = service.get_request(replay_request_id)
            if request["tenant_id"] != (claims.tenant_id or claims.organization_id):
                raise HTTPException(status_code=403, detail={"code": "AUDIT_TENANT_DENIED"})
            return service.evaluate(replay_request_id)
        except AuditReplayError as exc:
            raise HTTPException(status_code=404, detail={"code": str(exc)}) from None

    @router.post("/replay/requests/{replay_request_id}/approval-requests")
    def request_approval(
        replay_request_id: str,
        payload: DecisionBody,
        claims: JWTClaims = Depends(replayer),
    ) -> dict[str, object]:
        _authorize(claims, "audit.replay.approve")
        request = service.get_request(replay_request_id)
        if request["tenant_id"] != (claims.tenant_id or claims.organization_id):
            raise HTTPException(status_code=403, detail={"code": "AUDIT_TENANT_DENIED"})
        try:
            return service.request_approval(
                replay_request_id,
                requested_by=claims.sub,
                reason=payload.reason,
            )
        except AuditReplayError as exc:
            raise HTTPException(status_code=400, detail={"code": str(exc)}) from None

    @router.post("/replay/requests/{replay_request_id}/approve")
    def approve_replay_request(
        replay_request_id: str,
        payload: DecisionBody,
        claims: JWTClaims = Depends(replayer),
    ) -> dict[str, object]:
        _authorize(claims, "audit.replay.approve")
        request = service.get_request(replay_request_id)
        if request["tenant_id"] != (claims.tenant_id or claims.organization_id):
            raise HTTPException(status_code=403, detail={"code": "AUDIT_TENANT_DENIED"})
        try:
            return service.approve(replay_request_id, approver_id=claims.sub, reason=payload.reason)
        except AuditReplayError as exc:
            code = str(exc)
            if code == "self_approval_denied":
                raise HTTPException(status_code=403, detail={"code": code}) from None
            raise HTTPException(status_code=400, detail={"code": code}) from None

    @router.post("/replay/requests/{replay_request_id}/reject")
    def reject_replay_request(
        replay_request_id: str,
        payload: DecisionBody,
        claims: JWTClaims = Depends(replayer),
    ) -> dict[str, object]:
        _authorize(claims, "audit.replay.approve")
        request = service.get_request(replay_request_id)
        if request["tenant_id"] != (claims.tenant_id or claims.organization_id):
            raise HTTPException(status_code=403, detail={"code": "AUDIT_TENANT_DENIED"})
        try:
            return service.reject(replay_request_id, approver_id=claims.sub, reason=payload.reason)
        except AuditReplayError as exc:
            raise HTTPException(status_code=400, detail={"code": str(exc)}) from None

    @router.post("/replay/requests/{replay_request_id}/execute")
    def execute_replay_request(
        replay_request_id: str,
        payload: DecisionBody,
        claims: JWTClaims = Depends(replayer),
    ) -> dict[str, object]:
        _authorize(claims, "audit.replay.execute")
        request = service.get_request(replay_request_id)
        if request["tenant_id"] != (claims.tenant_id or claims.organization_id):
            raise HTTPException(status_code=403, detail={"code": "AUDIT_TENANT_DENIED"})
        try:
            return service.execute(replay_request_id, executor_id=claims.sub, reason=payload.reason)
        except AuditReplayError as exc:
            code = str(exc)
            if code == "replay_not_approved":
                raise HTTPException(status_code=403, detail={"code": code}) from None
            raise HTTPException(status_code=400, detail={"code": code}) from None

    @router.post("/replay/requests/{replay_request_id}/cancel")
    def cancel_replay_request(
        replay_request_id: str,
        payload: DecisionBody,
        claims: JWTClaims = Depends(replayer),
    ) -> dict[str, object]:
        _authorize(claims, "audit.replay.cancel")
        request = service.get_request(replay_request_id)
        if request["tenant_id"] != (claims.tenant_id or claims.organization_id):
            raise HTTPException(status_code=403, detail={"code": "AUDIT_TENANT_DENIED"})
        try:
            return service.cancel(replay_request_id, actor_id=claims.sub, reason=payload.reason)
        except AuditReplayError as exc:
            raise HTTPException(status_code=400, detail={"code": str(exc)}) from None

    @router.get("/replay/requests/{replay_request_id}/events")
    def list_replay_events(
        replay_request_id: str, claims: JWTClaims = Depends(reader)
    ) -> list[dict[str, object]]:
        _authorize(claims, "audit.events.read")
        request = service.get_request(replay_request_id)
        if request["tenant_id"] != (claims.tenant_id or claims.organization_id):
            raise HTTPException(status_code=403, detail={"code": "AUDIT_TENANT_DENIED"})
        return service.events(replay_request_id)

    @router.get("/replay/requests/{replay_request_id}/evidence")
    def replay_evidence(
        replay_request_id: str, claims: JWTClaims = Depends(reader)
    ) -> dict[str, object]:
        _authorize(claims, "audit.replay.evidence.read")
        request = service.get_request(replay_request_id)
        if request["tenant_id"] != (claims.tenant_id or claims.organization_id):
            raise HTTPException(status_code=403, detail={"code": "AUDIT_TENANT_DENIED"})
        return service.evidence(replay_request_id)

    @router.get("/checkpoints")
    def list_checkpoints(
        claims: JWTClaims = Depends(reader), limit: int = 100
    ) -> list[dict[str, object]]:
        _authorize(claims, "audit.checkpoints.read")
        return service.list_checkpoints(
            tenant_id=claims.tenant_id or claims.organization_id, limit=limit
        )

    @router.get("/dead-letters")
    def list_dead_letters(
        claims: JWTClaims = Depends(reader), limit: int = 100
    ) -> list[dict[str, object]]:
        _authorize(claims, "audit.dead_letters.read")
        return service.list_dead_letters(
            tenant_id=claims.tenant_id or claims.organization_id, limit=limit
        )

    return router
