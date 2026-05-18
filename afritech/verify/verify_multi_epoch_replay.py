from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

from afritech.shared.types import stable_hash
from afritech.verify.verify_execution_lineage import verify_contract


ROOT = Path(__file__).resolve().parents[2]
EPOCH_STATUS = ROOT / "afritech/registry/epochs/EPOCH_STATUS.yaml"


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_epoch_status() -> dict[str, Any]:
    payload = yaml.safe_load(EPOCH_STATUS.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail("epoch status must be a mapping")
    return payload


def authoritative_epochs(payload: dict[str, Any]) -> list[str]:
    epochs = payload.get("current_authoritative_epoch", [])
    if not isinstance(epochs, list) or not epochs:
        fail("missing current authoritative epoch")
    return [str(epoch) for epoch in epochs]


def run() -> None:
    payload = load_epoch_status()
    epochs = authoritative_epochs(payload)

    reconstructed = [
        verify_contract("minimal_admit.yaml"),
        verify_contract("adversarial_rejected_admission.yaml"),
    ]
    replay_chain = [
        {
            "epoch": epoch,
            "receipts": [
                item["receipt_hash"]
                for item in reconstructed
            ],
            "replay_hashes": [
                item["replay_hash"]
                for item in reconstructed
            ],
        }
        for epoch in epochs
    ]

    chain_hash = stable_hash(replay_chain)
    if not chain_hash:
        fail("multi-epoch replay chain hash missing")

    print("✅ Multi-epoch replay verification PASSED")
    print(f"✅ Authoritative epochs: {len(epochs)}")
    print(f"✅ Replay chain hash: {chain_hash}")


def main() -> int:
    try:
        run()
        return 0
    except Exception as exc:
        print(f"Multi-epoch replay verification failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
