"""Generated from afritech/platform_contracts/platform.yaml. Do not hand-edit."""

from dataclasses import dataclass
from typing import Any


VERSION_VECTOR = {
    "platform": "2.0.0",
    "contract": "2.0.0",
    "schema": "1.0.0",
    "api": "1.0.0",
    "replay": "1.0.0",
    "evidence": "1.0.0",
    "signature": "1.0.0",
}


@dataclass(frozen=True)
class GovernedRequest:
    request_id: str
    operation: str
    tenant_id: str
    actor_id: str
    idempotency_key: str
    payload: dict[str, Any]
    contract_version: str = VERSION_VECTOR["contract"]
    schema_version: str = VERSION_VECTOR["schema"]
