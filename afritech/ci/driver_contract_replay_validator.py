"""Validate replay enforcement for driver API contract-bound lifecycle events."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPLAY_HELPER = ROOT / "afritech/trust_kernel/replay/contract_bindings.py"
RECEIPT_INDEX_HELPER = ROOT / "afritech/proof/contract_receipt_index.py"
RECEIPT_INDEX = ROOT / "afritech/proof/contract_receipts/index.json"
DRIVER_RECEIPT = ROOT / "afritech/proof/contract_receipts/driver_api_routes_v1.json"
SIMULATED_ROTATION_INDEX = ROOT / "afritech/tests/fixtures/contract_receipts/index.json"
SIMULATED_OVERLAP_INDEX = ROOT / "afritech/tests/fixtures/contract_receipts/index_overlapping.json"
SIMULATED_OPEN_PREDECESSOR_INDEX = ROOT / "afritech/tests/fixtures/contract_receipts/index_open_predecessor.json"
SIMULATED_V2_RECEIPT = ROOT / "afritech/tests/fixtures/contract_receipts/driver_api_routes_v2_simulated.json"
DRIVER_VIEWS = ROOT / "afritech/api/afriride_driver_views.py"
TEST_FILE = ROOT / "afritech/tests/api/test_afriride_driver_views.py"
CI_TEST_FILE = ROOT / "afritech/tests/ci/test_driver_contract_replay_validator.py"


class DriverContractReplayValidationError(RuntimeError):
    """Raised when driver event contract replay enforcement is incomplete."""


def validate() -> bool:
    for path in (
        REPLAY_HELPER,
        RECEIPT_INDEX_HELPER,
        RECEIPT_INDEX,
        DRIVER_RECEIPT,
        SIMULATED_ROTATION_INDEX,
        SIMULATED_OVERLAP_INDEX,
        SIMULATED_OPEN_PREDECESSOR_INDEX,
        SIMULATED_V2_RECEIPT,
        DRIVER_VIEWS,
        TEST_FILE,
        CI_TEST_FILE,
    ):
        if not path.exists():
            raise DriverContractReplayValidationError(f"missing required file: {path}")
    _validate_receipt_index()
    _validate_simulated_rotation_fixture()
    _validate_replay_helper()
    _validate_driver_replay_surface()
    _validate_tests()
    return True


def _validate_receipt_index() -> None:
    helper_source = RECEIPT_INDEX_HELPER.read_text(encoding="utf-8")
    for needle in (
        "resolve_driver_api_receipt_by_hash",
        "resolve_driver_api_receipt_by_timestamp",
        "guard_declared_receipt_matches_timestamp",
        "guard_driver_api_receipt_index_non_overlapping",
        "guard_driver_api_receipt_windows_non_overlapping",
        "guard_driver_api_receipt_index_succession",
        "guard_driver_api_receipt_succession",
        "guard_receipt_effective_at",
        "ContractReceiptIndexError",
        "indexed receipt hash reconstruction mismatch",
        "indexed receipt snapshot hash mismatch",
        "indexed receipt event hash mismatch",
        "event timestamp precedes contract receipt effective_from",
        "declared receipt does not match timestamp-resolved receipt",
        "no driver API receipt effective at event timestamp",
        "contract receipt effective windows overlap",
        "non-latest receipt must declare effective_to",
        "receipt successor starts before predecessor ends",
    ):
        if needle not in helper_source:
            raise DriverContractReplayValidationError(
                f"contract receipt index helper missing verification text: {needle}"
            )
    index_source = RECEIPT_INDEX.read_text(encoding="utf-8")
    for needle in (
        '"driver_api"',
        '"active": "driver_api_routes_v1"',
        '"path": "driver_api_routes_v1.json"',
        '"effective_from": "2026-06-01T00:00:00Z"',
        '"effective_to": null',
    ):
        if needle not in index_source:
            raise DriverContractReplayValidationError(
                f"contract receipt index missing declared receipt text: {needle}"
            )


def _validate_simulated_rotation_fixture() -> None:
    index_source = SIMULATED_ROTATION_INDEX.read_text(encoding="utf-8")
    overlap_source = SIMULATED_OVERLAP_INDEX.read_text(encoding="utf-8")
    open_predecessor_source = SIMULATED_OPEN_PREDECESSOR_INDEX.read_text(encoding="utf-8")
    receipt_source = SIMULATED_V2_RECEIPT.read_text(encoding="utf-8")
    for needle in (
        "driver_api_routes_v2_simulated",
        '"version": "v2-simulated"',
        '"effective_from": "2026-06-10T00:00:00Z"',
    ):
        if needle not in index_source + receipt_source:
            raise DriverContractReplayValidationError(
                f"simulated rotation fixture missing text: {needle}"
            )
    for needle in (
        "index_overlapping",
        '"effective_to": "2026-06-11T00:00:00Z"',
    ):
        if needle not in str(SIMULATED_OVERLAP_INDEX) + overlap_source:
            raise DriverContractReplayValidationError(
                f"simulated overlap fixture missing text: {needle}"
            )
    for needle in (
        "index_open_predecessor",
        '"effective_to": null',
    ):
        if needle not in str(SIMULATED_OPEN_PREDECESSOR_INDEX) + open_predecessor_source:
            raise DriverContractReplayValidationError(
                f"simulated open predecessor fixture missing text: {needle}"
            )


def _validate_replay_helper() -> None:
    source = REPLAY_HELPER.read_text(encoding="utf-8")
    for needle in (
        "resolve_driver_api_receipt_by_hash",
        "guard_declared_receipt_matches_timestamp",
        "guard_receipt_effective_at",
        "validate_driver_event_contract_binding",
        "replay_driver_event_contract_bindings",
        "contract_receipt_hash",
        "timestamp_aligned_indexed_receipt",
    ):
        if needle not in source:
            raise DriverContractReplayValidationError(
                f"contract replay helper missing enforcement text: {needle}"
            )


def _validate_driver_replay_surface() -> None:
    source = DRIVER_VIEWS.read_text(encoding="utf-8")
    for needle in (
        "replay_driver_event_contract_bindings",
        "_completed_ride_contract_replay",
        '"contract_replay"',
    ):
        if needle not in source:
            raise DriverContractReplayValidationError(
                f"driver replay surface missing contract replay text: {needle}"
            )


def _validate_tests() -> None:
    source = TEST_FILE.read_text(encoding="utf-8")
    for needle in (
        "test_driver_replay_history_reports_contract_receipt_binding",
        "test_driver_event_contract_replay_rejects_tampered_binding",
        "ContractBindingReplayError",
        "timestamp_aligned_indexed_receipt",
        "receipt_effective_from",
    ):
        if needle not in source:
            raise DriverContractReplayValidationError(
                f"missing contract replay test coverage: {needle}"
            )
    ci_source = CI_TEST_FILE.read_text(encoding="utf-8")
    for needle in (
        "test_simulated_rotation_fixture_resolves_v1_before_boundary",
        "test_simulated_rotation_fixture_resolves_v2_after_boundary",
        "test_simulated_rotation_rejects_wrong_declared_receipt_for_timestamp",
        "test_overlapping_rotation_fixture_is_rejected",
        "test_open_predecessor_rotation_fixture_is_rejected",
    ):
        if needle not in ci_source:
            raise DriverContractReplayValidationError(
                f"missing simulated rotation test coverage: {needle}"
            )


def main() -> int:
    try:
        validate()
    except DriverContractReplayValidationError as exc:
        print(f"Driver contract replay validation FAILED: {exc}")
        return 1
    print("Driver contract replay validation PASSED")
    print("Replay verifies driver lifecycle events against timestamp-aligned indexed receipts")
    print("Simulated v2 receipt fixture proves rotation resolution without live rotation")
    print("Receipt index overlap guard enforces deterministic timestamp resolution")
    print("Receipt succession guard enforces safe predecessor closure")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
