from pathlib import Path

from afritech.api.semantic_admission import (
    SemanticAdmissionRequest,
    admit_semantic_contract,
    create_semantic_admission_app,
)
from afritech.runtime.system_enforcement.execution_guard import admit_contract
from afritech.sdk.semantic_admission import SemanticAdmissionClient
from afritech.semantic_engine.inspection import inspect_admission, mermaid_proof_graph
from afritech.tools.proof_viewer import load_result_or_contract, main as proof_viewer_main


CONTRACT = {
    "id": "operability_admission",
    "declared_symbols": ["request_valid", "driver_available", "can_assign"],
    "truth_values": {
        "request_valid": True,
        "driver_available": True,
        "can_assign": True,
    },
    "expression": {
        "operator": "AND",
        "operands": [
            {
                "operator": "REQUIRES",
                "operands": ["can_assign", "driver_available"],
            },
            "request_valid",
        ],
    },
}


def test_inspection_view_is_hash_bound_and_trace_aware():
    result = admit_contract(CONTRACT)
    inspection = inspect_admission(result)

    assert inspection["status"] == "ADMIT"
    assert inspection["trace_complete"] is True
    assert inspection["proof"]["present"] is True
    assert inspection["proof_graph"]["nodes"]
    assert inspection["inspection_hash"]


def test_mermaid_proof_graph_is_generated():
    result = admit_contract(CONTRACT)
    graph = mermaid_proof_graph(result)

    assert graph.startswith("flowchart TD")
    assert "Normalized S-IR" in graph
    assert "Proof Artifact" in graph


def test_semantic_admission_api_handler_returns_operable_payload():
    response = admit_semantic_contract(SemanticAdmissionRequest(contract=CONTRACT))

    assert response["status"] == "ADMIT"
    assert response["program_id"] == "operability_admission"
    assert response["proof"]["proof_hash"]
    assert response["inspection"]["trace_complete"] is True


def test_semantic_admission_api_handler_returns_denial_proof():
    denied = {
        **CONTRACT,
        "truth_values": {
            "request_valid": True,
            "driver_available": False,
            "can_assign": True,
        },
    }

    response = admit_semantic_contract(SemanticAdmissionRequest(contract=denied))

    assert response["status"] == "DENY"
    assert response["reason"] == "execution_not_admissible"
    assert response["proof"]["evaluated"] is False
    assert response["inspection"]["trace_complete"] is True
    assert response["inspection"]["proof"]["present"] is True
    assert 'decision["DENY"]' in mermaid_proof_graph(response)


def test_semantic_admission_app_exposes_ga_routes():
    app = create_semantic_admission_app()
    paths = {route.path for route in app.routes}

    assert "/health" in paths
    assert "/semantic/admit" in paths
    assert "/semantic/inspect" in paths
    assert "/semantic/proof_graph" in paths


def test_sdk_client_runs_local_admission_with_inspection():
    client = SemanticAdmissionClient()
    response = client.admit(CONTRACT, inspect=True)

    assert response["result"]["status"] == "ADMIT"
    assert response["inspection"]["proof"]["present"] is True


def test_sdk_prepares_external_api_payload_without_semantic_interpretation():
    client = SemanticAdmissionClient()
    payload = client.prepare_api_payload(CONTRACT)

    assert payload["contract"] == CONTRACT
    assert payload["truth_values"] is None
    assert payload["include_trace"] is True


def test_proof_viewer_reads_contract_and_prints_summary(capsys):
    exit_code = proof_viewer_main(
        [
            "afritech/semantic_engine/contracts/minimal_admit.yaml",
            "--format",
            "summary",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "status: ADMIT" in captured.out
    assert "proof_hash:" in captured.out


def test_proof_viewer_reads_denial_contract_and_prints_rejection_proof(capsys):
    exit_code = proof_viewer_main(
        [
            "afritech/semantic_engine/contracts/adversarial_rejected_admission.yaml",
            "--format",
            "summary",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "status: DENY" in captured.out
    assert "reason: execution_not_admissible" in captured.out
    assert "proof_present: True" in captured.out


def test_proof_viewer_reads_api_example_payload():
    result = load_result_or_contract(
        Path("afritech/api/examples/semantic_admission_request.json")
    )

    assert result["status"] == "ADMIT"
