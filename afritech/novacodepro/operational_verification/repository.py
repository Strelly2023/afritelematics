from __future__ import annotations

from typing import Protocol

from .models import EvidenceEnvelope, GovernanceDecision, OperationalVerificationProgram, OperationalVerificationRun


class OperationalProgramRepository(Protocol):
    def save(self, program: OperationalVerificationProgram) -> OperationalVerificationProgram: ...
    def list(self) -> list[OperationalVerificationProgram]: ...
    def get(self, program_id: str) -> OperationalVerificationProgram | None: ...


class VerificationRunRepository(Protocol):
    def save(self, run: OperationalVerificationRun) -> OperationalVerificationRun: ...
    def list(self) -> list[OperationalVerificationRun]: ...
    def get(self, run_id: str) -> OperationalVerificationRun | None: ...


class EvidenceRepository(Protocol):
    def save(self, evidence: EvidenceEnvelope) -> EvidenceEnvelope: ...
    def list(self) -> list[EvidenceEnvelope]: ...
    def get(self, evidence_id: str) -> EvidenceEnvelope | None: ...


class ApprovalRepository(Protocol):
    def save(self, decision: GovernanceDecision) -> GovernanceDecision: ...
    def list(self) -> list[GovernanceDecision]: ...


class InMemoryOperationalVerificationRepository:
    def __init__(self) -> None:
        self.programs: dict[str, OperationalVerificationProgram] = {}
        self.runs: dict[str, OperationalVerificationRun] = {}
        self.evidence: dict[str, EvidenceEnvelope] = {}
        self.approvals: list[GovernanceDecision] = []

    def save_program(self, program: OperationalVerificationProgram) -> OperationalVerificationProgram:
        self.programs[program.id] = program
        return program

    def list_programs(self) -> list[OperationalVerificationProgram]:
        return list(self.programs.values())

    def get_program(self, program_id: str) -> OperationalVerificationProgram | None:
        return self.programs.get(program_id)

    def save_run(self, run: OperationalVerificationRun) -> OperationalVerificationRun:
        self.runs[run.id] = run
        return run

    def list_runs(self) -> list[OperationalVerificationRun]:
        return list(self.runs.values())

    def get_run(self, run_id: str) -> OperationalVerificationRun | None:
        return self.runs.get(run_id)

    def save_evidence(self, evidence: EvidenceEnvelope) -> EvidenceEnvelope:
        if evidence.evidence_id in self.evidence:
            raise ValueError("immutable_evidence_already_exists")
        self.evidence[evidence.evidence_id] = evidence
        return evidence

    def list_evidence(self) -> list[EvidenceEnvelope]:
        return list(self.evidence.values())

    def get_evidence(self, evidence_id: str) -> EvidenceEnvelope | None:
        return self.evidence.get(evidence_id)

    def save_approval(self, decision: GovernanceDecision) -> GovernanceDecision:
        self.approvals.append(decision)
        return decision

    def list_approvals(self) -> list[GovernanceDecision]:
        return list(self.approvals)
