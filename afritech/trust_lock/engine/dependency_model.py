"""Model external dependencies on replay-authoritative truth."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Iterable


@dataclass(frozen=True)
class ExternalDependency:
    consumer_id: str
    workflow: str
    required_evidence: tuple[str, ...]
    trust_requirement: str

    def canonical_dict(self) -> dict[str, object]:
        return {
            "consumer_id": self.consumer_id,
            "required_evidence": list(self.required_evidence),
            "trust_requirement": self.trust_requirement,
            "workflow": self.workflow,
        }


@dataclass(frozen=True)
class TrustDependencyGraph:
    dependencies: tuple[ExternalDependency, ...]

    @property
    def graph_hash(self) -> str:
        return _canonical_hash(
            [dependency.canonical_dict() for dependency in self.dependencies]
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "dependencies": [
                dependency.canonical_dict() for dependency in self.dependencies
            ],
            "graph_hash": self.graph_hash,
            "schema": "afritech.trust_dependency_graph.v1",
        }


def build_dependency_graph(
    dependencies: Iterable[ExternalDependency] | None = None,
) -> TrustDependencyGraph:
    if dependencies is None:
        dependencies = _default_dependencies()
    return TrustDependencyGraph(
        dependencies=tuple(sorted(dependencies, key=lambda item: item.consumer_id))
    )


def _default_dependencies() -> tuple[ExternalDependency, ...]:
    required = (
        "audit_hash",
        "claims_hash",
        "decisions_hash",
        "replay_authority_hash",
        "resolution_hash",
    )
    return (
        ExternalDependency(
            consumer_id="payments.settlement",
            required_evidence=required,
            trust_requirement="fare_dispute_requires_replay_authority",
            workflow="settle_authoritative_fare",
        ),
        ExternalDependency(
            consumer_id="support.disputes",
            required_evidence=required,
            trust_requirement="conflicting_claims_require_replay_resolution",
            workflow="close_driver_rider_dispute",
        ),
        ExternalDependency(
            consumer_id="partner.audit_export",
            required_evidence=required,
            trust_requirement="external_audit_requires_hash_bound_packet",
            workflow="export_dispute_audit_packet",
        ),
    )


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()

