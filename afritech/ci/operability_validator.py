from __future__ import annotations

import sys

from afritech.api.semantic_admission import (
    SemanticAdmissionRequest,
    admit_semantic_contract,
    create_semantic_admission_app,
)
from afritech.sdk.semantic_admission import SemanticAdmissionClient


CONTRACT = {
    "id": "ga_operability_contract",
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


def fail(message: str) -> None:
    raise RuntimeError(message)


def validate_api_routes() -> None:
    app = create_semantic_admission_app()
    paths = {route.path for route in app.routes}
    required = {
        "/health",
        "/semantic/admit",
        "/semantic/inspect",
        "/semantic/proof_graph",
    }
    missing = required - paths
    if missing:
        fail(f"semantic admission API missing routes: {sorted(missing)}")


def validate_api_admission() -> None:
    response = admit_semantic_contract(SemanticAdmissionRequest(contract=CONTRACT))
    if response["status"] != "ADMIT":
        fail("semantic admission API did not admit valid contract")
    if not response.get("proof", {}).get("proof_hash"):
        fail("semantic admission API did not emit proof hash")
    if response.get("inspection", {}).get("trace_complete") is not True:
        fail("semantic admission API did not emit complete trace inspection")


def validate_sdk() -> None:
    response = SemanticAdmissionClient().admit(CONTRACT, inspect=True)
    if response["result"]["status"] != "ADMIT":
        fail("semantic SDK did not admit valid contract")
    if response["inspection"]["proof"]["present"] is not True:
        fail("semantic SDK did not expose proof inspection")


def run() -> None:
    validate_api_routes()
    validate_api_admission()
    validate_sdk()
    print("Semantic operability validation PASSED")


def main() -> int:
    try:
        run()
        return 0
    except Exception as exc:
        print(f"Semantic operability validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
