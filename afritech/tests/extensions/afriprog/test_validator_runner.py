from __future__ import annotations

from pathlib import Path

import pytest

from afritech.extensions.afriprog.validator_runner.ci_runner import (
    CIRunner,
    CIRunnerError,
)
from afritech.extensions.afriprog.validator_runner.command_result import (
    CommandResult,
    CommandResultError,
)
from afritech.extensions.afriprog.validator_runner.flutter_runner import (
    FlutterRunner,
    FlutterRunnerError,
)
from afritech.extensions.afriprog.validator_runner.test_runner import (
    TestRunner,
    TestRunnerError,
)


def test_command_result_reports_passed_and_failed():
    passed = CommandResult(
        command=("python3", "-m", "pytest"),
        exit_code=0,
        stdout="ok",
        stderr="",
        duration_seconds=0.1,
    )

    failed = CommandResult(
        command=("python3", "-m", "pytest"),
        exit_code=1,
        stdout="",
        stderr="failed",
        duration_seconds=0.1,
    )

    assert passed.passed is True
    assert passed.failed is False
    assert failed.passed is False
    assert failed.failed is True


def test_command_result_rejects_empty_command():
    with pytest.raises(CommandResultError):
        CommandResult(
            command=(),
            exit_code=0,
            stdout="",
            stderr="",
            duration_seconds=0.0,
        )


def test_test_runner_runs_pytest_on_fixture(tmp_path: Path):
    test_file = tmp_path / "test_sample.py"
    test_file.write_text(
        "def test_sample():\n    assert True\n",
        encoding="utf-8",
    )

    result = TestRunner(root=tmp_path).run_file(test_file)

    assert result.passed is True
    assert result.exit_code == 0
    assert "passed" in result.stdout.lower()


def test_test_runner_captures_failed_pytest(tmp_path: Path):
    test_file = tmp_path / "test_failure.py"
    test_file.write_text(
        "def test_failure():\n    assert False\n",
        encoding="utf-8",
    )

    result = TestRunner(root=tmp_path).run_file(test_file)

    assert result.failed is True
    assert result.exit_code != 0


def test_test_runner_rejects_invalid_root(tmp_path: Path):
    with pytest.raises(TestRunnerError):
        TestRunner(root=tmp_path / "missing")


def test_test_runner_rejects_non_pytest_command(tmp_path: Path):
    runner = TestRunner(root=tmp_path)

    with pytest.raises(TestRunnerError):
        runner._run(["python3", "-m", "pip", "list"])  # noqa: SLF001


def test_ci_runner_rejects_unknown_module(tmp_path: Path):
    runner = CIRunner(root=tmp_path)

    with pytest.raises(CIRunnerError):
        runner.run_module("os")


def test_ci_runner_allows_phase_2_orchestrator_on_repo_root():
    result = CIRunner(root=".").run_phase_2_orchestrator_preview()

    assert result.command[:3] == (
        "python3",
        "-m",
        "afritech.extensions.afriprog.orchestrator",
    )
    assert result.exit_code in {0, 1}


def test_flutter_runner_rejects_missing_root(tmp_path: Path):
    with pytest.raises(FlutterRunnerError):
        FlutterRunner(root=tmp_path / "missing")


def test_flutter_runner_rejects_unsupported_command(tmp_path: Path):
    runner = FlutterRunner(root=tmp_path)

    with pytest.raises(FlutterRunnerError):
        runner._run(["flutter", "pub", "get"])  # noqa: SLF001
