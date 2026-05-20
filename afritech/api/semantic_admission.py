from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from afritech.core.runtime.system_enforcement.execution_guard import admit_contract
from afritech.semantic_engine.inspection import inspect_admission, mermaid_proof_graph


class SemanticAdmissionRequest(BaseModel):
    contract: dict[str, Any]
    truth_values: dict[str, bool] | None = None
    include_trace: bool = True
    include_inspection: bool = True


class SemanticAdmissionResponse(BaseModel):
    status: str
    program_id: str | None = None
    reason: str | None = None
    proof: dict[str, Any] | None = None
    trace: list[dict[str, Any]] = Field(default_factory=list)
    receipt: dict[str, Any] | None = None
    transcript: dict[str, Any] | None = None
    execution_chain: dict[str, Any] | None = None
    mutation_trace: dict[str, Any] | None = None
    inspection: dict[str, Any] | None = None


def admit_semantic_contract(request: SemanticAdmissionRequest) -> dict[str, Any]:
    result = admit_contract(request.contract, truth_values=request.truth_values)
    response = {
        "status": result["status"],
        "program_id": result.get("program_id"),
        "reason": result.get("reason"),
        "proof": result.get("proof"),
        "trace": result.get("trace", []) if request.include_trace else [],
        "receipt": result.get("receipt"),
        "transcript": result.get("transcript"),
        "execution_chain": result.get("execution_chain"),
        "mutation_trace": result.get("mutation_trace"),
    }
    if request.include_inspection:
        response["inspection"] = inspect_admission(result)
    return response


def create_semantic_admission_app() -> FastAPI:
    app = FastAPI(
        title="AfriTech Semantic Admission API",
        version="7.0.0-ga",
        description="Single-process constitutional semantic admission interface.",
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "OK",
            "system": "afritech-semantic-admission",
            "mode": "single_process_replay_authoritative",
        }

    @app.post("/semantic/admit", response_model=SemanticAdmissionResponse)
    def semantic_admit(request: SemanticAdmissionRequest) -> dict[str, Any]:
        return admit_semantic_contract(request)

    @app.post("/semantic/inspect")
    def semantic_inspect(request: SemanticAdmissionRequest) -> dict[str, Any]:
        result = admit_contract(request.contract, truth_values=request.truth_values)
        return inspect_admission(result)

    @app.post("/semantic/proof_graph")
    def semantic_proof_graph(request: SemanticAdmissionRequest) -> dict[str, str]:
        result = admit_contract(request.contract, truth_values=request.truth_values)
        return {"format": "mermaid", "graph": mermaid_proof_graph(result)}

    return app


app = create_semantic_admission_app()
