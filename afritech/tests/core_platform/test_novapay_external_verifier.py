from __future__ import annotations

import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

from afritech.core_platform.models import Identity
from afritech.core_platform.novapay_external_verifier import verify_audit_package
from afritech.core_platform.novapay_runtime import NovaPayRuntimeEngine


def _identity() -> Identity:
    return Identity(
        identity_id="sender-1",
        email="sender-1@novapay.local",
        roles=("CUSTOMER",),
        organization_id="org-pay",
        kyc_status="verified",
    )


def _transfer_payload() -> dict[str, object]:
    return {
        "transfer_type": "Cross-Border Remittance",
        "recipient_name": "Amina Okello",
        "recipient_identifier": "+254700000001",
        "recipient_country": "KE",
        "amount": "100.00",
        "source_currency": "AUD",
        "source_country": "AU",
        "funding_source_type": "wallet",
        "funding_source_reference": "wallet-ref-1",
        "payout_method": "mobile_money",
        "use_case": "family_support",
        "memo": "school fees",
        "recipient_type": "individual",
        "live_provider": False,
        "auto_execute": False,
    }


def _audit_package() -> dict[str, object]:
    runtime = NovaPayRuntimeEngine()
    record = runtime.create_transfer(_transfer_payload(), identity=_identity(), auto_execute=True)
    return runtime.build_audit_package(record.transfer.transfer_id)


def test_external_verifier_accepts_runtime_audit_package() -> None:
    package = _audit_package()

    result = verify_audit_package(package)

    assert result["valid"] is True
    assert result["protocol_valid"] is True
    assert result["signature_valid"] is True
    assert result["ledger_hash_valid"] is True
    assert result["snapshot_root_valid"] is True
    assert result["snapshot_ledger_valid"] is True
    assert result["event_chain_valid"] is True
    assert result["transfer_merkle_valid"] is True
    assert result["ledger_checkpoint_valid"] is True
    assert result["reconciliation_valid"] is True


def test_external_verifier_rejects_tampered_ledger() -> None:
    package = deepcopy(_audit_package())
    package["ledger"][0]["amount"] = "99.99"

    result = verify_audit_package(package)

    assert result["valid"] is False
    assert result["ledger_hash_valid"] is False


def test_external_verifier_rejects_tampered_merkle_proof() -> None:
    package = deepcopy(_audit_package())
    package["merkle_proofs"][0]["path"][0]["hash"] = "f" * 64

    result = verify_audit_package(package)

    assert result["valid"] is False
    assert result["transfer_merkle_valid"] is False


def test_external_verifier_rejects_tampered_merkle_event_identity() -> None:
    package = deepcopy(_audit_package())
    package["merkle_proofs"][0]["sequence"] = 999

    result = verify_audit_package(package)

    assert result["valid"] is False
    assert result["transfer_merkle_valid"] is False


def test_external_verifier_rejects_tampered_global_ledger_root() -> None:
    package = deepcopy(_audit_package())
    package["ledger_checkpoint"]["transfer_roots"][0]["transfer_merkle_root"] = "e" * 64

    result = verify_audit_package(package)

    assert result["valid"] is False
    assert result["ledger_checkpoint_valid"] is False


def test_external_verifier_cli_verifies_audit_package(tmp_path: Path) -> None:
    package_path = tmp_path / "audit_package.json"
    package_path.write_text(json.dumps(_audit_package(), indent=2, sort_keys=True), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "afritech.tools.novapay_verify_cli",
            str(package_path),
            "--format",
            "json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    result = json.loads(completed.stdout)
    assert result["valid"] is True
    assert result["transfer_merkle_valid"] is True
    assert result["ledger_checkpoint_valid"] is True


def test_external_verifier_protocol_does_not_import_runtime_engine() -> None:
    verifier_source = Path("afritech/core_platform/novapay_external_verifier.py").read_text(
        encoding="utf-8"
    )

    assert "NovaPayRuntimeEngine" not in verifier_source
    assert "novapay_runtime" not in verifier_source
