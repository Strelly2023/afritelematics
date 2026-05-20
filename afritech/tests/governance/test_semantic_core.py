import pytest

from afritech.core.runtime.system_enforcement.execution_guard import admit_contract, admit_semantic_yaml
from afritech.semantic_engine.cli import main as semantic_cli
from afritech.semantic_engine.ir.schema import SystemInvalid
from afritech.semantic_engine.parser.ir_builder import compile_semantic_yaml
from afritech.semantic_engine.proof.proof_builder import validate_proof
from afritech.semantic_engine.satisfiability.solver import admissible


CONTRACT_ROOT = "afritech/semantic_engine/contracts"


def test_admits_normalized_semantic_program():
    source = {
        "id": "mvp_admission",
        "declared_symbols": ["request_valid", "driver_available", "can_assign"],
        "expression": {
            "operator": "AND",
            "operands": [
                {
                    "operator": "REQUIRES",
                    "operands": ["can_assign", "driver_available"],
                },
                {
                    "operator": "EQUIVALENT",
                    "operands": ["request_valid", "request_valid"],
                },
            ],
        },
    }

    admitted, proof = admit_semantic_yaml(
        source,
        {
            "request_valid": True,
            "driver_available": True,
            "can_assign": True,
        },
    )

    assert admitted is True
    assert proof["evaluated"] is True
    assert proof["normalized"] is True
    assert proof["pipeline"] == "compile.normalize.hash.evaluate.proof"
    assert proof["normalized_expression_hash"]
    assert proof["proof_hash"]


def test_rejects_undeclared_symbol():
    source = {
        "id": "undeclared_symbol",
        "declared_symbols": ["request_valid"],
        "expression": {
            "operator": "AND",
            "operands": ["request_valid", "driver_available"],
        },
    }

    with pytest.raises(SystemInvalid, match="undeclared_symbol:driver_available"):
        admit_semantic_yaml(source, {"request_valid": True, "driver_available": True})


def test_rejects_unsupported_operator():
    source = {
        "id": "unsupported_operator",
        "declared_symbols": ["a", "b"],
        "expression": {
            "operator": "OR",
            "operands": ["a", "b"],
        },
    }

    with pytest.raises(SystemInvalid, match="unsupported_operator:OR"):
        admit_semantic_yaml(source, {"a": True, "b": True})


def test_forall_quantifies_declared_domain():
    source = {
        "id": "forall_domain",
        "declared_symbols": ["rider_verified", "driver_verified"],
        "expression": {
            "operator": "FORALL",
            "operands": [
                "party",
                ["rider_verified", "driver_verified"],
                "party",
            ],
        },
    }

    admitted, proof = admit_semantic_yaml(
        source,
        {"rider_verified": True, "driver_verified": True},
    )

    assert admitted is True
    assert proof["evaluated"] is True


def test_rejects_tampered_proof():
    source = {
        "id": "tampered_proof",
        "declared_symbols": ["request_valid"],
        "expression": "request_valid",
    }
    program = compile_semantic_yaml(source)
    result, proof, normalized = admissible(
        program.expression,
        {"request_valid": True},
        program.declared_symbols,
    )

    assert result is True
    proof["evaluated"] = False

    with pytest.raises(SystemInvalid, match="proof_invalid"):
        validate_proof(proof, normalized)


def test_contract_file_admits_with_observability_trace():
    result = admit_contract(f"{CONTRACT_ROOT}/minimal_admit.yaml")

    assert result["status"] == "ADMIT"
    assert result["program_id"] == "minimal_assignment_admission"
    assert result["proof"]["proof_hash"]
    assert [entry["stage"] for entry in result["trace"]] == [
        "compile",
        "normalize",
        "hash",
        "evaluate",
        "proof",
        "admission_gate",
    ]
    assert result["trace"][-1]["decision"] == "ADMIT"


@pytest.mark.parametrize(
    ("contract", "reason"),
    [
        ("adversarial_undeclared_symbol.yaml", "undeclared_symbol:driver_available"),
        ("adversarial_unsupported_operator.yaml", "unsupported_operator:OR"),
    ],
)
def test_adversarial_contracts_fail_for_declared_reasons(contract, reason):
    result = admit_contract(f"{CONTRACT_ROOT}/{contract}")

    assert result["status"] == "SYSTEM_INVALID"
    assert result["reason"] == reason
    assert result["trace"][-1]["decision"] == "SYSTEM_INVALID"


def test_denial_contract_returns_valid_proof_of_rejection():
    result = admit_contract(f"{CONTRACT_ROOT}/adversarial_rejected_admission.yaml")

    assert result["status"] == "DENY"
    assert result["reason"] == "execution_not_admissible"
    assert result["proof"]["evaluated"] is False
    assert result["proof"]["normalized"] is True
    assert result["proof"]["normalized_expression_hash"]
    assert result["proof"]["proof_hash"]
    assert [entry["stage"] for entry in result["trace"]] == [
        "compile",
        "normalize",
        "hash",
        "evaluate",
        "proof",
        "admission_gate",
    ]
    assert result["trace"][-1]["decision"] == "DENY"


def test_semantic_cli_admits_contract(capsys):
    exit_code = semantic_cli([f"{CONTRACT_ROOT}/minimal_admit.yaml", "--pretty"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert '"status": "ADMIT"' in captured.out
    assert "proof_hash" in captured.out


def test_semantic_cli_denies_contract_with_distinct_exit_code(capsys):
    exit_code = semantic_cli([f"{CONTRACT_ROOT}/adversarial_rejected_admission.yaml"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "DENY" in captured.out
    assert "execution_not_admissible" in captured.out
    assert "proof_hash" in captured.out


def test_semantic_cli_rejects_bad_contract(capsys):
    exit_code = semantic_cli([f"{CONTRACT_ROOT}/adversarial_undeclared_symbol.yaml"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "SYSTEM_INVALID" in captured.out
    assert "undeclared_symbol:driver_available" in captured.out
