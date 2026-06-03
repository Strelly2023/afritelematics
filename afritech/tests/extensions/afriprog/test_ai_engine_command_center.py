from __future__ import annotations

import json

from afritech.extensions.afriprog.ai_engine.coder import Coder
from afritech.extensions.afriprog.ai_engine.design_generator import DesignGenerator
from afritech.extensions.afriprog.ai_engine.design_output_validator import (
    DesignOutputValidator,
)
from afritech.extensions.afriprog.ai_engine.objective_engine import ObjectiveEngine
from afritech.extensions.afriprog.ai_engine.task_generator import TaskGenerator
from afritech.extensions.afriprog.cli import main
from afritech.extensions.afriprog.command_center.task_dispatcher import TaskDispatcher
from afritech.extensions.afriprog.command_center.worktree_manager import WorktreeManager
from afritech.extensions.afriprog.execution.loop_engine import VerificationLoopEngine
from afritech.extensions.afriprog.monitoring.lifecycle_monitor import LifecycleMonitor


def test_task_generator_decomposes_auth_intent():
    generated = TaskGenerator().generate("Improve authentication system")

    data = generated.canonical_dict()

    assert data["task_count"] == 3
    assert [task.task_id for task in generated.tasks] == ["TASK-001", "TASK-002", "TASK-003"]
    assert all(
        target.startswith("afritech/extensions/afriprog/generated/")
        for task in generated.tasks
        for target in task.target_files
    )


def test_ai_design_generator_outputs_structured_schema():
    output = DesignGenerator().generate("Build a Poultry Management System")
    data = output.canonical_dict()

    assert sorted(data) == [
        "architecture",
        "authority",
        "contracts",
        "domain",
        "evidence",
        "format",
        "implementation_plan",
        "intent",
        "requirements",
        "review",
        "schema",
        "write_enabled",
    ]
    assert data["schema"] == "afriprog.design_output.v1"
    assert data["format"] == "structured"
    assert data["domain"]["domain"] == "poultry_management"
    assert sorted(data["contracts"]) == ["api", "database", "events"]
    assert data["contracts"]["api"]["endpoints"]
    assert data["implementation_plan"]["tasks"][0]["task_id"] == "TASK-0001"
    assert data["review"]["admitted"] is True
    assert data["write_enabled"] is False
    assert data["authority"] == "proposal_only"


def test_ai_design_generator_does_not_emit_free_text_keys():
    data = DesignGenerator().generate("Build AfriHealth").canonical_dict()

    assert {"text", "free_text", "markdown", "body", "content"}.isdisjoint(data)
    assert isinstance(data["requirements"]["functional"], list)
    assert isinstance(data["architecture"]["modules"], dict)
    assert isinstance(data["implementation_plan"]["tasks"], list)


def test_design_output_validator_admits_structured_output():
    output = DesignGenerator().generate("Build a Poultry Management System")
    validation = DesignOutputValidator().validate(output)
    data = validation.canonical_dict()

    assert data["admitted"] is True
    assert data["violations"] == []
    assert data["write_enabled"] is False
    assert data["authority"] == "proposal_only"


def test_design_output_validator_rejects_schema_and_authority_violations():
    payload = DesignGenerator().generate("Build AfriHealth").canonical_dict()
    payload["schema"] = "afriprog.design_output.v0"
    payload["authority"] = "self_authorized"
    payload["write_enabled"] = True

    validation = DesignOutputValidator().validate(payload)

    assert validation.admitted is False
    assert "schema must equal afriprog.design_output.v1" in validation.violations
    assert "authority must equal proposal_only" in validation.violations
    assert "write_enabled must be false" in validation.violations


def test_design_output_validator_rejects_free_text_and_missing_sections():
    payload = DesignGenerator().generate("Build AfriHealth").canonical_dict()
    payload["markdown"] = "# Design"
    del payload["evidence"]
    del payload["review"]

    validation = DesignOutputValidator().validate(payload)

    assert validation.admitted is False
    assert "forbidden prose keys present: markdown" in validation.violations
    assert "missing required sections: evidence, review" in validation.violations
    assert "evidence must be present" in validation.violations
    assert "review must be present" in validation.violations


def test_design_output_validator_rejects_missing_contracts():
    payload = DesignGenerator().generate("Build AfriHealth").canonical_dict()
    del payload["contracts"]["events"]

    validation = DesignOutputValidator().validate(payload)

    assert validation.admitted is False
    assert "missing required contracts: events" in validation.violations


