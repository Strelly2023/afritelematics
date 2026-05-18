from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

from afritech.runtime.system_enforcement.execution_guard import (
    admit_contract,
    truth_values_from_payload,
)
from afritech.trace.trace_reconstructor import TraceReconstructor


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "afritech/semantic_engine/contracts"


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_contract(name: str) -> dict[str, Any]:
    payload = yaml.safe_load((CONTRACT_ROOT / name).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail(f"{name} must be a YAML mapping")
    return payload


def verify_contract(name: str) -> dict[str, Any]:
    contract = load_contract(name)
    result = admit_contract(contract, truth_values=truth_values_from_payload(contract))
    reconstructed = TraceReconstructor.reconstruct_receipt_bundle(result)

    if reconstructed["receipt_hash"] != result["receipt"]["receipt_hash"]:
        fail(f"{name} receipt hash mismatch")
    if reconstructed["replay_hash"] != result["receipt"]["replay_hash"]:
        fail(f"{name} replay hash mismatch")

    return reconstructed


def run() -> None:
    admitted = verify_contract("minimal_admit.yaml")
    denied = verify_contract("adversarial_rejected_admission.yaml")

    if admitted["decision"] != "ADMIT":
        fail("admit lineage did not reconstruct as ADMIT")
    if denied["decision"] != "DENY":
        fail("deny lineage did not reconstruct as DENY")

    print("✅ Execution lineage verification PASSED")


def main() -> int:
    try:
        run()
        return 0
    except Exception as exc:
        print(f"Execution lineage verification failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
