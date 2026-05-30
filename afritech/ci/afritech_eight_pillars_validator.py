"""Validate and summarize the eight AfriTech pillars."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from afritech.ci import (
    afripower_intelligence_validator,
    afriprogramming_engineering_validator,
    afritech_constitution_v1_binding_validator,
    afritech_constitution_v1_validator,
    afritech_constitutional_pillars_validator,
    afritpps_execution_validator,
)


class AfriTechEightPillarsValidationError(RuntimeError):
    """Raised when any of the eight pillars fails validation."""


@dataclass(frozen=True)
class EightPillarSummary:
    pillar_id: str
    name: str
    layer: str
    role: str
    summary: str
    purpose: str
    question_answered: str
    outputs: tuple[str, ...]
    verified: bool

    def canonical_dict(self) -> dict[str, object]:
        return {
            "pillar_id": self.pillar_id,
            "name": self.name,
            "layer": self.layer,
            "role": self.role,
            "summary": self.summary,
            "purpose": self.purpose,
            "question_answered": self.question_answered,
            "outputs": self.outputs,
            "verified": self.verified,
        }


@dataclass(frozen=True)
class AfriTechEightPillarsReport:
    pillars: tuple[EightPillarSummary, ...]

    @property
    def verified(self) -> bool:
        return len(self.pillars) == 8 and all(pillar.verified for pillar in self.pillars)

    @property
    def constitutional_pillars(self) -> tuple[EightPillarSummary, ...]:
        return tuple(
            pillar for pillar in self.pillars if pillar.layer == "CONSTITUTIONAL"
        )

    @property
    def ecosystem_pillars(self) -> tuple[EightPillarSummary, ...]:
        return tuple(pillar for pillar in self.pillars if pillar.layer == "ECOSYSTEM")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "schema": "afritech.eight_pillars_validation_report.v1",
            "pillar_count": len(self.pillars),
            "constitutional_pillar_count": len(self.constitutional_pillars),
            "ecosystem_pillar_count": len(self.ecosystem_pillars),
            "verified": self.verified,
            "pillars": [pillar.canonical_dict() for pillar in self.pillars],
        }


CONSTITUTIONAL_SUMMARIES = {
    "DETERMINISTIC_TRUTH": {
        "summary": "Deterministic Truth makes replay governance the source of canonical truth.",
        "purpose": "Defines canonical truth through deterministic replay.",
        "question_answered": "What is true?",
        "outputs": (
            "Replay Authority",
            "Replay Integrity",
            "Authoritative Decisions",
            "Replay Proof Reports",
        ),
    },
    "ORCHESTRATION": {
        "summary": "Orchestration coordinates execution without mutating event meaning or replay truth.",
        "purpose": "Coordinates execution while preserving replay safety.",
        "question_answered": "How does execution proceed safely?",
        "outputs": (
            "Workflow Results",
            "Dependency Decisions",
            "Saga Compensation",
            "Replay-Safe Execution Flow",
        ),
    },
    "DATA_LOCALITY": {
        "summary": "Data Locality keeps compute near declared data, partitions, and surfaces.",
        "purpose": "Keeps compute near bounded, declared data scope.",
        "question_answered": "Where should computation happen?",
        "outputs": (
            "Locality Guard Reports",
            "Scheduler Traces",
            "Partition Affinity",
            "Bounded Working Sets",
        ),
    },
    "OBSERVABILITY": {
        "summary": "Observability explains system behavior while remaining non-authoritative.",
        "purpose": "Explains system behavior without creating decision authority.",
        "question_answered": "What happened and why?",
        "outputs": (
            "Traces",
            "Metrics",
            "Evidence Snapshots",
            "Non-Authoritative Reports",
        ),
    },
}

ECOSYSTEM_SUMMARIES = {
    "AfriCPPT": {
        "summary": "AfriCPPT governs through policy, ADRs, invariants, rules, bindings, and guards.",
        "validator": afritech_constitution_v1_binding_validator.validate,
    },
    "AfriTPPS": {
        "summary": "AfriTPPS executes operational capability through workflows, programs, and metrics.",
        "validator": afritpps_execution_validator.validate_afritpps_execution_surface,
    },
    "AfriProgramming": {
        "summary": "AfriProgramming engineers proof-aware autonomous software systems.",
        "validator": afriprogramming_engineering_validator.validate_afriprogramming_engineering_surface,
    },
    "AFRIPower": {
        "summary": "AFRIPower explains evidence through read-only enterprise intelligence views.",
        "validator": lambda: afripower_intelligence_validator.validate_afripower_intelligence_surface(
            require_tests=True
        ),
    },
}


def validate() -> AfriTechEightPillarsReport:
    payload = afritech_constitution_v1_validator.load_constitution()
    afritech_constitution_v1_validator.validate()
    constitutional_report = afritech_constitutional_pillars_validator.validate()

    summaries = _constitutional_summaries(constitutional_report)
    summaries += _ecosystem_summaries(payload)

    report = AfriTechEightPillarsReport(pillars=tuple(summaries))
    if not report.verified:
        raise AfriTechEightPillarsValidationError(
            "AfriTech eight-pillar report failed"
        )
    return report


def _constitutional_summaries(
    report: afritech_constitutional_pillars_validator.AfriTechConstitutionalPillarsReport,
) -> list[EightPillarSummary]:
    summaries: list[EightPillarSummary] = []
    for pillar in report.pillars:
        summary = CONSTITUTIONAL_SUMMARIES[pillar.pillar_id]
        summaries.append(
            EightPillarSummary(
                pillar_id=pillar.pillar_id,
                name=pillar.name,
                layer="CONSTITUTIONAL",
                role=pillar.constitutional_function,
                summary=summary["summary"],
                purpose=summary["purpose"],
                question_answered=summary["question_answered"],
                outputs=tuple(summary["outputs"]),
                verified=pillar.ga_elite_complete,
            )
        )
    return summaries


def _ecosystem_summaries(payload: dict[str, object]) -> list[EightPillarSummary]:
    responsibilities = payload.get("layer_responsibilities")
    if not isinstance(responsibilities, dict):
        raise AfriTechEightPillarsValidationError(
            "constitution missing layer_responsibilities"
        )

    summaries: list[EightPillarSummary] = []
    for pillar_id, metadata in afritech_constitution_v1_validator.REQUIRED_ECOSYSTEM_PILLARS.items():
        branch = responsibilities.get(pillar_id)
        if not isinstance(branch, dict):
            raise AfriTechEightPillarsValidationError(
                f"{pillar_id} responsibilities missing"
            )

        validator = ECOSYSTEM_SUMMARIES[pillar_id]["validator"]
        _run_validator(pillar_id, validator)

        outputs = branch.get("outputs")
        if not isinstance(outputs, list) or not outputs:
            raise AfriTechEightPillarsValidationError(
                f"{pillar_id} outputs missing"
            )

        summaries.append(
            EightPillarSummary(
                pillar_id=pillar_id,
                name=pillar_id,
                layer="ECOSYSTEM",
                role=str(metadata["role"]),
                summary=str(ECOSYSTEM_SUMMARIES[pillar_id]["summary"]),
                purpose=str(branch["purpose"]),
                question_answered=str(branch["question_answered"]),
                outputs=tuple(str(output) for output in outputs),
                verified=True,
            )
        )
    return summaries


def _run_validator(pillar_id: str, validator: Callable[[], object]) -> None:
    try:
        validator()
    except Exception as exc:
        raise AfriTechEightPillarsValidationError(
            f"{pillar_id} validator failed: {exc}"
        ) from exc


def format_summary(report: AfriTechEightPillarsReport) -> str:
    lines = [
        "AfriTech eight pillars validation PASSED",
        f"pillar_count={len(report.pillars)} verified={report.verified}",
    ]
    for pillar in report.pillars:
        lines.append(
            f"- {pillar.layer}: {pillar.name} ({pillar.role}) - {pillar.summary}"
        )
    return "\n".join(lines)


def main() -> int:
    try:
        report = validate()
    except AfriTechEightPillarsValidationError as exc:
        print(f"AfriTech eight pillars validation FAILED: {exc}")
        return 1

    print(format_summary(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
