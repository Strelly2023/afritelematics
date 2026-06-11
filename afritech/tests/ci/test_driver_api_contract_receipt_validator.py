from __future__ import annotations

import subprocess
import sys

from afritech.ci import driver_api_contract_receipt_validator as validator
from afritech.proof.contract_snapshot_receipt import build_driver_api_contract_receipt


def test_driver_api_contract_receipt_validator_passes():
    assert validator.validate() is True


def test_driver_api_contract_receipt_is_bound_to_snapshot_and_hash_chain():
    receipt = build_driver_api_contract_receipt()

    assert receipt.event_type == "APIContractValidated"
    assert receipt.status == "MATCH"
    assert len(receipt.snapshot_hash) == 64
    assert len(receipt.event_hash) == 64
    assert len(receipt.receipt_hash) == 64
    assert receipt.signature["mode"] == "deterministic_local_contract_signature"
    assert receipt.truth_boundary == {
        "live_pilot_authorized": False,
        "production_proven": False,
        "economic_activation": False,
    }


def test_driver_api_contract_receipt_validator_cli_passes():
    result = subprocess.run(
        [sys.executable, "-m", "afritech.ci.driver_api_contract_receipt_validator"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Driver API contract receipt validation PASSED" in result.stdout
    assert "snapshot_hash=" in result.stdout
