from __future__ import annotations

from pathlib import Path

import pytest

from afritech.extensions.afriprog.orchestrator import (
    AfriProgOrchestrator,
    AfriProgOrchestratorError,
    run_phase_2_preview,
)
from afritech.extensions.afriprog.task_planner.failure_parser import (
    FailureParser,
    FailureParserError,
)
from afritech.extensions.afriprog.task_planner.planner import (
    TaskPlanner,
    TaskPlannerError,
)
from afritech.extensions.afriprog.task_planner.task_model import (
    Task,
    TaskModelError,
)
from afritech.extensions.afriprog.task_planner.task_types import (
    RiskLevel,
    TaskType,
    get_task_metadata,
)


def test_failure_parser_extracts_structured_signals():
    parser = FailureParser(
        "ImportError: cannot import name ReplayVerifier. "
        "AssertionError: expected replay validation to pass."
    )

    signals = parser.signal_names()

    assert "import_error" in signals
    assert "missing_element" in signals
    assert "assertion_failure" in signals


def test_failure_parser_rejects_non_string_input():
    with pytest.raises(FailureParserError):
        FailureParser(123)  # type: ignore[arg-type]


def test_task_model_is_canonical_and_readable():
    task = Task(
        task_id="TASK-0001",
        task_type=TaskType.TEST_FAILURE.value,
        description="Investigate failing assertion.",
        target_files=("b.py", "a.py"),
        risk_level=RiskLevel.MEDIUM.value,
        requires_write=False,
        source_tests=("tests/test_b.py", "tests/test_a.py"),
    )

    data = task.canonical_dict()

    assert data["task_id"] == "TASK-0001"
    assert data["target_files"] == ["a.py", "b.py"]
    assert data["source_tests"] == ["tests/test_a.py", "tests/test_b.py"]
    assert data["requires_write"] is False


def test_task_model_rejects_invalid_risk_level():
    with pytest.raises(TaskModelError):
        Task(
            task_id="TASK-0001",
            task_type=TaskType.UNKNOWN.value,
            description="Invalid task.",
            target_files=(),
            risk_level="unknown",
            requires_write=False,
            source_tests=(),
        )


def test_task_type_metadata_registry_is_canonical():
    metadata = get_task_metadata(TaskType.MISSING_ELEMENT)

    assert metadata.task_type == TaskType.MISSING_ELEMENT
    assert metadata.default_risk == RiskLevel.LOW
    assert metadata.requires_write is True


def test_task_planner_creates_read_only_missing_element_task():
    planner = TaskPlanner()

    task = planner.plan_from_failure(
        failure_text="ImportError: cannot import name ReplayVerifier",
        related_tests=["afritech/tests/runtime/test_replay.py"],
        candidate_files=["afritech/runtime/replay.py"],
    )

    assert task.task_id == "TASK-0001"
    assert task.task_type == TaskType.MISSING_ELEMENT.value
    assert task.risk_level == RiskLevel.LOW.value
    assert task.requires_write is False
    assert task.target_files == ("afritech/runtime/replay.py",)


def test_task_planner_creates_read_only_test_failure_task():
    planner = TaskPlanner()

    task = planner.plan_from_failure(
        failure_text="AssertionError: expected True",
        related_tests=["tests/test_runtime.py"],
        candidate_files=["runtime/runtime.py"],
    )

    assert task.task_type == TaskType.TEST_FAILURE.value
    assert task.risk_level == RiskLevel.MEDIUM.value
    assert task.requires_write is False


def test_task_planner_uses_deterministic_incrementing_ids():
    planner = TaskPlanner()

    first = planner.plan_from_failure("AssertionError", (), ())
    second = planner.plan_from_failure("AssertionError", (), ())

    assert first.task_id == "TASK-0001"
    assert second.task_id == "TASK-0002"


def test_task_planner_rejects_empty_prefix():
    with pytest.raises(TaskPlannerError):
        TaskPlanner(task_prefix="")


def test_phase_2_orchestrator_runs_read_only_plan(tmp_path: Path):
    (tmp_path / "afritech" / "tests").mkdir(parents=True)
    (tmp_path / "afritech" / "runtime").mkdir(parents=True)

    (tmp_path / "afritech" / "tests" / "test_replay.py").write_text(
        "def test_sample():\n    assert True\n",
        encoding="utf-8",
    )
    (tmp_path / "afritech" / "runtime" / "replay.py").write_text(
        "class Replay:\n    pass\n",
        encoding="utf-8",
    )

    result = run_phase_2_preview(
        root=tmp_path,
        failure_text="ImportError: cannot import name ReplayVerifier",
        related_tests=("afritech/tests/test_replay.py",),
        candidate_files=("afritech/runtime/replay.py",),
    )

    data = result.canonical_dict()

    assert data["mode"] == "PHASE_2_READ_ONLY_PLANNING"
    assert data["task_count"] == 1
    assert data["tasks"][0]["requires_write"] is False
    assert data["tasks"][0]["task_type"] == TaskType.MISSING_ELEMENT.value


def test_phase_2_orchestrator_rejects_missing_root(tmp_path: Path):
    with pytest.raises(AfriProgOrchestratorError):
        AfriProgOrchestrator(root=tmp_path / "missing")


def test_phase_2_orchestrator_reports_disabled_mutation_flags(tmp_path: Path):
    orchestrator = AfriProgOrchestrator(root=tmp_path)

    data = orchestrator.canonical_dict()

    assert data["write_enabled"] is False
    assert data["patch_enabled"] is False
    assert data["git_enabled"] is False
