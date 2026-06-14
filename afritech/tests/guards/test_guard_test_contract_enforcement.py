from __future__ import annotations

from pathlib import Path

import pytest

from afritech.guards.guard_test_contract_enforcement import (
    DEFAULT_TEST_ROOT,
    TestContractEnforcementGuardError,
    main,
    validate,
)


def _write_test_file(path: Path, function_names: list[str]) -> None:
    lines = ["from __future__ import annotations", ""]
    for name in function_names:
        lines.extend(
            [
                f"def {name}():",
                "    assert True",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def test_guard_accepts_current_compliance_test_root() -> None:
    report = validate(DEFAULT_TEST_ROOT)

    assert report.verified is True
    assert report.missing_patterns == ()
    assert report.parse_errors == ()
    assert report.file_count > 0


def test_guard_rejects_missing_patterns(tmp_path: Path) -> None:
    test_root = tmp_path / "tests"
    test_root.mkdir()
    _write_test_file(
        test_root / "test_sample.py",
        [
            "test_happy_path",
            "test_invalid_input",
            "test_determinism",
        ],
    )

    with pytest.raises(TestContractEnforcementGuardError, match="missing patterns"):
        validate(test_root)


def test_guard_cli_reports_pass_for_contract_root(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    test_root = tmp_path / "tests"
    test_root.mkdir()
    _write_test_file(
        test_root / "test_sample.py",
        [
            "test_happy_path",
            "test_invalid_input",
            "test_determinism",
            "test_replay_stability",
            "test_tampering",
            "test_serialization",
            "test_schema",
            "test_authority_boundary",
            "test_governance",
            "test_backward_compatibility",
            "test_detects_drift",
            "test_reproducibility",
        ],
    )

    assert main(["--root", str(test_root)]) == 0
    output = capsys.readouterr().out
    assert "TEST_CONTRACT_ENFORCEMENT: PASS" in output

