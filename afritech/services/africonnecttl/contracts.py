from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthorityBoundary:
    surface: str
    status: str
    operational_proof: str
    field_execution: str
    live_deployment: str
    allowed_claims: tuple[str, ...]
    forbidden_claims: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "surface": self.surface,
            "status": self.status,
            "operational_proof": self.operational_proof,
            "field_execution": self.field_execution,
            "live_deployment": self.live_deployment,
            "allowed_claims": list(self.allowed_claims),
            "forbidden_claims": list(self.forbidden_claims),
        }


AUTHORITY_BOUNDARY = AuthorityBoundary(
    surface="AfriConnectTL",
    status="PLANNED",
    operational_proof="NONE",
    field_execution="NONE",
    live_deployment="FORBIDDEN",
    allowed_claims=(
        "future_surface",
        "architecture_design",
        "code_module_implementation",
        "controlled_simulation",
        "internal_rehearsal",
    ),
    forbidden_claims=(
        "live_deployment",
        "production_readiness",
        "real_world_reliability",
        "autonomous_logistics_system",
    ),
)


def assert_claim_allowed(claim: str) -> None:
    normalized = claim.strip().lower().replace(" ", "_").replace("-", "_")
    forbidden = {item.lower() for item in AUTHORITY_BOUNDARY.forbidden_claims}
    if normalized in forbidden:
        raise RuntimeError(
            f"AfriConnectTL authority boundary forbids claim: {claim}"
        )
