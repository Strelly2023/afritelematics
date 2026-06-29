"""Runtime NovaRide schema registry API surface."""

from __future__ import annotations

from collections.abc import Mapping
from functools import lru_cache
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from afritech.api.auth.jwt_device_auth import require_roles
from afritech.platform_contracts.schema_registry import (
    CompatibilityReport,
    SchemaRegistry,
    SchemaRegistryError,
    build_schema_catalog,
    build_schema_registry,
)


class EventValidationRequest(BaseModel):
    event: dict[str, Any] | None = None
    events: list[dict[str, Any]] | None = None

    class Config:
        extra = "allow"


class CompatibilityRequest(BaseModel):
    previous_event_type: str = Field(min_length=1)
    current_event_type: str = Field(min_length=1)

    class Config:
        extra = "allow"


@lru_cache(maxsize=1)
def get_schema_registry() -> SchemaRegistry:
    return build_schema_registry()


def _registry() -> SchemaRegistry:
    return get_schema_registry()


def _coerce_validation_targets(payload: EventValidationRequest | Mapping[str, Any]) -> list[dict[str, Any]]:
    if isinstance(payload, EventValidationRequest):
        if payload.event is not None:
            return [payload.event]
        if payload.events is not None:
            return list(payload.events)
        raise HTTPException(status_code=400, detail="event_or_events_required")
    if "event" in payload and isinstance(payload["event"], Mapping):
        return [dict(payload["event"])]
    if "events" in payload and isinstance(payload["events"], list):
        return [dict(event) for event in payload["events"] if isinstance(event, Mapping)]
    if payload.get("event_type"):
        return [dict(payload)]
    raise HTTPException(status_code=400, detail="event_or_events_required")


def build_schema_registry_router() -> APIRouter:
    router = APIRouter(prefix="/v1/contracts/events", tags=["schema-registry"])

    @router.get("/registry")
    def registry(
        _: object = Depends(require_roles("OPERATOR", "ADMIN", "VERIFIER", "DEVELOPER")),
    ) -> dict[str, Any]:
        registry = _registry()
        return {
            "registry_id": registry.registry.get("registry_id"),
            "status": registry.registry.get("status"),
            "classification": registry.registry.get("classification"),
            "entries": [
                {
                    "event_type": entry.event_type,
                    "domain": entry.domain,
                    "owner_service": entry.owner_service,
                    "schema_version": entry.schema_version,
                    "compatibility": entry.compatibility,
                    "status": entry.status,
                    "partition_key_strategy": entry.partition_key_strategy,
                    "idempotency_strategy": entry.idempotency_strategy,
                    "decision_trace_required": entry.decision_trace_required,
                }
                for entry in registry.entries
            ],
        }

    @router.get("/catalog")
    def catalog(
        _: object = Depends(require_roles("OPERATOR", "ADMIN", "VERIFIER", "DEVELOPER")),
    ) -> dict[str, Any]:
        return build_schema_catalog()

    @router.get("/registry/{event_type}")
    def registry_entry(
        event_type: str,
        _: object = Depends(require_roles("OPERATOR", "ADMIN", "VERIFIER", "DEVELOPER")),
    ) -> dict[str, Any]:
        registry = _registry()
        try:
            entry = registry.lookup(event_type, allow_deprecated=True)
        except SchemaRegistryError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {
            "event_type": entry.event_type,
            "domain": entry.domain,
            "owner_service": entry.owner_service,
            "schema_version": entry.schema_version,
            "compatibility": entry.compatibility,
            "status": entry.status,
            "partition_key_strategy": entry.partition_key_strategy,
            "idempotency_strategy": entry.idempotency_strategy,
            "decision_trace_required": entry.decision_trace_required,
            "certification": registry.certification_check(event_type),
        }

    @router.get("/registry/{event_type}/schema")
    def registry_schema(
        event_type: str,
        _: object = Depends(require_roles("OPERATOR", "ADMIN", "VERIFIER", "DEVELOPER")),
    ) -> dict[str, Any]:
        registry = _registry()
        try:
            schema = registry.generate_json_schema(event_type)
        except SchemaRegistryError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {
            "event_type": event_type,
            "schema": schema,
            "schema_digest": registry.schema_digest(event_type),
            "certification": registry.certification_check(event_type),
        }

    @router.get("/registry/{event_type}/certification")
    def registry_certification(
        event_type: str,
        _: object = Depends(require_roles("OPERATOR", "ADMIN", "VERIFIER", "DEVELOPER")),
    ) -> dict[str, Any]:
        registry = _registry()
        try:
            return registry.certification_check(event_type)
        except SchemaRegistryError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/validate")
    def validate_event_contract(
        payload: EventValidationRequest,
        _: object = Depends(require_roles("OPERATOR", "ADMIN", "VERIFIER", "DEVELOPER")),
    ) -> dict[str, Any]:
        registry = _registry()
        targets = _coerce_validation_targets(payload)
        if len(targets) == 1:
            try:
                result = registry.validate_event(targets[0])
            except SchemaRegistryError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
            return {
                "all_valid": True,
            "accepted": [result],
            "rejected": [],
        }
        try:
            result = registry.validate_batch(targets)
        except SchemaRegistryError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return result

    @router.post("/publish")
    def publish_event_contract(
        request: Request,
        payload: EventValidationRequest,
        _: object = Depends(require_roles("OPERATOR", "ADMIN", "VERIFIER", "DEVELOPER")),
    ) -> dict[str, Any]:
        registry = _registry()
        admission = getattr(request.state, "novaride_contract_admission", None)
        if admission is None:
            targets = _coerce_validation_targets(payload)
            admission = registry.validate_batch(targets) if len(targets) > 1 else registry.validate_event(targets[0])
        if isinstance(admission, Mapping) and "accepted" in admission:
            return {
                "status": "admitted",
                "mode": "batch",
                "admission": admission,
            }
        return {
            "status": "admitted",
            "mode": "single",
            "admission": admission,
        }

    @router.post("/compatibility")
    def compare_compatibility(
        payload: CompatibilityRequest,
        _: object = Depends(require_roles("OPERATOR", "ADMIN", "VERIFIER", "DEVELOPER")),
    ) -> dict[str, Any]:
        registry = _registry()
        try:
            report: CompatibilityReport = registry.compatibility_report(
                payload.previous_event_type,
                payload.current_event_type,
            )
        except SchemaRegistryError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {
            "previous_event_type": payload.previous_event_type,
            "current_event_type": payload.current_event_type,
            **report.canonical(),
        }

    return router


__all__ = ["build_schema_registry_router", "get_schema_registry"]
