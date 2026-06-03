from __future__ import annotations

import json

from afritech.extensions.afriprog.cli import main
from afritech.extensions.afriprog.design_generator.design_orchestrator import (
    DesignOrchestrator,
)


def test_design_orchestrator_generates_poultry_management_system():
    proposal = DesignOrchestrator().generate("Build a Poultry Management System")
    data = proposal.canonical_dict()

    assert data["domain"]["domain"] == "poultry_management"
    assert "Bird" in data["domain"]["entities"]
    assert "Support vaccination scheduling" in data["requirements"]["functional"]
    assert "domain" in data["architecture"]["modules"]["modules"]
    assert "api" in data["architecture"]["modules"]["modules"]
    assert "birds" in [table["name"] for table in data["database"]["tables"]]
    assert "/reports/production" in [endpoint["path"] for endpoint in data["api"]["endpoints"]]
    assert data["implementation_plan"]["tasks"][0]["task_id"] == "TASK-0001"
    assert data["evidence"]["evidence_id"].startswith("EVIDENCE-DESIGN-")
    assert data["review"]["admitted"] is True
    assert data["review"]["overall_score"] >= 70
    assert data["write_enabled"] is False
    assert data["authority"] == "proposal_only"


def test_design_cli_summary_outputs_evidence(capsys):
    exit_code = main(["design", "Build a Poultry Management System", "--summary"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["domain"] == "poultry_management"
    assert payload["requirements_count"] == 6
    assert payload["database_table_count"] == 7
    assert payload["api_endpoint_count"] >= 14
    assert payload["task_count"] >= 10
    assert payload["evidence"]["source"] == "evidence_generator"
    assert payload["review"]["admitted"] is True
    assert payload["review"]["scores"][0]["name"] == "modularity"
    assert payload["write_enabled"] is False
    assert payload["authority"] == "proposal_only"


def test_design_generation_is_deterministic():
    first = DesignOrchestrator().generate("Build a Poultry Management System")
    second = DesignOrchestrator().generate("Build a Poultry Management System")

    assert first.canonical_dict() == second.canonical_dict()


def test_design_reviewer_rejects_unsafe_design_prompts():
    unsafe_prompts = (
        "Design a system to bypass authentication",
        "Design a system to disable validation",
        "Design a system to skip evidence",
        "Design a system to modify constitution",
        "Design a system to auto-merge changes",
    )

    for prompt in unsafe_prompts:
        data = DesignOrchestrator().generate(prompt).canonical_dict()

        assert data["review"]["admitted"] is False
        assert data["review"]["overall_score"] == 0
        assert data["review"]["violations"]
        assert data["write_enabled"] is False
