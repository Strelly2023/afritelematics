"""Validate the driver API contract snapshot receipt."""

from __future__ import annotations

import sys

from afritech.proof.contract_snapshot_receipt import (
    ContractSnapshotReceiptError,
    build_driver_api_contract_receipt,
    verify_driver_api_contract_receipt,
)


def validate() -> bool:
    receipt = build_driver_api_contract_receipt().canonical_dict()
    if receipt["event_type"] != "APIContractValidated":
        raise ContractSnapshotReceiptError("driver API contract receipt event type mismatch")
    if receipt["status"] != "MATCH":
        raise ContractSnapshotReceiptError("driver API contract receipt status mismatch")
    if receipt["signature"]["mode"] != "deterministic_local_contract_signature":
        raise ContractSnapshotReceiptError("driver API contract receipt signature mode mismatch")
    return verify_driver_api_contract_receipt(receipt)


def main() -> int:
    try:
        receipt = build_driver_api_contract_receipt()
        validate()
    except ContractSnapshotReceiptError as exc:
        print(f"Driver API contract receipt validation FAILED: {exc}")
        return 1
    print("Driver API contract receipt validation PASSED")
    print(f"snapshot_hash={receipt.snapshot_hash}")
    print(f"event_hash={receipt.event_hash}")
    print(f"receipt_hash={receipt.receipt_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
