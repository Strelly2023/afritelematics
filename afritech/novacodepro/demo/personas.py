from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any

from afritech.api.auth.jwt_device_auth import JWT


def _b64url_encode(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")


@dataclass(frozen=True)
class DemoPersona:
    sub: str
    tenant_id: str
    organization_id: str
    roles: tuple[str, ...]
    environment: str = "demo"
    demo: bool = True
    realm: str = "novatech-enterprise-demo"


DEMO_PERSONAS: tuple[DemoPersona, ...] = (
    DemoPersona("cto", "tenant-novacodepro-enterprise-demo", "org-novatech-demo", ("CTO",)),
    DemoPersona("ceo", "tenant-novacodepro-enterprise-demo", "org-novatech-demo", ("CEO",)),
    DemoPersona("coo", "tenant-novacodepro-enterprise-demo", "org-novatech-demo", ("COO",)),
    DemoPersona("cfo", "tenant-novacodepro-enterprise-demo", "org-novatech-demo", ("CFO",)),
    DemoPersona("ciso", "tenant-novacodepro-enterprise-demo", "org-novatech-demo", ("CISO",)),
    DemoPersona("board-chair", "tenant-novacodepro-enterprise-demo", "org-novatech-demo", ("ADMIN",)),
)


def build_demo_persona_token(persona: DemoPersona, *, expires_in: int = 3600, realm: str = "novatech-enterprise-demo") -> dict[str, Any]:
    if realm != "novatech-enterprise-demo":
        raise RuntimeError("persona_switcher_disabled")
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": persona.sub,
        "role": persona.roles[0],
        "organization_id": persona.organization_id,
        "tenant_id": persona.tenant_id,
        "environment": persona.environment,
        "demo": persona.demo,
        "realm": persona.realm,
        "exp": now + int(expires_in),
    }
    signing_input = ".".join(
        (
            _b64url_encode(json.dumps(header, sort_keys=True, separators=(",", ":")).encode()),
            _b64url_encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()),
        )
    )
    signature = hmac.new(JWT.secret, signing_input.encode("ascii"), hashlib.sha256).digest()
    token = f"{signing_input}.{_b64url_encode(signature)}"
    return {"token": token, "claims": payload}


def switch_demo_persona(role: str) -> dict[str, Any]:
    for persona in DEMO_PERSONAS:
        if role.upper() in persona.roles:
            return build_demo_persona_token(persona)
    raise KeyError(f"unknown demo persona: {role}")

