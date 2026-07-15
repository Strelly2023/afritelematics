"""Evidence-based production readiness certificate generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from afritech.novaride_runtime.common.clocks import utc_now
from afritech.novaride_runtime.events.hashing import canonical_hash


class ReadinessStatus(StrEnum):
    NOT_READY = "NOT_READY"
    CONDITIONALLY_READY = "CONDITIONALLY_READY"
    READY_FOR_CONTROLLED_PILOT = "READY_FOR_CONTROLLED_PILOT"
    READY_FOR_PUBLIC_PILOT = "READY_FOR_PUBLIC_PILOT"
    READY_FOR_GA = "READY_FOR_GA"


@dataclass(slots=True)
class ReadinessEvidence:
    build_commit: str = "unknown"
    container_digests: tuple[str, ...] = ()
    migration_version: str = "0008_novaride_resilience_hardening"
    environment: str = "development"
    regions: tuple[str, ...] = ()
    zones: tuple[str, ...] = ()
    test_results: dict[str, str] = field(default_factory=dict)
    live_postgresql_verified: bool = False
    live_kafka_verified: bool = False
    live_kubernetes_failover_verified: bool = False
    emergency_path_verified: bool = False
    security_verified: bool = False
    accessibility_verified: bool = False
    dr_exercise_verified: bool = False
    unresolved_risks: tuple[str, ...] = ()


def generate_readiness_certificate(evidence: ReadinessEvidence) -> dict[str, Any]:
    ready_for_ga = all(
        [
            evidence.live_postgresql_verified,
            evidence.live_kafka_verified,
            evidence.live_kubernetes_failover_verified,
            evidence.emergency_path_verified,
            evidence.security_verified,
            evidence.accessibility_verified,
            evidence.dr_exercise_verified,
        ]
    ) and not evidence.unresolved_risks
    if ready_for_ga:
        status = ReadinessStatus.READY_FOR_GA
    elif evidence.test_results and evidence.emergency_path_verified:
        status = ReadinessStatus.READY_FOR_CONTROLLED_PILOT
    elif evidence.test_results:
        status = ReadinessStatus.CONDITIONALLY_READY
    else:
        status = ReadinessStatus.NOT_READY
    payload = {
        "issued_at": utc_now().isoformat(),
        "build_commit": evidence.build_commit,
        "container_digests": list(evidence.container_digests),
        "migration_version": evidence.migration_version,
        "environment": evidence.environment,
        "regions": list(evidence.regions),
        "zones": list(evidence.zones),
        "test_results": evidence.test_results,
        "live_postgresql_verified": evidence.live_postgresql_verified,
        "live_kafka_verified": evidence.live_kafka_verified,
        "live_kubernetes_failover_verified": evidence.live_kubernetes_failover_verified,
        "emergency_path_verified": evidence.emergency_path_verified,
        "security_verified": evidence.security_verified,
        "accessibility_verified": evidence.accessibility_verified,
        "dr_exercise_verified": evidence.dr_exercise_verified,
        "unresolved_risks": list(evidence.unresolved_risks),
        "final_status": status.value,
    }
    payload["evidence_hash"] = canonical_hash(payload)
    return payload
