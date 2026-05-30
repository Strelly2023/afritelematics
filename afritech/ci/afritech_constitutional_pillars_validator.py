"""Validate all four AfriTech constitutional pillars at GA Elite level."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from afritech.ci import (
    afritech_constitution_v1_validator,
    data_locality_validator,
    observability_authority_validator,
    observability_evidence_validator,
    replay_authority_validator,
    replay_integrity_validator,
)
from afritech.runtime.orchestration.orchestration_manager import OrchestrationManager


ROOT = Path(__file__).resolve().parents[2]

REQUIRED_PILLAR_FILES = {
    "DETERMINISTIC_TRUTH": (
        ROOT / "afritech/ci/replay_authority_validator.py",
        ROOT / "afritech/ci/replay_integrity_validator.py",
        ROOT / "afritech/replay_authority/engine/proof.py",
        ROOT / "afritech/tests/replay_authority/test_replay_authority_gate4.py",
        ROOT / "afritech/tests/replay/test_replay_valid.py",
    ),
    "ORCHESTRATION": (
        ROOT / "afritech/runtime/orchestration/orchestration_manager.py",
        ROOT / "afritech/runtime/orchestration/workflow_engine.py",
        ROOT / "afritech/runtime/orchestration/dependency_graph.py",
        ROOT / "afritech/runtime/orchestration/saga_manager.py",
        ROOT / "afritech/tests/runtime/test_orchestration.py",
    ),
    "DATA_LOCALITY": (
        ROOT / "afritech/ci/data_locality_validator.py",
        ROOT / "afritech/guards/data_locality_guard.py",
        ROOT / "afritech/runtime/locality/scheduler.py",
        ROOT / "afritech/constitution/canonical/concepts/data_locality.yaml",
        ROOT / "afritech/tests/runtime/test_locality_scheduler.py",
        ROOT / "afritech/tests/governance/test_data_locality_guard.py",
    ),
    "OBSERVABILITY": (
        ROOT / "afritech/ci/observability_authority_validator.py",
        ROOT / "afritech/ci/observability_evidence_validator.py",
        ROOT / "afritech/observability/evidence.py",
        ROOT / "afritech/runtime/observability/observability_manager.py",
        ROOT / "afritech/tests/runtime/test_observability.py",
        ROOT / "afritech/tests/observability/test_observability_evidence.py",
    ),
}


class AfriTechConstitutionalPillarsValidationError(RuntimeError):
    """Raised when any AfriTech constitutional pillar is incomplete."""


@dataclass(frozen=True)
class PillarValidationReport:
    pillar_id: str
    name: str
    constitutional_function: str
    implementation_files: int
    behavior_verified: bool

    @property
    def ga_elite_complete(self) -> bool:
        return self.implementation_files > 0 and self.behavior_verified


@dataclass(frozen=True)
class AfriTechConstitutionalPillarsReport:
    pillars: tuple[PillarValidationReport, ...]

    @property
    def verified(self) -> bool:
        return len(self.pillars) == 4 and all(
            pillar.ga_elite_complete for pillar in self.pillars
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "schema": "afritech.constitutional_pillars_validation_report.v1",
            "pillar_count": len(self.pillars),
            "verified": self.verified,
            "pillars": [
                {
                    "pillar_id": pillar.pillar_id,
                    "name": pillar.name,
                    "constitutional_function": pillar.constitutional_function,
                    "implementation_files": pillar.implementation_files,
                    "behavior_verified": pillar.behavior_verified,
                    "ga_elite_complete": pillar.ga_elite_complete,
                }
                for pillar in self.pillars
            ],
        }


def validate() -> AfriTechConstitutionalPillarsReport:
    afritech_constitution_v1_validator.validate()
    required = afritech_constitution_v1_validator.REQUIRED_CONSTITUTIONAL_PILLARS

    validators: dict[str, Callable[[], bool]] = {
        "DETERMINISTIC_TRUTH": _validate_deterministic_truth,
        "ORCHESTRATION": _validate_orchestration,
        "DATA_LOCALITY": _validate_data_locality,
        "OBSERVABILITY": _validate_observability,
    }

    reports: list[PillarValidationReport] = []
    for pillar_id, metadata in required.items():
        files = REQUIRED_PILLAR_FILES.get(pillar_id, ())
        missing = [path for path in files if not path.exists()]
        if missing:
            raise AfriTechConstitutionalPillarsValidationError(
                f"{pillar_id} missing implementation files: "
                + ", ".join(map(str, missing))
            )

        behavior_verified = validators[pillar_id]()
        reports.append(
            PillarValidationReport(
                pillar_id=pillar_id,
                name=metadata["name"],
                constitutional_function=metadata["constitutional_function"],
                implementation_files=len(files),
                behavior_verified=behavior_verified,
            )
        )

    report = AfriTechConstitutionalPillarsReport(pillars=tuple(reports))
    if not report.verified:
        raise AfriTechConstitutionalPillarsValidationError(
            "AfriTech constitutional pillars are not GA Elite complete"
        )
    return report


def _validate_deterministic_truth() -> bool:
    replay_authority = replay_authority_validator.validate()
    if not replay_authority.verified:
        raise AfriTechConstitutionalPillarsValidationError(
            "Deterministic Truth replay authority failed"
        )
    replay_integrity_validator.main()
    return True


def _validate_orchestration() -> bool:
    manager = OrchestrationManager()
    context = _Context()
    event = {"event_id": "pillar.orchestration", "payload": {"value": 1}}
    original = {"event_id": event["event_id"], "payload": dict(event["payload"])}
    decisions = {"route": "ga_elite", "priority": 1}

    first = manager.preview(event, decisions)
    second = manager.preview(event, decisions)
    if first != second:
        raise AfriTechConstitutionalPillarsValidationError(
            "Orchestration preview is not deterministic"
        )
    if event != original:
        raise AfriTechConstitutionalPillarsValidationError(
            "Orchestration preview mutated input event"
        )

    processed = manager.process(event, context, decisions)
    if processed.get("event_id") != event["event_id"]:
        raise AfriTechConstitutionalPillarsValidationError(
            "Orchestration result event mismatch"
        )
    if event != original:
        raise AfriTechConstitutionalPillarsValidationError(
            "Orchestration process mutated input event"
        )
    return True


def _validate_data_locality() -> bool:
    report = data_locality_validator.validate()
    if not report.verified:
        raise AfriTechConstitutionalPillarsValidationError(
            "Data Locality report failed"
        )
    return True


def _validate_observability() -> bool:
    observability_authority_validator.validate()
    evidence = observability_evidence_validator.validate()
    if not evidence.verified:
        raise AfriTechConstitutionalPillarsValidationError(
            "Observability evidence report failed"
        )
    return True


class _Context:
    policy: dict[str, object] = {}


def main() -> int:
    try:
        report = validate()
    except AfriTechConstitutionalPillarsValidationError as exc:
        print(f"AfriTech constitutional pillars validation FAILED: {exc}")
        return 1

    print(
        "AfriTech constitutional pillars validation PASSED: "
        f"pillar_count={len(report.pillars)} verified={report.verified}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
