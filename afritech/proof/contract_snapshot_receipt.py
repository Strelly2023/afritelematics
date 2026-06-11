"""Deterministic receipts for frozen API contract snapshots."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from afritech.trust_kernel.hashing import sha256_payload


# ------------------------------------------------------------------------------------
# PATH CONFIGURATION
# ------------------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

DRIVER_ROUTES_SNAPSHOT = ROOT / "afritech/ci/contracts/driver_routes.json"
CONSTITUTIONAL_RECEIPT = ROOT / "afritech/proof/constitutional_receipt.json"
DRIVER_CONTRACT_RECEIPT = ROOT / "afritech/proof/driver_api_contract_receipt.json"


# ------------------------------------------------------------------------------------
# CONSTANTS
# ------------------------------------------------------------------------------------

RECEIPT_SCHEMA = "afritech.proof.contract_snapshot_receipt.v1"
EVENT_TYPE_VALIDATED = "APIContractValidated"

SIGNATURE_MODE = "deterministic_local_contract_signature"
SIGNER = "afritech-contract-snapshot-signer"


# ------------------------------------------------------------------------------------
# ERRORS
# ------------------------------------------------------------------------------------

class ContractSnapshotReceiptError(RuntimeError):
    """Raised when a contract snapshot receipt cannot be reconstructed."""


# ------------------------------------------------------------------------------------
# DATA MODEL
# ------------------------------------------------------------------------------------

@dataclass(frozen=True)
class ContractSnapshotReceipt:
    schema: str
    contract: str
    version: str
    event_type: str
    snapshot_path: str
    snapshot_hash: str
    contract_payload_hash: str
    previous_receipt_hash: str
    event_hash: str
    receipt_hash: str
    validator: str
    validator_version: str
    signature: Dict[str, str]
    status: str
    generated_at: str
    truth_boundary: Dict[str, bool]

    def canonical_dict(self) -> Dict[str, Any]:
        """Return canonical dictionary representation for deterministic comparison."""
        return {
            "schema": self.schema,
            "contract": self.contract,
            "version": self.version,
            "event_type": self.event_type,
            "snapshot_path": self.snapshot_path,
            "snapshot_hash": self.snapshot_hash,
            "contract_payload_hash": self.contract_payload_hash,
            "previous_receipt_hash": self.previous_receipt_hash,
            "event_hash": self.event_hash,
            "receipt_hash": self.receipt_hash,
            "validator": self.validator,
            "validator_version": self.validator_version,
            "signature": self.signature,
            "status": self.status,
            "generated_at": self.generated_at,
            "truth_boundary": self.truth_boundary,
        }


# ------------------------------------------------------------------------------------
# CORE RECEIPT BUILDER
# ------------------------------------------------------------------------------------

def build_driver_api_contract_receipt() -> ContractSnapshotReceipt:
    """Build deterministic contract snapshot receipt."""

    snapshot_payload = _load_json(DRIVER_ROUTES_SNAPSHOT)
    previous_receipt = _load_json(CONSTITUTIONAL_RECEIPT)

    snapshot_hash = _file_sha256(DRIVER_ROUTES_SNAPSHOT)
    contract_payload_hash = sha256_payload(snapshot_payload)

    previous_receipt_hash = _text(
        previous_receipt.get("receipt_hash"),
        "receipt_hash"
    )

    # --------------------------------------------------------------------------------
    # TRUTH BOUNDARY VALIDATION (STRICT)
    # --------------------------------------------------------------------------------

    truth_boundary = snapshot_payload.get("truth_boundary")
    if not isinstance(truth_boundary, dict):
        raise ContractSnapshotReceiptError(
            "driver route snapshot missing truth_boundary"
        )

    normalized_truth_boundary = {
        "live_pilot_authorized": _false_value(truth_boundary, "live_pilot_authorized"),
        "production_proven": _false_value(truth_boundary, "production_proven"),
        "economic_activation": _false_value(truth_boundary, "economic_activation"),
    }

    # --------------------------------------------------------------------------------
    # EVENT BODY (HASH BASE)
    # --------------------------------------------------------------------------------

    event_body = {
        "event_type": EVENT_TYPE_VALIDATED,
        "contract": "driver_api_routes",
        "version": "v1",
        "snapshot_hash": snapshot_hash,
        "contract_payload_hash": contract_payload_hash,
        "previous_receipt_hash": previous_receipt_hash,
        "status": "MATCH",
        "truth_boundary": normalized_truth_boundary,
    }

    event_hash = sha256_payload(event_body)

    # --------------------------------------------------------------------------------
    # SIGNATURE (DETERMINISTIC)
    # --------------------------------------------------------------------------------

    signature = {
        "mode": SIGNATURE_MODE,
        "signer": SIGNER,
        "signature_hash": sha256_payload(
            {
                "signer": SIGNER,
                "event_hash": event_hash,
                "snapshot_hash": snapshot_hash,
            }
        ),
    }

    # --------------------------------------------------------------------------------
    # UNSIGNED RECEIPT (PRE-HASH)
    # --------------------------------------------------------------------------------

    unsigned_receipt = {
        "schema": RECEIPT_SCHEMA,
        "contract": "driver_api_routes",
        "version": "v1",
        "event_type": EVENT_TYPE_VALIDATED,
        "snapshot_path": "afritech/ci/contracts/driver_routes.json",
        "snapshot_hash": snapshot_hash,
        "contract_payload_hash": contract_payload_hash,
        "previous_receipt_hash": previous_receipt_hash,
        "event_hash": event_hash,
        "validator": "afritech.ci.driver_api_contract_validator",
        "validator_version": "v1",
        "signature": signature,
        "status": "MATCH",
        "generated_at": "deterministic-contract-snapshot-receipt-v1",
        "truth_boundary": normalized_truth_boundary,
    }

    # --------------------------------------------------------------------------------
    # FINAL HASH
    # --------------------------------------------------------------------------------

    receipt_hash = sha256_payload(unsigned_receipt)

    return ContractSnapshotReceipt(
        receipt_hash=receipt_hash,
        **unsigned_receipt,
    )


# ------------------------------------------------------------------------------------
# VERIFICATION
# ------------------------------------------------------------------------------------

def verify_driver_api_contract_receipt(
    receipt_payload: Dict[str, Any] | None = None
) -> bool:
    """Verify receipt deterministically matches expected reconstruction."""

    expected = build_driver_api_contract_receipt().canonical_dict()

    actual = (
        receipt_payload
        if receipt_payload is not None
        else _load_json(DRIVER_CONTRACT_RECEIPT)
    )

    if actual != expected:
        raise ContractSnapshotReceiptError(
            "driver API contract receipt reconstruction mismatch"
        )

    return True


# ------------------------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------------------------

def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        raise ContractSnapshotReceiptError(
            f"{path} must contain a JSON object"
        )

    return payload


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractSnapshotReceiptError(f"{label} is required")

    return value.strip()


def _false_value(payload: Dict[str, Any], key: str) -> bool:
    if payload.get(key) is not False:
        raise ContractSnapshotReceiptError(
            f"truth boundary must be false: {key}"
        )

    return False