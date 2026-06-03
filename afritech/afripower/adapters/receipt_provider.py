"""
Read-only receipt provider for AFRIPower.

This adapter exposes existing receipts/proofs/traces to AFRIPower as
reference data only.

Constitutional boundary:
- reads existing artifacts
- never writes artifacts
- never mutates receipts
- never validates truth
- never creates authority
- never influences runtime/replay/proof/CI/governance
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

from afritech.afripower.contracts.read_only_contract import (
    assert_read_only_contract,
)


class AFRIPowerReceiptProviderError(RuntimeError):
    """Raised when read-only receipt access fails."""


@dataclass(frozen=True)
class AFRIPowerReceiptReference:
    """Immutable read-only receipt reference."""

    source_path: str
    receipt_id: str
    receipt_type: str
    payload: Mapping[str, object]

    def canonical_dict(self) -> dict[str, object]:
        return {
            "source_path": self.source_path,
            "receipt_id": self.receipt_id,
            "receipt_type": self.receipt_type,
            "payload": dict(self.payload),
            "read_only": True,
            "reference_only": True,
            "display_only": True,
            "creates_authority": False,
            "mutates_receipt": False,
            "validates_truth": False,
        }


def _safe_str(value: object, fallback: str = "") -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def _load_json_file(path: Path) -> Mapping[str, object]:
    if not path.is_file():
        raise AFRIPowerReceiptProviderError(
            f"receipt source is not a file: {path}"
        )

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise AFRIPowerReceiptProviderError(
            f"failed to read receipt source: {path}"
        ) from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AFRIPowerReceiptProviderError(
            f"receipt source is not valid JSON: {path}"
        ) from exc

    if not isinstance(parsed, Mapping):
        raise AFRIPowerReceiptProviderError(
            f"receipt source must contain a JSON object: {path}"
        )

    return parsed


def _infer_receipt_id(path: Path, payload: Mapping[str, object]) -> str:
    return (
        _safe_str(payload.get("receipt_id"))
        or _safe_str(payload.get("id"))
        or _safe_str(payload.get("proof_id"))
        or _safe_str(payload.get("trace_id"))
        or path.stem
    )


def _infer_receipt_type(payload: Mapping[str, object]) -> str:
    return (
        _safe_str(payload.get("receipt_type"))
        or _safe_str(payload.get("type"))
        or _safe_str(payload.get("kind"))
        or "receipt"
    )


def load_receipt_reference(path: str | Path) -> AFRIPowerReceiptReference:
    """
    Load one receipt as a read-only AFRIPower reference.

    This function does not validate receipt truth.
    It only adapts already-existing data for projection.
    """

    assert_read_only_contract()

    source = Path(path)
    payload = _load_json_file(source)

    return AFRIPowerReceiptReference(
        source_path=str(source),
        receipt_id=_infer_receipt_id(source, payload),
        receipt_type=_infer_receipt_type(payload),
        payload=payload,
    )


def load_receipt_references(
    paths: Iterable[str | Path],
) -> tuple[AFRIPowerReceiptReference, ...]:
    """
    Load multiple receipts deterministically.

    Ordering is canonicalized by path string.
    """

    assert_read_only_contract()

    normalized_paths = tuple(sorted(Path(path) for path in paths))
    return tuple(load_receipt_reference(path) for path in normalized_paths)


def load_receipt_reference_dict(path: str | Path) -> dict[str, object]:
    return load_receipt_reference(path).canonical_dict()


def load_receipt_reference_dicts(
    paths: Iterable[str | Path],
) -> tuple[dict[str, object], ...]:
    return tuple(
        receipt.canonical_dict()
        for receipt in load_receipt_references(paths)
    )


__all__ = [
    "AFRIPowerReceiptProviderError",
    "AFRIPowerReceiptReference",
    "load_receipt_reference",
    "load_receipt_references",
    "load_receipt_reference_dict",
    "load_receipt_reference_dicts",
]
