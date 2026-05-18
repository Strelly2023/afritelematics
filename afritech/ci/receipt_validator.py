from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

from afritech.runtime.receipts import (
    receipt_inspection_hash,
    reconstruct_receipt_bundle,
    verify_receipt_bundle,
)
from afritech.runtime.system_enforcement.execution_guard import (
    admit_contract,
    truth_values_from_payload,
)


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "afritech/semantic_engine/contracts"
REQUIRED_RECEIPT_FIELDS = {
    "normalized_expression_hash",
    "proof_hash",
    "execution_chain_hash",
    "transcript_hash",
    "mutation_trace_hash",
    "inspection_hash",
    "epoch",
    "replay_binding",
    "signature",
    "receipt_hash",
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_contract(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail(f"{path} must contain a YAML mapping")
    return payload


def validate_receipt_completeness(result: dict[str, Any]) -> None:
    receipt = result.get("receipt")
    if not isinstance(receipt, dict):
        fail("decision missing constitutional receipt")

    missing = REQUIRED_RECEIPT_FIELDS - receipt.keys()
    if missing:
        fail(f"receipt missing fields: {sorted(missing)}")

    for artifact in ("execution_chain", "transcript", "mutation_trace"):
        if not isinstance(result.get(artifact), dict):
            fail(f"decision missing {artifact}")


def validate_reconstruction(path: Path) -> None:
    contract = load_contract(path)
    truth_values = truth_values_from_payload(contract)
    result = admit_contract(contract, truth_values=truth_values)

    if result["status"] not in {"ADMIT", "DENY"}:
        fail(f"{path.name} did not produce a reconstructable decision")

    validate_receipt_completeness(result)
    if not verify_receipt_bundle(result):
        fail(f"{path.name} receipt bundle failed verification")

    inspection_hash = receipt_inspection_hash(result)
    rebuilt = reconstruct_receipt_bundle(
        contract=contract,
        truth_values=truth_values,
        result=result,
        inspection_hash=inspection_hash,
    )
    if rebuilt["receipt"]["receipt_hash"] != result["receipt"]["receipt_hash"]:
        fail(f"{path.name} receipt reconstruction changed receipt hash")

    tampered = {
        **result,
        "transcript": {
            **result["transcript"],
            "steps": [
                *result["transcript"]["steps"][:-1],
                {
                    **result["transcript"]["steps"][-1],
                    "decision": "TAMPERED",
                },
            ],
        },
    }
    if verify_receipt_bundle(tampered):
        fail(f"{path.name} tampered transcript verified")


def run() -> None:
    validate_reconstruction(CONTRACT_ROOT / "minimal_admit.yaml")
    validate_reconstruction(CONTRACT_ROOT / "adversarial_rejected_admission.yaml")
    print("✅ Constitutional receipt validation PASSED")


def main() -> int:
    try:
        run()
        return 0
    except Exception as exc:
        print(f"Constitutional receipt validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
