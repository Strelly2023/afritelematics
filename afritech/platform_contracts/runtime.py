"""Runtime vocabulary shared with the NovaTech platform contract validator."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum
import re
from typing import Iterable, Mapping


SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


class CapabilityLayer(IntEnum):
    INFRASTRUCTURE = 0
    IDENTITY = 1
    POLICY = 2
    EXECUTION = 3
    EVIDENCE = 4
    REPLAY = 5
    FEDERATION = 6
    PRODUCTS = 7


class TrustLevel(IntEnum):
    UNVERIFIED = 0
    AUTHENTICATED = 1
    POLICY_VERIFIED = 2
    EVIDENCE_PRODUCED = 3
    REPLAY_VERIFIED = 4
    FEDERATED_VERIFIED = 5
    PUBLICLY_VERIFIABLE = 6


class ProductLifecycle(str, Enum):
    CONCEPT = "CONCEPT"
    PROTOTYPE = "PROTOTYPE"
    PILOT = "PILOT"
    PRODUCTION = "PRODUCTION"
    CERTIFIED = "CERTIFIED"
    FEDERATED = "FEDERATED"
    RETIRED = "RETIRED"


class ApiLifecycle(str, Enum):
    DRAFT = "DRAFT"
    EXPERIMENTAL = "EXPERIMENTAL"
    STABLE = "STABLE"
    LTS = "LTS"
    DEPRECATED = "DEPRECATED"
    RETIRED = "RETIRED"


@dataclass(frozen=True)
class VersionVector:
    platform: str
    contract: str
    schema: str
    api: str
    replay: str
    evidence: str
    signature: str

    def __post_init__(self) -> None:
        for name, value in self.canonical().items():
            if not SEMVER.fullmatch(value):
                raise ValueError(f"{name}_version_must_be_semver")

    def canonical(self) -> dict[str, str]:
        return {
            "platform": self.platform,
            "contract": self.contract,
            "schema": self.schema,
            "api": self.api,
            "replay": self.replay,
            "evidence": self.evidence,
            "signature": self.signature,
        }


@dataclass(frozen=True)
class TrustAssessment:
    level: TrustLevel
    checks: tuple[str, ...]

    def canonical(self) -> dict[str, object]:
        return {
            "level": int(self.level),
            "name": self.level.name,
            "checks": list(self.checks),
        }


def assess_trust_level(
    *,
    authenticated: bool = False,
    policy_verified: bool = False,
    evidence_produced: bool = False,
    replay_verified: bool = False,
    federated_verified: bool = False,
    publicly_verifiable: bool = False,
) -> TrustAssessment:
    """Return the highest contiguous trust level actually supported by proof."""

    proofs = (
        ("authenticated", authenticated),
        ("policy_verified", policy_verified),
        ("evidence_produced", evidence_produced),
        ("replay_verified", replay_verified),
        ("federated_verified", federated_verified),
        ("publicly_verifiable", publicly_verifiable),
    )
    achieved = TrustLevel.UNVERIFIED
    checks: list[str] = []
    for level, (name, present) in enumerate(proofs, start=1):
        if not present:
            break
        achieved = TrustLevel(level)
        checks.append(name)
    return TrustAssessment(level=achieved, checks=tuple(checks))


def validate_capability_dependencies(
    capabilities: Iterable[Mapping[str, object]],
) -> None:
    """Fail when a capability depends on a higher, undeclared authority layer."""

    declared: dict[str, int] = {}
    dependencies: dict[str, tuple[str, ...]] = {}
    for capability in capabilities:
        identifier = str(capability.get("id", "")).strip()
        if not identifier or identifier in declared:
            raise ValueError("capability_ids_must_be_unique_and_non_empty")
        layer = int(capability.get("layer", -1))
        if layer not in {item.value for item in CapabilityLayer}:
            raise ValueError(f"invalid_capability_layer:{identifier}")
        declared[identifier] = layer
        raw_dependencies = capability.get("depends_on", ())
        if not isinstance(raw_dependencies, (list, tuple)):
            raise ValueError(f"capability_dependencies_must_be_a_list:{identifier}")
        dependencies[identifier] = tuple(str(item) for item in raw_dependencies)

    for identifier, targets in dependencies.items():
        for target in targets:
            if target not in declared:
                raise ValueError(f"unknown_capability_dependency:{identifier}:{target}")
            if declared[target] > declared[identifier]:
                raise ValueError(f"upward_capability_dependency:{identifier}:{target}")
