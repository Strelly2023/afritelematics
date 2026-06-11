from __future__ import annotations

import subprocess
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from afritech.ci import driver_contract_replay_validator
from afritech.proof.contract_receipt_index import (
    ContractReceiptIndexError,
    guard_declared_receipt_matches_timestamp,
    guard_driver_api_receipt_index_non_overlapping,
    guard_driver_api_receipt_index_succession,
    guard_receipt_effective_at,
    resolve_driver_api_receipt_by_hash,
    resolve_driver_api_receipt_by_timestamp,
)
from afritech.proof.contract_snapshot_receipt import build_driver_api_contract_receipt

import pytest


FIXTURE_RECEIPTS_DIR = Path(__file__).resolve().parents[1] / "fixtures/contract_receipts"
FIXTURE_RECEIPT_INDEX = FIXTURE_RECEIPTS_DIR / "index.json"
FIXTURE_OVERLAPPING_RECEIPT_INDEX = FIXTURE_RECEIPTS_DIR / "index_overlapping.json"
FIXTURE_OPEN_PREDECESSOR_INDEX = FIXTURE_RECEIPTS_DIR / "index_open_predecessor.json"


def test_driver_contract_replay_validator_passes():
    assert driver_contract_replay_validator.validate() is True


def test_driver_contract_replay_validator_cli_passes():
    result = subprocess.run(
        [sys.executable, "-m", "afritech.ci.driver_contract_replay_validator"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Driver contract replay validation PASSED" in result.stdout


def test_driver_receipt_index_resolves_declared_receipt_hash():
    expected = build_driver_api_contract_receipt()
    indexed = resolve_driver_api_receipt_by_hash(expected.receipt_hash)

    assert indexed.receipt_id == "driver_api_routes_v1"
    assert indexed.contract == expected.contract
    assert indexed.version == expected.version
    assert indexed.snapshot_hash == expected.snapshot_hash
    assert indexed.event_hash == expected.event_hash
    assert indexed.receipt_hash == expected.receipt_hash
    assert indexed.effective_from_iso == "2026-06-01T00:00:00Z"
    assert indexed.effective_to_iso is None


def test_driver_receipt_index_accepts_event_inside_effective_window():
    expected = build_driver_api_contract_receipt()
    indexed = resolve_driver_api_receipt_by_hash(expected.receipt_hash)

    guard_receipt_effective_at(
        indexed,
        datetime(2026, 6, 5, 16, 0, tzinfo=timezone.utc),
    )


def test_driver_receipt_index_resolves_expected_receipt_by_timestamp():
    expected = build_driver_api_contract_receipt()
    indexed = resolve_driver_api_receipt_by_timestamp(
        datetime(2026, 6, 5, 16, 0, tzinfo=timezone.utc)
    )

    assert indexed.receipt_hash == expected.receipt_hash
    assert indexed.receipt_id == "driver_api_routes_v1"


def test_driver_receipt_index_requires_declared_receipt_to_match_timestamp():
    expected = build_driver_api_contract_receipt()
    indexed = resolve_driver_api_receipt_by_hash(expected.receipt_hash)

    guard_declared_receipt_matches_timestamp(
        indexed,
        datetime(2026, 6, 5, 16, 0, tzinfo=timezone.utc),
    )


def test_driver_receipt_index_rejects_declared_receipt_mismatch_for_timestamp():
    expected = build_driver_api_contract_receipt()
    indexed = resolve_driver_api_receipt_by_hash(expected.receipt_hash)
    wrong_declared = replace(indexed, receipt_hash="1" * 64)

    with pytest.raises(
        ContractReceiptIndexError,
        match="declared receipt does not match timestamp-resolved receipt",
    ):
        guard_declared_receipt_matches_timestamp(
            wrong_declared,
            datetime(2026, 6, 5, 16, 0, tzinfo=timezone.utc),
        )


def test_driver_receipt_index_rejects_event_before_effective_window():
    expected = build_driver_api_contract_receipt()
    indexed = resolve_driver_api_receipt_by_hash(expected.receipt_hash)

    with pytest.raises(
        ContractReceiptIndexError,
        match="event timestamp precedes contract receipt effective_from",
    ):
        guard_receipt_effective_at(
            indexed,
            datetime(2026, 5, 31, 23, 59, tzinfo=timezone.utc),
        )


def test_driver_receipt_index_rejects_timestamp_without_receipt_window():
    with pytest.raises(
        ContractReceiptIndexError,
        match="no driver API receipt effective at event timestamp",
    ):
        resolve_driver_api_receipt_by_timestamp(
            datetime(2026, 5, 31, 23, 59, tzinfo=timezone.utc)
        )


def test_driver_receipt_index_rejects_unknown_receipt_hash():
    with pytest.raises(
        ContractReceiptIndexError,
        match="declared contract receipt hash not found in index",
    ):
        resolve_driver_api_receipt_by_hash("0" * 64)


def test_production_driver_receipt_index_has_no_overlapping_windows():
    guard_driver_api_receipt_index_non_overlapping()


def test_production_driver_receipt_index_has_valid_succession():
    guard_driver_api_receipt_index_succession()


def test_simulated_rotation_fixture_has_adjacent_non_overlapping_windows():
    guard_driver_api_receipt_index_non_overlapping(
        index_path=FIXTURE_RECEIPT_INDEX,
        receipts_dir=FIXTURE_RECEIPTS_DIR,
    )


def test_simulated_rotation_fixture_has_valid_receipt_succession():
    guard_driver_api_receipt_index_succession(
        index_path=FIXTURE_RECEIPT_INDEX,
        receipts_dir=FIXTURE_RECEIPTS_DIR,
    )


def test_overlapping_rotation_fixture_is_rejected():
    with pytest.raises(
        ContractReceiptIndexError,
        match="contract receipt effective windows overlap",
    ):
        guard_driver_api_receipt_index_non_overlapping(
            index_path=FIXTURE_OVERLAPPING_RECEIPT_INDEX,
            receipts_dir=FIXTURE_RECEIPTS_DIR,
        )


def test_open_predecessor_rotation_fixture_is_rejected():
    with pytest.raises(
        ContractReceiptIndexError,
        match="non-latest receipt must declare effective_to",
    ):
        guard_driver_api_receipt_index_succession(
            index_path=FIXTURE_OPEN_PREDECESSOR_INDEX,
            receipts_dir=FIXTURE_RECEIPTS_DIR,
        )


def test_simulated_rotation_fixture_resolves_v1_before_boundary():
    indexed = resolve_driver_api_receipt_by_timestamp(
        datetime(2026, 6, 5, 16, 0, tzinfo=timezone.utc),
        index_path=FIXTURE_RECEIPT_INDEX,
        receipts_dir=FIXTURE_RECEIPTS_DIR,
    )

    assert indexed.receipt_id == "driver_api_routes_v1"
    assert indexed.version == "v1"


def test_simulated_rotation_fixture_resolves_v2_after_boundary():
    indexed = resolve_driver_api_receipt_by_timestamp(
        datetime(2026, 6, 10, 0, 0, tzinfo=timezone.utc),
        index_path=FIXTURE_RECEIPT_INDEX,
        receipts_dir=FIXTURE_RECEIPTS_DIR,
    )

    assert indexed.receipt_id == "driver_api_routes_v2_simulated"
    assert indexed.version == "v2-simulated"


def test_simulated_rotation_rejects_wrong_declared_receipt_for_timestamp():
    v1 = resolve_driver_api_receipt_by_timestamp(
        datetime(2026, 6, 5, 16, 0, tzinfo=timezone.utc),
        index_path=FIXTURE_RECEIPT_INDEX,
        receipts_dir=FIXTURE_RECEIPTS_DIR,
    )

    with pytest.raises(
        ContractReceiptIndexError,
        match="declared receipt does not match timestamp-resolved receipt",
    ):
        guard_declared_receipt_matches_timestamp(
            v1,
            datetime(2026, 6, 10, 0, 0, tzinfo=timezone.utc),
            index_path=FIXTURE_RECEIPT_INDEX,
            receipts_dir=FIXTURE_RECEIPTS_DIR,
        )
