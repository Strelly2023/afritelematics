from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from time import perf_counter
from typing import Any, Iterator
from uuid import uuid4

from afritech.afriprogramming.persistence import PlatformStore, get_platform_store
from afritech.afriprogramming.v9.schema import ensure_v9_schema


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _stable_json(payload: dict[str, Any]) -> str:
    import json

    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _hash(payload: dict[str, Any]) -> str:
    return sha256(_stable_json(payload).encode("utf-8")).hexdigest()


try:  # pragma: no cover - optional dependency
    from opentelemetry import trace as _otel_trace  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    _otel_trace = None


@dataclass(frozen=True)
class TraceSpanRecord:
    span_id: str
    trace_id: str
    parent_span_id: str | None
    organization_id: str
    actor_user_id: str
    operation_name: str
    endpoint: str
    latency_ms: int
    status_code: int
    policy_decision_id: str | None
    proof_hash: str | None
    deployment_id: str | None
    attributes: dict[str, Any]
    created_at: str


class OpenTelemetryTracingService:
    """OTel-compatible span recorder with persistence."""

    def __init__(self, repository: PlatformStore | None = None) -> None:
        self.repository = repository or get_platform_store()
        ensure_v9_schema(self.repository)

    def record_span(
        self,
        *,
        organization_id: str,
        actor_user_id: str,
        operation_name: str,
        endpoint: str,
        latency_ms: int,
        status_code: int,
        policy_decision_id: str | None = None,
        proof_hash: str | None = None,
        deployment_id: str | None = None,
        parent_span_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        attributes = attributes or {}
        trace_id = _hash(
            {
                "organization_id": organization_id,
                "actor_user_id": actor_user_id,
                "operation_name": operation_name,
                "endpoint": endpoint,
                "policy_decision_id": policy_decision_id,
                "proof_hash": proof_hash,
                "deployment_id": deployment_id,
                "created_at": _now(),
            }
        )
        span_id = uuid4().hex[:16]
        record = TraceSpanRecord(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            operation_name=operation_name,
            endpoint=endpoint,
            latency_ms=int(latency_ms),
            status_code=int(status_code),
            policy_decision_id=policy_decision_id,
            proof_hash=proof_hash,
            deployment_id=deployment_id,
            attributes=attributes,
            created_at=_now(),
        )
        with self.repository._connect() as conn:  # noqa: SLF001 - repository boundary shim
            conn.execute(
                """
                INSERT INTO trace_spans (
                    span_id, trace_id, parent_span_id, organization_id,
                    actor_user_id, operation_name, endpoint, latency_ms,
                    status_code, policy_decision_id, proof_hash, deployment_id,
                    attributes_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.span_id,
                    record.trace_id,
                    record.parent_span_id,
                    record.organization_id,
                    record.actor_user_id,
                    record.operation_name,
                    record.endpoint,
                    record.latency_ms,
                    record.status_code,
                    record.policy_decision_id,
                    record.proof_hash,
                    record.deployment_id,
                    _stable_json(record.attributes),
                    record.created_at,
                ),
            )
            conn.commit()
        return {
            "span_id": record.span_id,
            "trace_id": record.trace_id,
            "parent_span_id": record.parent_span_id,
            "organization_id": record.organization_id,
            "actor_user_id": record.actor_user_id,
            "operation_name": record.operation_name,
            "endpoint": record.endpoint,
            "latency_ms": record.latency_ms,
            "status_code": record.status_code,
            "policy_decision_id": record.policy_decision_id,
            "proof_hash": record.proof_hash,
            "deployment_id": record.deployment_id,
            "attributes": record.attributes,
            "created_at": record.created_at,
        }

    def spans(self, organization_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        query = "SELECT * FROM trace_spans"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self.repository._connect() as conn:  # noqa: SLF001 - repository boundary shim
            rows = conn.execute(query, params).fetchall()
        return [
            {
                "span_id": row["span_id"],
                "trace_id": row["trace_id"],
                "parent_span_id": row["parent_span_id"],
                "organization_id": row["organization_id"],
                "actor_user_id": row["actor_user_id"],
                "operation_name": row["operation_name"],
                "endpoint": row["endpoint"],
                "latency_ms": row["latency_ms"],
                "status_code": row["status_code"],
                "policy_decision_id": row["policy_decision_id"],
                "proof_hash": row["proof_hash"],
                "deployment_id": row["deployment_id"],
                "attributes": json.loads(row["attributes_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    @contextmanager
    def span(
        self,
        *,
        organization_id: str,
        actor_user_id: str,
        operation_name: str,
        endpoint: str,
        policy_decision_id: str | None = None,
        proof_hash: str | None = None,
        deployment_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Iterator[dict[str, Any]]:
        started = perf_counter()
        span_id = uuid4().hex[:16]
        trace_id = _hash(
            {
                "organization_id": organization_id,
                "actor_user_id": actor_user_id,
                "operation_name": operation_name,
                "endpoint": endpoint,
                "span_id": span_id,
            }
        )
        try:
            yield {
                "span_id": span_id,
                "trace_id": trace_id,
                "parent_span_id": None,
            }
            status_code = 200
        except Exception:
            status_code = 500
            raise
        finally:
            latency_ms = int(round((perf_counter() - started) * 1000))
            self.record_span(
                organization_id=organization_id,
                actor_user_id=actor_user_id,
                operation_name=operation_name,
                endpoint=endpoint,
                latency_ms=latency_ms,
                status_code=status_code,
                policy_decision_id=policy_decision_id,
                proof_hash=proof_hash,
                deployment_id=deployment_id,
                parent_span_id=None,
                attributes=attributes,
            )

    def trace_http_request(
        self,
        *,
        organization_id: str,
        actor_user_id: str,
        operation_name: str | None = None,
        endpoint: str,
        method: str,
        status_code: int,
        latency_ms: int,
        policy_decision_id: str | None = None,
        proof_hash: str | None = None,
        deployment_id: str | None = None,
        parent_span_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        otel_span = None
        if _otel_trace is not None:  # pragma: no cover - optional dependency
            tracer = _otel_trace.get_tracer(__name__)
            span_name = operation_name or f"{method.upper()} {endpoint}"
            with tracer.start_as_current_span(span_name) as current:
                current.set_attribute("organization_id", organization_id)
                current.set_attribute("actor_user_id", actor_user_id)
                current.set_attribute("endpoint", endpoint)
                current.set_attribute("status_code", int(status_code))
                current.set_attribute("latency_ms", int(latency_ms))
                otel_span = current
        record = self.record_span(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            operation_name=operation_name or f"{method.upper()} {endpoint}",
            endpoint=endpoint,
            latency_ms=latency_ms,
            status_code=status_code,
            policy_decision_id=policy_decision_id,
            proof_hash=proof_hash,
            deployment_id=deployment_id,
            parent_span_id=parent_span_id,
            attributes=attributes or {},
        )
        if otel_span is not None:  # pragma: no cover - optional dependency
            record["otel_instrumented"] = True
        return record


__all__ = ["OpenTelemetryTracingService", "TraceSpanRecord"]
