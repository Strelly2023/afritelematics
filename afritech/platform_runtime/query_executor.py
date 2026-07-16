"""Dynamic query execution for NovaTech product runtimes."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from .errors import ProductExecutionDenied
from .models import ExecutionContext, LoadedProduct, QueryResult
from .runtime_evidence import RuntimeEvidenceService


class ProductQueryExecutor:
    def __init__(self, evidence_service: RuntimeEvidenceService | None = None) -> None:
        self.evidence_service = evidence_service or RuntimeEvidenceService()

    async def execute(
        self,
        *,
        product_code: str,
        query_name: str,
        parameters: Mapping[str, Any],
        context: ExecutionContext,
        loaded_product: LoadedProduct | None = None,
    ) -> QueryResult:
        if context.tenant_id.strip() == "":
            raise ProductExecutionDenied("tenant_context_required")
        if loaded_product is None or loaded_product.state not in {"LOADED", "RUNNING", "DEGRADED"}:
            raise ProductExecutionDenied("product_not_active")
        handler = loaded_product.queries.get(query_name)
        if handler is None:
            raise KeyError(f"unknown query: {query_name}")
        started = datetime.now(timezone.utc)
        result = handler(parameters, context)
        if hasattr(result, "__await__"):
            result = await result
        evidence = self.evidence_service.record(
            product_code=product_code,
            version=loaded_product.version,
            environment=context.environment,
            region=context.region,
            operation=query_name,
            actor_id=context.actor_id,
            approval_id="",
            correlation_id=context.correlation_id,
            inputs={"parameters": dict(parameters), "context": context.canonical_dict()},
            result={"result": result},
            module_checksum=loaded_product.module_checksum,
            configuration_checksum="sha256:query",
            infrastructure_checksum="sha256:query",
        )
        return QueryResult(
            success=True,
            product_code=product_code,
            operation=query_name,
            result=result,
            audit_id=f"audit-{product_code}-{query_name}",
            evidence_id=evidence.evidence_id,
            request_id=context.request_id,
            correlation_id=context.correlation_id,
            duration_ms=(datetime.now(timezone.utc) - started).total_seconds() * 1000.0,
        )


__all__ = ["ProductQueryExecutor"]
