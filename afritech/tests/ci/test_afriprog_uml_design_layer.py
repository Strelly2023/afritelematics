from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from afritech.ci import (
    afriprog_uml_consistency_validator,
    afriprog_uml_non_authority_validator,
    afriprog_uml_structure_validator,
    afriprog_uml_to_proposal_validator,
)
from afritech.design.uml import parse_uml, uml_to_proposal, validate_uml_design


ROOT = Path(__file__).resolve().parents[3]


def test_class_diagram_is_design_time_only() -> None:
    model = parse_uml("Customer\n- name\n- email\n+ placeOrder()", diagram_type="class")

    assert model["diagram_type"] == "class"
    assert model["authority"] == "design_time_non_authoritative"
    assert model["runtime_mutation_allowed"] is False
    assert model["classes"][0]["name"] == "Customer"
    assert model["classes"][0]["attributes"] == ["name", "email"]
    assert model["classes"][0]["methods"] == ["placeOrder()"]


def test_supported_uml_diagrams_validate_without_authority() -> None:
    cases = (
        ("sequence", "User -> OrderService: placeOrder"),
        ("activity", "Collect Eggs -> Sort -> Store -> Sell"),
        ("state", "Pending -> Paid\nPaid -> Shipped"),
    )

    for diagram_type, source in cases:
        validation = validate_uml_design(parse_uml(source, diagram_type=diagram_type))

        assert validation["valid"] is True
        assert validation["governance_required"] is True
        assert validation["activation_allowed"] is False
        assert validation["runtime_mutation_allowed"] is False


def test_uml_to_proposal_remains_governance_ready_only() -> None:
    model = parse_uml("Chicken\n- age\n- weight\n+ layEgg()", diagram_type="class")
    proposal = uml_to_proposal(model)
    proposal_payload = proposal.canonical_dict()

    assert "Chicken" in proposal_payload["intent"]
    assert proposal_payload["governance_required"] is True
    assert proposal_payload["activation_allowed"] is False
    assert proposal_payload["runtime_mutation_allowed"] is False
    assert proposal_payload["replay_required"] is True
    assert proposal_payload["rollback_required"] is True


def test_uml_cli_surfaces_emit_blocked_design_payloads() -> None:
    source = "Customer\n- name\n+ placeOrder()"

    parse_payload = _run_cli_json("uml-parse", source, "--diagram-type", "class")
    assert parse_payload["activation_allowed"] is False
    assert parse_payload["uml_model"]["runtime_mutation_allowed"] is False

    validate_payload = _run_cli_json("uml-validate", source, "--diagram-type", "class")
    assert validate_payload["validation"]["valid"] is True
    assert validate_payload["validation"]["governance_required"] is True
    assert validate_payload["validation"]["activation_allowed"] is False

    propose_payload = _run_cli_json("uml-propose", source, "--diagram-type", "class")
    assert propose_payload["governance_review_required"] is True
    assert propose_payload["activation_allowed"] is False
    assert propose_payload["runtime_mutation_allowed"] is False
    assert propose_payload["proposal"]["runtime_mutation_allowed"] is False


def test_uml_validators_pass_directly() -> None:
    afriprog_uml_structure_validator.validate()
    afriprog_uml_to_proposal_validator.validate()
    afriprog_uml_non_authority_validator.validate()
    afriprog_uml_consistency_validator.validate()


def _run_cli_json(*args: str) -> dict[str, object]:
    completed = subprocess.run(
        (sys.executable, "-m", "afritech.cli.main", *args, "--json"),
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return json.loads(completed.stdout)
