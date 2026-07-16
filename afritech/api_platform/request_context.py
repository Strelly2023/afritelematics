"""Request context for governed API execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping
import uuid


@dataclass(frozen=True, slots=True)
class RequestContext:
    request_id: str
    correlation_id: str
    trace_id: str
    product_code: str
    tenant_id: str
    organization_id: str
    actor_id: str
    audience: str
    roles: tuple[str, ...]
    permissions: tuple[str, ...]
    environment: str = "production"
    region: str = "AU"
    purpose: str = ""
    session_id: str | None = None
    device_id: str | None = None
    extra: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_headers(cls, product_code: str, headers: Mapping[str, str], *, audience: str = "INTERNAL") -> "RequestContext":
        tenant_id = headers.get("x-novatech-tenant-id", "").strip()
        organization_id = headers.get("x-novatech-organization-id", "").strip()
        actor_id = headers.get("x-novatech-actor-id", "").strip()
        roles = tuple(filter(None, (item.strip() for item in headers.get("x-novatech-roles", "").split(","))))
        permissions = tuple(filter(None, (item.strip() for item in headers.get("x-novatech-permissions", "").split(","))))
        return cls(
            request_id=headers.get("x-request-id", f"req-{uuid.uuid4().hex[:12]}"),
            correlation_id=headers.get("x-correlation-id", f"corr-{uuid.uuid4().hex[:12]}"),
            trace_id=headers.get("x-trace-id", f"trace-{uuid.uuid4().hex[:12]}"),
            product_code=product_code,
            tenant_id=tenant_id,
            organization_id=organization_id,
            actor_id=actor_id,
            audience=audience,
            roles=roles,
            permissions=permissions,
            purpose=headers.get("x-purpose", ""),
            session_id=headers.get("x-session-id"),
            device_id=headers.get("x-device-id"),
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "trace_id": self.trace_id,
            "product_code": self.product_code,
            "tenant_id": self.tenant_id,
            "organization_id": self.organization_id,
            "actor_id": self.actor_id,
            "audience": self.audience,
            "roles": list(self.roles),
            "permissions": list(self.permissions),
            "environment": self.environment,
            "region": self.region,
            "purpose": self.purpose,
            "session_id": self.session_id,
            "device_id": self.device_id,
            "extra": dict(self.extra),
        }
