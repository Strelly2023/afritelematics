"""Simulate replacement or removal of replay-authoritative truth."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from afritech.trust_lock.engine.dependency_model import TrustDependencyGraph
from afritech.trust_lock.engine.workflow_consumer import WorkflowResult, consume_audit_packet


@dataclass(frozen=True)
class RemovalSimulation:
    baseline_results: tuple[WorkflowResult, ...]
    removed_results: tuple[WorkflowResult, ...]
    replacement_results: tuple[WorkflowResult, ...]

    @property
    def baseline_trusted(self) -> bool:
        return all(result.accepted for result in self.baseline_results)

    @property
    def removal_breaks_workflows(self) -> bool:
        return all(not result.accepted for result in self.removed_results)

    @property
    def replacement_breaks_trust(self) -> bool:
        return all(not result.accepted for result in self.replacement_results)

    @property
    def trust_lock_verified(self) -> bool:
        return (
            self.baseline_trusted
            and self.removal_breaks_workflows
            and self.replacement_breaks_trust
        )

    @property
    def simulation_hash(self) -> str:
        return _canonical_hash(self.canonical_dict(include_hash=False))

    def canonical_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        payload = {
            "baseline_results": [
                result.canonical_dict() for result in self.baseline_results
            ],
            "baseline_trusted": self.baseline_trusted,
            "removal_breaks_workflows": self.removal_breaks_workflows,
            "removed_results": [
                result.canonical_dict() for result in self.removed_results
            ],
            "replacement_breaks_trust": self.replacement_breaks_trust,
            "replacement_results": [
                result.canonical_dict() for result in self.replacement_results
            ],
            "trust_lock_verified": self.trust_lock_verified,
        }
        if include_hash:
            payload["simulation_hash"] = self.simulation_hash
        return payload


def simulate_removal(
    graph: TrustDependencyGraph,
    audit_packet: Mapping[str, Any],
) -> RemovalSimulation:
    replacement = _replacement_packet(audit_packet)
    return RemovalSimulation(
        baseline_results=tuple(
            consume_audit_packet(dependency, audit_packet)
            for dependency in graph.dependencies
        ),
        removed_results=tuple(
            consume_audit_packet(dependency, None) for dependency in graph.dependencies
        ),
        replacement_results=tuple(
            consume_audit_packet(dependency, replacement)
            for dependency in graph.dependencies
        ),
    )


def _replacement_packet(audit_packet: Mapping[str, Any]) -> dict[str, Any]:
    replacement = dict(audit_packet)
    replacement.pop("replay_authority_hash", None)
    replacement["verified"] = False
    return replacement


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()

