"""Shared execution pipeline for governed API endpoints."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any
import hashlib
import json

from .audit import AuditEvent, AuditRecorder
from .authentication import ApiPrincipal
from .authorization import AuthorizationPolicy
from .contracts import ApiEndpointDefinition, NovaTechProductApi
from .evidence import EvidenceRecord, EvidenceStore
from .errors import ApiIdempotencyError, ApiRegistrationError, ApiValidationError
from .idempotency import IdempotencyStore
from .policy import PolicyEvaluator
from .rate_limiting import RateLimiter
from .request_context import RequestContext
from .tenancy import require_tenant
from .telemetry import TelemetryRecorder
from .validation import SchemaRegistry


def _sha(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True, slots=True)
class ApiExecutionResult:
    endpoint_id: str
    product_code: str
    operation_id: str
    result: Any
    evidence_id: str | None
    audit_action: str
    idempotency_key: str | None


class ApiExecutionPipeline:
    def __init__(
        self,
        *,
        schema_registry: SchemaRegistry | None = None,
        authorization_policy: AuthorizationPolicy | None = None,
        policy_evaluator: PolicyEvaluator | None = None,
        rate_limiter: RateLimiter | None = None,
        idempotency_store: IdempotencyStore | None = None,
        audit_recorder: AuditRecorder | None = None,
        evidence_store: EvidenceStore | None = None,
        telemetry: TelemetryRecorder | None = None,
    ) -> None:
        self.schema_registry = schema_registry or SchemaRegistry()
        self.authorization_policy = authorization_policy or AuthorizationPolicy()
        self.policy_evaluator = policy_evaluator or PolicyEvaluator()
        self.rate_limiter = rate_limiter or RateLimiter()
        self.idempotency_store = idempotency_store or IdempotencyStore()
        self.audit_recorder = audit_recorder or AuditRecorder()
        self.evidence_store = evidence_store or EvidenceStore()
        self.telemetry = telemetry or TelemetryRecorder()

    async def execute(
        self,
        *,
        definition: ApiEndpointDefinition,
        payload: Mapping[str, Any],
        context: RequestContext,
        product_api: NovaTechProductApi,
    ) -> ApiExecutionResult:
        require_tenant(context)
        self.authorization_policy.authorize(definition, context)
        policy = self.policy_evaluator.evaluate(
            definition.policy_code,
            context=context.canonical_dict(),
            definition=asdict(definition),
        )
        if not policy.allowed:
            raise ApiValidationError(policy.reason or policy.code)
        self.rate_limiter.enforce(definition.rate_limit_policy)
        self.schema_registry.validate(definition.request_schema, payload)
        idempotency_key = context.extra.get("idempotency_key") if isinstance(context.extra, Mapping) else None
        if definition.idempotency_required and not idempotency_key:
            raise ApiIdempotencyError("idempotency_key_required")
        if idempotency_key:
            existing = self.idempotency_store.get(f"{definition.endpoint_id}:{idempotency_key}")
            request_hash = _sha({"payload": payload, "context": context.canonical_dict(), "endpoint": definition.endpoint_id})
            if existing is not None:
                if existing.request_hash != request_hash:
                    raise ApiIdempotencyError("idempotency_payload_conflict")
                return existing.response
        handler_result = await self._invoke(product_api, definition, payload, context)
        if definition.response_schema:
            self.schema_registry.validate(definition.response_schema, handler_result if isinstance(handler_result, Mapping) else {"value": handler_result})
        evidence: EvidenceRecord | None = None
        if definition.evidence_required:
            evidence = self.evidence_store.record(
                product_code=definition.product_code,
                endpoint_id=definition.endpoint_id,
                request_id=context.request_id,
                correlation_id=context.correlation_id,
                payload={"request": dict(payload), "result": handler_result, "context": context.canonical_dict()},
                metadata={"operation_id": definition.operation_id},
            )
        self.audit_recorder.record(
            AuditEvent(
                action=definition.operation_id,
                product_code=definition.product_code,
                endpoint_id=definition.endpoint_id,
                request_id=context.request_id,
                correlation_id=context.correlation_id,
                actor_id=context.actor_id,
                metadata={"audience": definition.audience, "purpose": definition.purpose},
            )
        )
        self.telemetry.increment("api_endpoint_request_total")
        if idempotency_key:
            self.idempotency_store.put(
                f"{definition.endpoint_id}:{idempotency_key}",
                _sha({"payload": payload, "context": context.canonical_dict(), "endpoint": definition.endpoint_id}),
                ApiExecutionResult(
                    endpoint_id=definition.endpoint_id,
                    product_code=definition.product_code,
                    operation_id=definition.operation_id,
                    result=handler_result,
                    evidence_id=evidence.evidence_id if evidence else None,
                    audit_action=definition.operation_id,
                    idempotency_key=idempotency_key,
                ),
            )
        return ApiExecutionResult(
            endpoint_id=definition.endpoint_id,
            product_code=definition.product_code,
            operation_id=definition.operation_id,
            result=handler_result,
            evidence_id=evidence.evidence_id if evidence else None,
            audit_action=definition.operation_id,
            idempotency_key=idempotency_key,
        )

    async def _invoke(self, product_api: NovaTechProductApi, definition: ApiEndpointDefinition, payload: Mapping[str, Any], context: RequestContext) -> Any:
        if definition.command_name:
            handler = product_api.command_handlers().get(definition.command_name)
            if handler is None:
                raise ApiRegistrationError(f"unknown command: {definition.command_name}")
            result = handler(payload, context)
        elif definition.query_name:
            handler = product_api.query_handlers().get(definition.query_name)
            if handler is None:
                raise ApiRegistrationError(f"unknown query: {definition.query_name}")
            result = handler(payload, context)
        else:
            handler_name = definition.handler_name or definition.operation_id
            handler = product_api.direct_handlers().get(handler_name)
            if handler is None:
                raise ApiRegistrationError(f"unknown handler: {handler_name}")
            result = handler(payload, context)
        if hasattr(result, "__await__"):
            return await result
        return result
