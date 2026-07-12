from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DemoEnvironmentGuard:
    """Central demo safety guard for prohibiting real-world side effects."""

    realm: str = "novatech-enterprise-demo"

    PROHIBITED = {
        "production.deploy",
        "real.payment",
        "external.email",
        "external.sms",
        "real.cloud.create",
        "real.secret.access",
        "policy.override",
        "risk.accept",
        "board.vote",
    }

    def enforce(self, action: str) -> dict[str, str]:
        if action in self.PROHIBITED:
            return {
                "status": "blocked",
                "code": "demo_environment_restriction",
                "realm": self.realm,
                "action": action,
            }
        return {"status": "allowed", "realm": self.realm, "action": action}

