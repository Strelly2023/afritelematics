"""Validate driver lifecycle events bind to the driver API contract receipt."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DRIVER_VIEWS = ROOT / "afritech/api/afriride_driver_views.py"
CONTRACT_RECEIPT = ROOT / "afritech/proof/driver_api_contract_receipt.json"
CONTRACT_RECEIPT_MODULE = ROOT / "afritech/proof/contract_snapshot_receipt.py"
TEST_FILE = ROOT / "afritech/tests/api/test_afriride_driver_views.py"


class DriverEventContractBindingViolation(RuntimeError):
    """Raised when driver events are not contract-receipt bound."""


def validate() -> bool:
    for path in (DRIVER_VIEWS, CONTRACT_RECEIPT, CONTRACT_RECEIPT_MODULE, TEST_FILE):
        if not path.exists():
            raise DriverEventContractBindingViolation(f"missing required file: {path}")
    _validate_driver_view_binding()
    _validate_contract_receipt_builder()
    _validate_tests()
    return True


def _validate_driver_view_binding() -> None:
    source = DRIVER_VIEWS.read_text(encoding="utf-8")
    for needle in (
        "build_driver_api_contract_receipt",
        "_driver_api_contract_binding",
        '"contract_binding": contract_binding',
        "snapshot_hash",
        "contract_receipt_hash",
        "event_hash",
    ):
        if needle not in source:
            raise DriverEventContractBindingViolation(
                f"driver view missing contract binding text: {needle}"
            )
    tree = ast.parse(source, filename=str(DRIVER_VIEWS))
    helper_names = {
        node.name for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    if "_append_trust_event" not in helper_names or "_driver_api_contract_binding" not in helper_names:
        raise DriverEventContractBindingViolation("driver contract binding helpers missing")


def _validate_contract_receipt_builder() -> None:
    source = CONTRACT_RECEIPT_MODULE.read_text(encoding="utf-8")
    for needle in (
        "APIContractValidated",
        "snapshot_hash",
        "previous_receipt_hash",
        "receipt_hash",
        "truth_boundary",
    ):
        if needle not in source:
            raise DriverEventContractBindingViolation(
                f"contract receipt builder missing binding text: {needle}"
            )


def _validate_tests() -> None:
    source = TEST_FILE.read_text(encoding="utf-8")
    for needle in (
        "test_driver_lifecycle_events_include_contract_receipt_binding",
        "contract_binding",
        "contract_receipt_hash",
    ):
        if needle not in source:
            raise DriverEventContractBindingViolation(
                f"missing event contract binding test: {needle}"
            )


def main() -> int:
    try:
        validate()
    except DriverEventContractBindingViolation as exc:
        print(f"Driver event contract binding validation FAILED: {exc}")
        return 1
    print("Driver event contract binding validation PASSED")
    print("Ride lifecycle events carry driver API contract receipt hashes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