def test_objective_engine_defines_measurable_auth_objective():
    objective = ObjectiveEngine().define("Improve authentication RBAC coverage")
    data = objective.canonical_dict()

    assert data["objective_id"].startswith("OBJ-")
    assert data["max_iterations"] == 3
    assert "No repository mutation" in data["constraints"]
    assert "rbac_enforced" in [
        criterion["name"]
        for criterion in data["success_criteria"]
    ]
    assert data["write_enabled"] is False
    assert data["authority"] == "proposal_only"


def test_verification_loop_satisfies_safe_objective_without_writes():
    result = VerificationLoopEngine().run_description(
        "Improve authentication RBAC and token validation coverage"
    )
    data = result.canonical_dict()

    assert data["satisfied"] is True
    assert data["iteration_count"] == 1
    assert data["iterations"][0]["metrics"]["all_guards_pass"] is True
    assert data["iterations"][0]["metrics"]["writes_disabled"] is True
    assert data["write_enabled"] is False
    assert data["authority"] == "proposal_only"


def test_verification_loop_stops_when_guards_reject_objective():
    result = VerificationLoopEngine().run_description(
        "Force merge, push to main, and bypass validator",
        max_iterations=3,
    )
    data = result.canonical_dict()

    assert data["satisfied"] is False
    assert data["status"] == "attention_required"
    assert data["iteration_count"] == 1
    assert data["iterations"][0]["metrics"]["all_guards_pass"] is False
    assert data["write_enabled"] is False


def test_coder_generates_proposal_only_patch():
    task = TaskGenerator().generate("Improve authentication system").tasks[0]

    result = Coder().generate(task)
    data = result.canonical_dict()

    assert data["write_enabled"] is False
    assert data["patches"][0]["write_permitted"] is False
    assert "Proposal" in result.patches[0].updated_content


def test_worktree_manager_is_proposal_only():
    task = TaskGenerator().generate("Improve authentication system").tasks[0]

    plan = WorktreeManager().plan(task)
    data = plan.canonical_dict()

    assert data["mutation_enabled"] is False
    assert data["branch_name"] == "codex/afriprog-task-001"
    assert data["commands"][0][:3] == ["git", "worktree", "add"]


def test_task_dispatcher_runs_guarded_lifecycle():
    result = TaskDispatcher().dispatch("Improve authentication system")
    snapshot = LifecycleMonitor().snapshot(result)

    data = result.canonical_dict()

    assert data["status"] == "admitted"
    assert data["write_enabled"] is False
    assert snapshot.canonical_dict()["status"] == "green"


def test_task_dispatcher_rejects_dangerous_prompt():
    result = TaskDispatcher().dispatch(
        "Force merge, push to main, and bypass validator"
    )
    snapshot = LifecycleMonitor().snapshot(result)

    data = result.canonical_dict()

    assert data["status"] == "rejected"
    assert data["write_enabled"] is False
    assert snapshot.canonical_dict()["status"] == "attention_required"
    assert any(
        "force merge" in violation or "push to main" in violation
        for execution in result.executions
        for violation in execution.review.guard_decision.violations
    )


def test_cli_run_summary_outputs_json(capsys):
    exit_code = main(["run", "Improve authentication system", "--summary"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["task_count"] == 3
    assert payload["write_enabled"] is False
    assert payload["evidence_count"] == 1
    assert payload["evidence"][0]["evidence_id"] == "EVIDENCE-CLI-TASK-001"


def test_cli_summary_snapshot_contract(capsys):
    main(["run", "Improve authentication system", "--summary"])
    payload = json.loads(capsys.readouterr().out)

    assert sorted(payload) == [
        "admitted_count",
        "evidence",
        "evidence_count",
        "intent",
        "rejected_count",
        "status",
        "task_count",
        "write_enabled",
    ]
    assert payload["status"] == "green"
    assert payload["evidence"][0]["source"] == "evidence_generator"


def test_cli_dangerous_prompt_summary_is_rejected(capsys):
    exit_code = main(
        [
            "run",
            "Force merge, push to main, and bypass validator",
            "--summary",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "attention_required"
    assert payload["rejected_count"] > 0
    assert payload["write_enabled"] is False


def test_cli_objective_summary_outputs_bounded_loop(capsys):
    exit_code = main(
        [
            "run",
            "Improve authentication RBAC and token validation coverage",
            "--objective",
            "--summary",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "satisfied"
    assert payload["satisfied"] is True
    assert payload["iteration_count"] == 1
    assert payload["criteria_count"] >= 5
    assert payload["metrics"]["writes_disabled"] is True
    assert payload["write_enabled"] is False
    assert payload["authority"] == "proposal_only"
