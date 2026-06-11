from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from afritech.trust_kernel.hashing import sha256_payload


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_RECEIPTS_DIR = ROOT / "afritech/proof/contract_receipts"
CONTRACT_RECEIPT_INDEX = CONTRACT_RECEIPTS_DIR / "index.json"


class ContractReceiptIndexError(RuntimeError):
    """Raised when an event-declared contract receipt cannot be resolved."""


@dataclass(frozen=True)
class IndexedContractReceipt:
    contract: str
    version: str
    snapshot_hash: str
    contract_payload_hash: str
    event_hash: str
    receipt_hash: str
    receipt_id: str
    path: str
    effective_from: datetime
    effective_to: datetime | None
    payload: dict[str, Any]

    @property
    def effective_from_iso(self) -> str:
        return _format_utc(self.effective_from)

    @property
    def effective_to_iso(self) -> str | None:
        if self.effective_to is None:
            return None
        return _format_utc(self.effective_to)


def resolve_driver_api_receipt_by_hash(
    receipt_hash: str,
    *,
    index_path: Path = CONTRACT_RECEIPT_INDEX,
    receipts_dir: Path = CONTRACT_RECEIPTS_DIR,
) -> IndexedContractReceipt:
    if not isinstance(receipt_hash, str) or not receipt_hash.strip():
        raise ContractReceiptIndexError("contract receipt hash is required")
    index = _load_json(index_path)
    driver_api = index.get("driver_api")
    if not isinstance(driver_api, dict):
        raise ContractReceiptIndexError("driver_api index is required")
    receipts = driver_api.get("receipts")
    if not isinstance(receipts, dict):
        raise ContractReceiptIndexError("driver_api receipts index is required")

    for receipt_id, entry in receipts.items():
        if not isinstance(entry, dict):
            raise ContractReceiptIndexError(f"invalid receipt index entry: {receipt_id}")
        payload = _load_indexed_receipt(entry, receipts_dir=receipts_dir)
        if payload.get("receipt_hash") == receipt_hash:
            return _verify_indexed_receipt(str(receipt_id), entry, payload)
    raise ContractReceiptIndexError("declared contract receipt hash not found in index")


def resolve_driver_api_receipt_by_timestamp(
    event_timestamp: datetime,
    *,
    index_path: Path = CONTRACT_RECEIPT_INDEX,
    receipts_dir: Path = CONTRACT_RECEIPTS_DIR,
) -> IndexedContractReceipt:
    normalized = _normalize_timestamp(event_timestamp)
    guard_driver_api_receipt_index_succession(
        index_path=index_path,
        receipts_dir=receipts_dir,
    )
    receipts = _iter_driver_api_receipts(index_path=index_path, receipts_dir=receipts_dir)
    guard_driver_api_receipt_windows_non_overlapping(receipts)
    matches = [receipt for receipt in receipts if _receipt_effective_at(receipt, normalized)]
    if not matches:
        raise ContractReceiptIndexError("no driver API receipt effective at event timestamp")
    if len(matches) > 1:
        raise ContractReceiptIndexError("multiple driver API receipts effective at event timestamp")
    return matches[0]


def guard_driver_api_receipt_index_non_overlapping(
    *,
    index_path: Path = CONTRACT_RECEIPT_INDEX,
    receipts_dir: Path = CONTRACT_RECEIPTS_DIR,
) -> None:
    guard_driver_api_receipt_windows_non_overlapping(
        _iter_driver_api_receipts(index_path=index_path, receipts_dir=receipts_dir)
    )


def guard_driver_api_receipt_index_succession(
    *,
    index_path: Path = CONTRACT_RECEIPT_INDEX,
    receipts_dir: Path = CONTRACT_RECEIPTS_DIR,
) -> None:
    index = _load_json(index_path)
    driver_api = index.get("driver_api")
    if not isinstance(driver_api, dict):
        raise ContractReceiptIndexError("driver_api index is required")
    active_id = _required_text(driver_api, "active")
    receipts = _iter_driver_api_receipts(index_path=index_path, receipts_dir=receipts_dir)
    if active_id not in {receipt.receipt_id for receipt in receipts}:
        raise ContractReceiptIndexError("active driver API receipt is not indexed")
    guard_driver_api_receipt_succession(receipts, active_id=active_id)
    guard_driver_api_receipt_windows_non_overlapping(receipts)


