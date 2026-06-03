from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from afritech.extensions.afriprog.code_executor.diff_model import Diff
from afritech.extensions.afriprog.code_executor.patch_model import Patch
from afritech.extensions.afriprog.evidence.evidence_model import EvidenceRecord
from afritech.extensions.afriprog.task_planner.task_model import Task
from afritech.extensions.afriprog.validator_runner.command_result import (
    CommandResult,
)


class EvidenceGeneratorError(Exception):
    """Raised when evidence generation fails."""


class EvidenceGenerator:
    """
    AfriProgramming evidence generator.

    Constitutional properties:
    - deterministic
    - evidence-ready
    - non-authoritative
    - no mutation by default
    """

    PHASE = "PHASE_3_PROPOSAL_ONLY"

    def from_task(
        self,
        task: Task,
        *,
        evidence_id: str | None = None,
    ) -> EvidenceRecord:
        return EvidenceRecord(
            evidence_id=evidence_id or f"EVIDENCE-TASK-{task.task_id}",
            phase=self.PHASE,
            source="task_planner",
            status="captured",
            subject=task.task_id,
            payload=task.canonical_dict(),
        )

    def from_patch(
        self,
        patch: Patch,
        *,
        evidence_id: str | None = None,
    ) -> EvidenceRecord:
        return EvidenceRecord(
            evidence_id=evidence_id or f"EVIDENCE-PATCH-{patch.patch_hash[:12]}",
            phase=self.PHASE,
            source="code_executor",
            status="proposal_only",
            subject=patch.file_path,
            payload=patch.canonical_dict(),
        )

    def from_diff(
        self,
        diff: Diff,
        *,
        evidence_id: str | None = None,
    ) -> EvidenceRecord:
        return EvidenceRecord(
            evidence_id=evidence_id or f"EVIDENCE-DIFF-{diff.diff_hash[:12]}",
            phase=self.PHASE,
            source="code_executor",
            status="proposal_only",
            subject=diff.file_path,
            payload=diff.canonical_dict(),
        )

    def from_command_result(
        self,
        result: CommandResult,
        *,
        evidence_id: str | None = None,
    ) -> EvidenceRecord:
        status = "passed" if result.passed else "failed"

        return EvidenceRecord(
            evidence_id=(
                evidence_id
                or f"EVIDENCE-COMMAND-{_stable_id(result.command_string)}"
            ),
            phase=self.PHASE,
            source="validator_runner",
            status=status,
            subject=result.command_string,
            payload=result.canonical_dict(),
        )

    def bundle(
        self,
        records: list[EvidenceRecord] | tuple[EvidenceRecord, ...],
    ) -> dict[str, Any]:
        ordered = tuple(
            sorted(
                records,
                key=lambda item: item.evidence_id,
            )
        )

        return {
            "phase": self.PHASE,
            "record_count": len(ordered),
            "records": [
                record.canonical_dict()
                for record in ordered
            ],
        }

    def bundle_json(
        self,
        records: list[EvidenceRecord] | tuple[EvidenceRecord, ...],
    ) -> str:
        return json.dumps(
            self.bundle(records),
            indent=2,
            sort_keys=True,
        )

    def write_bundle(
        self,
        records: list[EvidenceRecord] | tuple[EvidenceRecord, ...],
        path: str | Path,
    ) -> Path:
        output_path = Path(path)

        output_path.write_text(
            self.bundle_json(records),
            encoding="utf-8",
        )

        return output_path.resolve()


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16].upper()
