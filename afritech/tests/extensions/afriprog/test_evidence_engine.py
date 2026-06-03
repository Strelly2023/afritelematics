from __future__ import annotations

import json
from pathlib import Path

import pytest

from afritech.extensions.afriprog.code_executor.diff_model import Diff
from afritech.extensions.afriprog.code_executor.patch_model import Patch
from afritech.extensions.afriprog.evidence.evidence_generator import EvidenceGenerator
from afritech.extensions.afriprog.evidence.evidence_model import (
    EvidenceModelError,
    EvidenceRecord,
)
from afritech.extensions.afriprog.evidence.evidence_validator import (
    EvidenceValidator,
    EvidenceValidatorError,
)
from afritech.extensions.afriprog.task_planner.task_model import Task
from afritech.extensions.afriprog.task_planner.task_types import RiskLevel, TaskType
from afritech.extensions.afriprog.validator_runner.command_result import CommandResult


def test_evidence_record_generates_stable_hash():
    record = EvidenceRecord(
        evidence_id="EVIDENCE-001",
        phase="PHASE_3_PROPOSAL_ONLY",
        source="task_planner",
        status="captured",
        subject="TASK-0001",
        payload={"task_id": "TASK-0001"},
    )

    data = record.canonical_dict()

    assert len(data["evidence_hash"]) == 64
    assert data["evidence_id"] == "EVIDENCE-001"


def test_evidence_record_hash_uses_canonical_payload_order():
    first = EvidenceRecord(
        evidence_id="EVIDENCE-001",
        phase="PHASE_3_PROPOSAL_ONLY",
        source="task_planner",
        status="captured",
        subject="TASK-0001",
        payload={"b": 2, "a": 1},
    )
    second = EvidenceRecord(
        evidence_id="EVIDENCE-001",
        phase="PHASE_3_PROPOSAL_ONLY",
        source="task_planner",
        status="captured",
        subject="TASK-0001",
        payload={"a": 1, "b": 2},
    )

    assert first.evidence_hash == second.evidence_hash


def test_evidence_record_rejects_empty_id():
    with pytest.raises(EvidenceModelError):
        EvidenceRecord(
            evidence_id="",
            phase="PHASE_3_PROPOSAL_ONLY",
            source="task_planner",
            status="captured",
            subject="TASK-0001",
            payload={},
        )


def test_evidence_generator_from_task():
    task = Task(
        task_id="TASK-0001",
        task_type=TaskType.MISSING_ELEMENT.value,
        description="Missing element",
        target_files=("afritech/extensions/afriprog/example.py",),
        risk_level=RiskLevel.LOW.value,
        requires_write=False,
        source_tests=(),
    )

    record = EvidenceGenerator().from_task(task)

    assert record.source == "task_planner"
    assert record.subject == "TASK-0001"
    assert record.status == "captured"
    assert EvidenceValidator().validate_record(record) is True


def test_evidence_generator_from_patch_and_diff():
    patch = Patch(
        file_path="afritech/extensions/afriprog/example.py",
        original_content="a = 1\n",
        updated_content="a = 2\n",
    )

    diff = Diff(
        file_path="afritech/extensions/afriprog/example.py",
        diff_text="-a = 1\n+a = 2",
    )

    generator = EvidenceGenerator()

    patch_record = generator.from_patch(patch)
    diff_record = generator.from_diff(diff)

    assert patch_record.source == "code_executor"
    assert diff_record.source == "code_executor"

    validator = EvidenceValidator()

    assert validator.validate_record(patch_record) is True
    assert validator.validate_record(diff_record) is True


def test_evidence_generator_from_command_result():
    result = CommandResult(
        command=("python3", "-m", "pytest"),
        exit_code=0,
        stdout="passed",
        stderr="",
        duration_seconds=0.1,
    )

    record = EvidenceGenerator().from_command_result(result)

    assert record.source == "validator_runner"
    assert record.status == "passed"
    assert EvidenceValidator().validate_record(record) is True


def test_evidence_generator_command_id_is_stable():
    result = CommandResult(
        command=("python3", "-m", "pytest"),
        exit_code=0,
        stdout="passed",
        stderr="",
        duration_seconds=0.1,
    )

    first = EvidenceGenerator().from_command_result(result)
    second = EvidenceGenerator().from_command_result(result)

    assert first.evidence_id == second.evidence_id
    assert first.evidence_id.startswith("EVIDENCE-COMMAND-")


def test_evidence_bundle_is_deterministic_and_valid():
    generator = EvidenceGenerator()

    records = (
        EvidenceRecord(
            evidence_id="EVIDENCE-B",
            phase="PHASE_3_PROPOSAL_ONLY",
            source="task_planner",
            status="captured",
            subject="B",
            payload={"value": "b"},
        ),
        EvidenceRecord(
            evidence_id="EVIDENCE-A",
            phase="PHASE_3_PROPOSAL_ONLY",
            source="task_planner",
            status="captured",
            subject="A",
            payload={"value": "a"},
        ),
    )

    bundle = generator.bundle(records)

    assert bundle["record_count"] == 2
    assert bundle["records"][0]["evidence_id"] == "EVIDENCE-A"
    assert EvidenceValidator().validate_bundle(bundle) is True


def test_evidence_bundle_json_is_valid_json():
    record = EvidenceRecord(
        evidence_id="EVIDENCE-001",
        phase="PHASE_3_PROPOSAL_ONLY",
        source="task_planner",
        status="captured",
        subject="TASK-0001",
        payload={"task_id": "TASK-0001"},
    )

    text = EvidenceGenerator().bundle_json((record,))
    loaded = json.loads(text)

    assert loaded["record_count"] == 1


def test_evidence_write_bundle_creates_file(tmp_path: Path):
    record = EvidenceRecord(
        evidence_id="EVIDENCE-001",
        phase="PHASE_3_PROPOSAL_ONLY",
        source="task_planner",
        status="captured",
        subject="TASK-0001",
        payload={"task_id": "TASK-0001"},
    )

    output = EvidenceGenerator().write_bundle(
        records=(record,),
        path=tmp_path / "evidence_bundle.json",
    )

    assert output.exists()

    loaded = json.loads(output.read_text(encoding="utf-8"))

    assert loaded["record_count"] == 1


def test_evidence_validator_rejects_bad_phase():
    record = EvidenceRecord(
        evidence_id="EVIDENCE-001",
        phase="BAD_PHASE",
        source="task_planner",
        status="captured",
        subject="TASK-0001",
        payload={},
    )

    with pytest.raises(EvidenceValidatorError):
        EvidenceValidator().validate_record(record)


def test_evidence_validator_rejects_missing_fields():
    with pytest.raises(EvidenceValidatorError):
        EvidenceValidator().validate_dict(
            {
                "evidence_id": "EVIDENCE-001",
            }
        )