def guard_driver_api_receipt_succession(
    receipts: list[IndexedContractReceipt],
    *,
    active_id: str,
) -> None:
    by_contract: dict[str, list[IndexedContractReceipt]] = {}
    for receipt in receipts:
        by_contract.setdefault(receipt.contract, []).append(receipt)

    for contract, contract_receipts in by_contract.items():
        ordered = sorted(
            contract_receipts,
            key=lambda receipt: (receipt.effective_from, receipt.receipt_id),
        )
        if not ordered:
            continue
        for receipt in ordered[:-1]:
            if receipt.effective_to is None:
                raise ContractReceiptIndexError(
                    f"non-latest receipt must declare effective_to: {contract}"
                )
        for receipt in ordered:
            if receipt.effective_to is None and receipt.receipt_id != active_id:
                raise ContractReceiptIndexError(
                    f"only active latest receipt may have null effective_to: {contract}"
                )
        for previous, current in zip(ordered, ordered[1:]):
            if previous.effective_to is None:
                raise ContractReceiptIndexError(
                    f"receipt successor starts before predecessor ends: {contract}"
                )
            if previous.effective_to > current.effective_from:
                raise ContractReceiptIndexError(
                    f"receipt successor starts before predecessor ends: {contract}"
                )


def guard_driver_api_receipt_windows_non_overlapping(
    receipts: list[IndexedContractReceipt],
) -> None:
    by_contract: dict[str, list[IndexedContractReceipt]] = {}
    for receipt in receipts:
        by_contract.setdefault(receipt.contract, []).append(receipt)

    for contract, contract_receipts in by_contract.items():
        ordered = sorted(
            contract_receipts,
            key=lambda receipt: (receipt.effective_from, receipt.receipt_id),
        )
        for previous, current in zip(ordered, ordered[1:]):
            if previous.effective_to is None:
                raise ContractReceiptIndexError(
                    f"contract receipt effective windows overlap: {contract}"
                )
            if previous.effective_to > current.effective_from:
                raise ContractReceiptIndexError(
                    f"contract receipt effective windows overlap: {contract}"
                )


def _iter_driver_api_receipts(
    *,
    index_path: Path = CONTRACT_RECEIPT_INDEX,
    receipts_dir: Path = CONTRACT_RECEIPTS_DIR,
) -> list[IndexedContractReceipt]:
    index = _load_json(index_path)
    driver_api = index.get("driver_api")
    if not isinstance(driver_api, dict):
        raise ContractReceiptIndexError("driver_api index is required")
    receipts = driver_api.get("receipts")
    if not isinstance(receipts, dict):
        raise ContractReceiptIndexError("driver_api receipts index is required")
    resolved: list[IndexedContractReceipt] = []
    for receipt_id, entry in receipts.items():
        if not isinstance(entry, dict):
            raise ContractReceiptIndexError(f"invalid receipt index entry: {receipt_id}")
        resolved.append(
            _verify_indexed_receipt(
                str(receipt_id),
                entry,
                _load_indexed_receipt(entry, receipts_dir=receipts_dir),
            )
        )
    return resolved


def _load_indexed_receipt(
    entry: dict[str, Any],
    *,
    receipts_dir: Path = CONTRACT_RECEIPTS_DIR,
) -> dict[str, Any]:
    path_value = entry.get("path")
    if not isinstance(path_value, str) or not path_value.strip():
        raise ContractReceiptIndexError("receipt index entry path is required")
    receipt_path = (receipts_dir / path_value).resolve()
    if receipts_dir.resolve() not in receipt_path.parents:
        raise ContractReceiptIndexError("receipt index path escapes contract_receipts")
    return _load_json(receipt_path)


