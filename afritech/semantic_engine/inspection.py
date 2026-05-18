from __future__ import annotations

from typing import Any

from afritech.shared.types import stable_hash


CANONICAL_TRACE_ORDER = [
    "compile",
    "normalize",
    "hash",
    "evaluate",
    "proof",
    "admission_gate",
]


def trace_timeline(trace: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "index": index,
            "stage": entry.get("stage"),
            "decision": entry.get("decision"),
            "reason": entry.get("reason"),
            "hash": entry.get("normalized_expression_hash") or entry.get("proof_hash"),
        }
        for index, entry in enumerate(trace)
    ]


def proof_view(proof: dict[str, Any] | None) -> dict[str, Any]:
    if not proof:
        return {
            "present": False,
            "proof_hash": None,
            "normalized_expression_hash": None,
            "evaluated": None,
            "dependency_count": 0,
        }

    dependencies = proof.get("dependency_graph", [])
    return {
        "present": True,
        "proof_hash": proof.get("proof_hash"),
        "normalized_expression_hash": proof.get("normalized_expression_hash"),
        "evaluated": proof.get("evaluated"),
        "pipeline": proof.get("pipeline"),
        "dependency_count": len(dependencies) if isinstance(dependencies, list) else 0,
    }


def proof_graph(proof: dict[str, Any] | None) -> dict[str, Any]:
    if not proof:
        return {"nodes": [], "edges": []}

    expression_hash = proof.get("normalized_expression_hash")
    proof_hash = proof.get("proof_hash")
    nodes = [
        {"id": "normalized_s_ir", "label": "Normalized S-IR", "hash": expression_hash},
        {"id": "proof", "label": "Proof", "hash": proof_hash},
        {"id": "decision", "label": "Admission Decision", "value": proof.get("evaluated")},
    ]
    edges = [
        {"source": "normalized_s_ir", "target": "proof", "label": "hash-bound"},
        {"source": "proof", "target": "decision", "label": "validates"},
    ]
    return {"nodes": nodes, "edges": edges}


def inspect_admission(result: dict[str, Any]) -> dict[str, Any]:
    trace = result.get("trace", [])
    stages = [entry.get("stage") for entry in trace]
    inspection = {
        "status": result.get("status"),
        "program_id": result.get("program_id"),
        "reason": result.get("reason"),
        "trace_complete": stages == CANONICAL_TRACE_ORDER,
        "trace_stages": stages,
        "timeline": trace_timeline(trace),
        "proof": proof_view(result.get("proof")),
        "proof_graph": proof_graph(result.get("proof")),
    }
    inspection["inspection_hash"] = stable_hash(inspection)
    return inspection


def mermaid_proof_graph(result: dict[str, Any]) -> str:
    graph = proof_graph(result.get("proof"))
    if not graph["nodes"]:
        return "flowchart TD\n  invalid[\"SYSTEM_INVALID\"]"

    status = result.get("status", "UNKNOWN")
    return "\n".join(
        [
            "flowchart TD",
            '  sir["Normalized S-IR"]',
            '  proof["Proof Artifact"]',
            f'  decision["{status}"]',
            "  sir --> proof",
            "  proof --> decision",
        ]
    )
