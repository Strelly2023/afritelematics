"""Trust lock-in proof harness."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from afritech.replay_authority.engine.proof import run_replay_authority_proof
from afritech.trust_lock.engine.dependency_model import (
    TrustDependencyGraph,
    build_dependency_graph,
)
from afritech.trust_lock.engine.removal_simulator import (
    RemovalSimulation,
    simulate_removal,
)


AUTHORITY_LAW = (
    "Externally consumed truth must not be replaceable without loss of "
    "institutional trust."
)

REQUIRED_SCENARIOS = (
    "external_dependency",
    "operational_consumption",
    "removal_breakage",
    "replacement_failure",
)

REPORT_FILES = {
    "external_dependency": "external_dependency.json",
    "operational_consumption": "operational_consumption.json",
    "removal_breakage": "removal_breakage.json",
    "replacement_failure": "replacement_failure.json",
}


class TrustLockProofError(RuntimeError):
    """Raised when trust lock-in proof detects replaceability."""


@dataclass(frozen=True)
class TrustLockScenarioProof:
    scenario: str
    dependency_graph: TrustDependencyGraph
    simulation: RemovalSimulation
    replay_authority_hash: str

    @property
    def verified(self) -> bool:
        if self.scenario == "external_dependency":
            return bool(self.dependency_graph.dependencies)
        if self.scenario == "operational_consumption":
            return self.simulation.baseline_trusted
        if self.scenario == "removal_breakage":
            return self.simulation.removal_breaks_workflows
        if self.scenario == "replacement_failure":
            return self.simulation.replacement_breaks_trust
        return False

    def canonical_dict(self) -> dict[str, object]:
        return {
            "authority_law": AUTHORITY_LAW,
            "dependency_graph": self.dependency_graph.canonical_dict(),
            "replay_authority_hash": self.replay_authority_hash,
            "scenario": self.scenario,
            "simulation": self.simulation.canonical_dict(),
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


@dataclass(frozen=True)
class TrustLockProofReport:
    scenarios: tuple[TrustLockScenarioProof, ...]

    @property
    def verified(self) -> bool:
        return (
            tuple(scenario.scenario for scenario in self.scenarios)
            == REQUIRED_SCENARIOS
            and all(scenario.verified for scenario in self.scenarios)
        )

    @property
    def trust_lock_hash(self) -> str:
        return _canonical_hash(
            {
                "authority_law": AUTHORITY_LAW,
                "scenario_hashes": {
                    scenario.scenario: scenario.report_hash()
                    for scenario in self.scenarios
                },
                "verified": self.verified,
            }
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "authority_law": AUTHORITY_LAW,
            "required_scenarios": list(REQUIRED_SCENARIOS),
            "scenarios": [scenario.canonical_dict() for scenario in self.scenarios],
            "schema": "afritech.trust_lock_proof_report.v1",
            "trust_lock_hash": self.trust_lock_hash,
            "verified": self.verified,
        }


def run_trust_lock_proof() -> TrustLockProofReport:
    graph = build_dependency_graph()
    authority_report = run_replay_authority_proof()
    audit_packet = _audit_packet_from_replay_authority()
    simulation = simulate_removal(graph, audit_packet)
    report = TrustLockProofReport(
        scenarios=tuple(
            TrustLockScenarioProof(
                dependency_graph=graph,
                replay_authority_hash=authority_report.replay_authority_hash,
                scenario=scenario,
                simulation=simulation,
            )
            for scenario in REQUIRED_SCENARIOS
        )
    )
    if not report.verified:
        raise TrustLockProofError("trust lock-in proof failed")
    return report


def write_trust_lock_proof_reports(
    output_dir: str | Path = "reports/trust_lock_proof_v1",
) -> TrustLockProofReport:
    report = run_trust_lock_proof()
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    for scenario in report.scenarios:
        _write_json(target / REPORT_FILES[scenario.scenario], scenario.canonical_dict())
    _write_json(
        target / "trust_lock_equivalence.json",
        {
            "authority_law": AUTHORITY_LAW,
            "equivalent": report.verified,
            "schema": "afritech.trust_lock_equivalence_report.v1",
            "scenario_hashes": {
                scenario.scenario: scenario.report_hash()
                for scenario in report.scenarios
            },
            "trust_lock_hash": report.trust_lock_hash,
        },
    )
    return report


def _audit_packet_from_replay_authority() -> Mapping[str, Any]:
    authority_report = run_replay_authority_proof()
    scenario = next(
        item
        for item in authority_report.scenarios
        if item.scenario == "conflicting_claims_resolution"
    )
    return scenario.audit_packet.canonical_dict()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8",
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


def main() -> int:
    try:
        report = write_trust_lock_proof_reports()
    except TrustLockProofError as exc:
        print(f"Trust lock-in proof FAILED: {exc}")
        return 1
    print(
        "Trust lock-in proof PASSED: "
        f"scenarios={len(report.scenarios)} "
        f"trust_lock_hash={report.trust_lock_hash}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