def _verify_indexed_receipt(
    receipt_id: str,
    entry: dict[str, Any],
    payload: dict[str, Any],
) -> IndexedContractReceipt:
    contract = _required_text(payload, "contract")
    version = _required_text(payload, "version")
    if contract != _required_text(entry, "contract"):
        raise ContractReceiptIndexError("indexed receipt contract mismatch")
    if version != _required_text(entry, "version"):
        raise ContractReceiptIndexError("indexed receipt version mismatch")

    receipt_hash = _required_text(payload, "receipt_hash")
    unsigned = dict(payload)
    unsigned.pop("receipt_hash", None)
    if sha256_payload(unsigned) != receipt_hash:
        raise ContractReceiptIndexError("indexed receipt hash reconstruction mismatch")

    snapshot_hash = _required_text(payload, "snapshot_hash")
    snapshot_path = ROOT / _required_text(payload, "snapshot_path")
    if not snapshot_path.exists():
        raise ContractReceiptIndexError("indexed receipt snapshot path missing")
    if hashlib.sha256(snapshot_path.read_bytes()).hexdigest() != snapshot_hash:
        raise ContractReceiptIndexError("indexed receipt snapshot hash mismatch")

    expected_event_hash = sha256_payload(
        {
            "event_type": _required_text(payload, "event_type"),
            "contract": contract,
            "version": version,
            "snapshot_hash": snapshot_hash,
            "contract_payload_hash": _required_text(payload, "contract_payload_hash"),
            "previous_receipt_hash": _required_text(payload, "previous_receipt_hash"),
            "status": _required_text(payload, "status"),
            "truth_boundary": payload.get("truth_boundary"),
        }
    )
    event_hash = _required_text(payload, "event_hash")
    if expected_event_hash != event_hash:
        raise ContractReceiptIndexError("indexed receipt event hash mismatch")

    return IndexedContractReceipt(
        contract=contract,
        version=version,
        snapshot_hash=snapshot_hash,
        contract_payload_hash=_required_text(payload, "contract_payload_hash"),
        event_hash=event_hash,
        receipt_hash=receipt_hash,
        receipt_id=receipt_id,
        path=_required_text(entry, "path"),
        effective_from=_parse_timestamp(_required_text(entry, "effective_from")),
        effective_to=_parse_optional_timestamp(entry.get("effective_to")),
        payload=payload,
    )


def guard_receipt_effective_at(
    receipt: IndexedContractReceipt,
    event_timestamp: datetime,
) -> None:
    if event_timestamp is None:
        raise ContractReceiptIndexError("event timestamp is required")
    normalized = _normalize_timestamp(event_timestamp)
    if not _receipt_effective_at(receipt, normalized):
        if normalized < receipt.effective_from:
            raise ContractReceiptIndexError("event timestamp precedes contract receipt effective_from")
        raise ContractReceiptIndexError("event timestamp is outside contract receipt effective window")


def guard_declared_receipt_matches_timestamp(
    declared_receipt: IndexedContractReceipt,
    event_timestamp: datetime,
    *,
    index_path: Path = CONTRACT_RECEIPT_INDEX,
    receipts_dir: Path = CONTRACT_RECEIPTS_DIR,
) -> None:
    expected = resolve_driver_api_receipt_by_timestamp(
        event_timestamp,
        index_path=index_path,
        receipts_dir=receipts_dir,
    )
    if expected.receipt_hash != declared_receipt.receipt_hash:
        raise ContractReceiptIndexError(
            "declared receipt does not match timestamp-resolved receipt"
        )


def _receipt_effective_at(
    receipt: IndexedContractReceipt,
    normalized_timestamp: datetime,
) -> bool:
    if normalized_timestamp < receipt.effective_from:
        return False
    if receipt.effective_to is not None and normalized_timestamp >= receipt.effective_to:
        return False
    return True


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ContractReceiptIndexError(f"{path} must contain a JSON object")
    return payload


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ContractReceiptIndexError(f"{key} is required")
    return value.strip()


def _parse_optional_timestamp(value: object) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ContractReceiptIndexError("effective_to must be null or a timestamp")
    return _parse_timestamp(value)


def _parse_timestamp(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ContractReceiptIndexError("contract receipt effective timestamp is invalid") from exc
    return _normalize_timestamp(parsed)


def _normalize_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ContractReceiptIndexError("timestamp must include timezone")
    return value.astimezone(timezone.utc)


def _format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
