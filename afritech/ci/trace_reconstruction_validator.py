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
CRITICAL_SURFACES = (
    ROOT / "afritech/trace/trace_reconstructor.py",
    ROOT / "afritech/proof/witness/transcript_witness.py",
    ROOT / "afritech/proof/witness/mutation_witness.py",
    ROOT / "afritech/proof/constitutional_receipt.json",
    ROOT / "afritech/proof/witness_bundle.json",
)


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_contract(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail(f"{path} must be a YAML mapping")
    return payload


def validate_contract(path: Path) -> None:
    contract = load_contract(path)
    result = admit_contract(
        contract,
        truth_values=truth_values_from_payload(contract),
    )
    reconstructed = TraceReconstructor.reconstruct_receipt_bundle(result)

    receipt = result["receipt"]
    required_pairs = {
        "execution_chain_hash": receipt["execution_chain_hash"],
        "transcript_hash": receipt["transcript_hash"],
        "mutation_trace_hash": receipt["mutation_trace_hash"],
        "replay_hash": receipt["replay_hash"],
        "receipt_hash": receipt["receipt_hash"],
    }

    for field, expected in required_pairs.items():
        if reconstructed[field] != expected:
            fail(f"{path.name} reconstruction mismatch: {field}")


def validate_no_partial_replay_critical_surfaces() -> None:
    forbidden = ("PLANNED", "PARTIAL")
    for path in CRITICAL_SURFACES:
        text = path.read_text(encoding="utf-8")
        for marker in forbidden:
            if marker in text:
                fail(f"replay-critical surface still {marker}: {path}")


def run() -> None:
    validate_no_partial_replay_critical_surfaces()
    validate_contract(CONTRACT_ROOT / "minimal_admit.yaml")
    validate_contract(CONTRACT_ROOT / "adversarial_rejected_admission.yaml")
    print("✅ Trace reconstruction validation PASSED")


def main() -> int:
    try:
        run()
        return 0
    except Exception as exc:
        print(f"Trace reconstruction validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
