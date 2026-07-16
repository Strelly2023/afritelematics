"""Dynamic command execution for NovaTech product runtimes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import hashlib
import json

from .errors import ProductExecutionDenied
from .models import ExecutionContext, ExecutionResult, LoadedProduct
from .runtime_evidence import RuntimeEvidenceService


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha(payload: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


@dataclass
class IdempotencyStore:
    records: dict[str, ExecutionResult]

    def get(self, key: str) -> ExecutionResult | None:
        return self.records.get(key)

    def set(self, key: str, value: ExecutionResult) -> None:
        self.records[key] = value


class ProductCommandExecutor:
    def __init__(self, evidence_service: RuntimeEvidenceService | None = None, idempotency_store: IdempotencyStore | None = None) -> None:
        self.evidence_service = evidence_service or RuntimeEvidenceService()
        self.idempotency_store = idempotency_store or IdempotencyStore(records={})

    async def execute(self, *, product_code: str, command_name: str, payload: Mapping[str, Any], context: ExecutionContext, loaded_product: LoadedProduct | None = None) -> ExecutionResult:
        if context.tenant_id.strip() == "":
            raise ProductExecutionDenied("tenant_context_required")
        if loaded_product is None or loaded_product.state not in {"LOADED", "RUNNING", "DEGRADED"}:
            raise ProductExecutionDenied("product_not_active")
        handler = loaded_product.commands.get(command_name)
        if handler is None:
            raise KeyError(f"unknown command: {command_name}")
        if context.idempotency_key:
            existing = self.idempotency_store.get(context.idempotency_key)
            if existing is not None:
                return existing
        started = datetime.now(timezone.utc)
        result = handler(payload, context)
        if hasattr(result, "__await__"):
            result = await result
        evidence = self.evidence_service.record(
            product_code=product_code,
            version=loaded_product.version,
            environment=context.environment,
            region=context.region,
            operation=command_name,
            actor_id=context.actor_id,
            approval_id="",
            correlation_id=context.correlation_id,
            inputs={"payload": dict(payload), "context": context.canonical_dict()},
            result={"result": result},
            module_checksum=loaded_product.module_checksum,
            configuration_checksum=_sha(dict(loaded_product.registration.configuration)),
            infrastructure_checksum=_sha(dict(loaded_product.registration.infrastructure)),
        )
        execution = ExecutionResult(
            success=True,
            product_code=product_code,
            operation=command_name,
            result=result,
            events=(),
            audit_id=f"audit-{_sha({'command': command_name, 'payload': dict(payload)})[:12]}",
            evidence_id=evidence.evidence_id,
            request_id=context.request_id,
            correlation_id=context.correlation_id,
            duration_ms=(datetime.now(timezone.utc) - started).total_seconds() * 1000.0,
        )
        if context.idempotency_key:
            self.idempotency_store.set(context.idempotency_key, execution)
        return execution


__all__ = ["IdempotencyStore", "ProductCommandExecutor"]
