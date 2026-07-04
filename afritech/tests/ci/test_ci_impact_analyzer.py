from __future__ import annotations

import json
from pathlib import Path

from afritech.ci.change_impact_analyzer import (
    PLAN_PATH,
    analyze_changed_files,
    render_summary,
    write_impact_artifacts,
)
from afritech.ci.run_selected_tests import run_selected_tests


def test_novapay_change_selects_novapay_related_suites() -> None:
    plan = analyze_changed_files(["afritech/novapay/service.py"])

    assert plan.full_validation_required is True
    assert "novapay" in plan.required_test_suites
    assert "payments" in plan.required_test_suites
    assert "trust" in plan.required_test_suites
    assert "release_certification" in plan.required_test_suites
    assert "four_gate" in plan.required_governance_checks
    assert "runtime_boundary" in plan.required_governance_checks
    assert any(module.startswith("novapay") for module in plan.affected_modules)
    assert plan.confidence >= 0.99

    write_impact_artifacts(plan)
    assert PLAN_PATH.exists()
    assert "CI Impact Summary" in render_summary(plan)


def test_forced_full_validation_triggers_all_suites() -> None:
    plan = analyze_changed_files(["afritech/guards/runtime_boundary_validator.py"])

    assert plan.full_validation_required is True
    assert "release_certification" in plan.required_test_suites
    assert "docs_link_check" in plan.required_governance_checks
    assert "secret_scan" in plan.required_governance_checks
    assert "git_diff_check" in plan.required_governance_checks


def test_selected_test_runner_supports_dry_run(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "required_test_suites": ["novapay", "dashboard"],
                "full_validation_required": False,
            }
        ),
        encoding="utf-8",
    )

    exit_code = run_selected_tests(plan_path, dry_run=True)

    assert exit_code == 0
