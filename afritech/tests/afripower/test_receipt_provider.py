from __future__ import annotations

import json

import pytest

from afritech.afripower.adapters.receipt_provider import (
    AFRIPowerReceiptProviderError,
    AFRIPowerReceiptReference,
    load_receipt_reference,
    load_receipt_reference_dict,
    load_receipt_reference_dicts,
    load_receipt_references,
)


def test_receipt_reference_canonical_dict_is_read_only():
    reference = AFRIPowerReceiptReference(
        source_path="receipts/demo.json",
        receipt_id="receipt.demo.001",
        receipt_type="proof_reference",
        payload={"status": "existing_reference"},
    )

    data = reference.canonical_dict()

    assert data["source_path"] == "receipts/demo.json"
    assert data["receipt_id"] == "receipt.demo.001"
    assert data["receipt_type"] == "proof_reference"
    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["creates_authority"] is False
    assert data["mutates_receipt"] is False
    assert data["validates_truth"] is False


def test_load_receipt_reference_from_receipt_id(tmp_path):
    path = tmp_path / "receipt.json"
    path.write_text(
        json.dumps(
            {
                "receipt_id": "receipt.demo.001",
                "receipt_type": "proof_reference",
                "status": "existing_reference",
            }
        ),
        encoding="utf-8",
    )

    reference = load_receipt_reference(path)

    assert reference.receipt_id == "receipt.demo.001"
    assert reference.receipt_type == "proof_reference"
    assert reference.payload["status"] == "existing_reference"


def test_load_receipt_reference_infers_id_from_id_field(tmp_path):
    path = tmp_path / "receipt.json"
    path.write_text(
        json.dumps(
            {
                "id": "generic.receipt.001",
                "type": "generic_reference",
            }
        ),
        encoding="utf-8",
    )

    reference = load_receipt_reference(path)

    assert reference.receipt_id == "generic.receipt.001"
    assert reference.receipt_type == "generic_reference"


def test_load_receipt_reference_infers_id_from_proof_id(tmp_path):
    path = tmp_path / "proof.json"
    path.write_text(
        json.dumps(
            {
                "proof_id": "proof.demo.001",
                "kind": "proof_reference",
            }
        ),
        encoding="utf-8",
    )

    reference = load_receipt_reference(path)

    assert reference.receipt_id == "proof.demo.001"
    assert reference.receipt_type == "proof_reference"


def test_load_receipt_reference_infers_id_from_trace_id(tmp_path):
    path = tmp_path / "trace.json"
    path.write_text(
        json.dumps(
            {
                "trace_id": "trace.demo.001",
            }
        ),
        encoding="utf-8",
    )

    reference = load_receipt_reference(path)

    assert reference.receipt_id == "trace.demo.001"
    assert reference.receipt_type == "receipt"


def test_load_receipt_reference_falls_back_to_filename(tmp_path):
    path = tmp_path / "fallback_receipt.json"
    path.write_text(
        json.dumps(
            {
                "status": "existing_reference",
            }
        ),
        encoding="utf-8",
    )

    reference = load_receipt_reference(path)

    assert reference.receipt_id == "fallback_receipt"
    assert reference.receipt_type == "receipt"


def test_load_receipt_reference_dict(tmp_path):
    path = tmp_path / "receipt.json"
    path.write_text(
        json.dumps(
            {
                "receipt_id": "receipt.demo.001",
                "receipt_type": "proof_reference",
            }
        ),
        encoding="utf-8",
    )

    data = load_receipt_reference_dict(path)

    assert data["receipt_id"] == "receipt.demo.001"
    assert data["receipt_type"] == "proof_reference"
    assert data["read_only"] is True
    assert data["creates_authority"] is False


def test_load_receipt_references_are_sorted_by_path(tmp_path):
    path_b = tmp_path / "b.json"
    path_a = tmp_path / "a.json"

    path_b.write_text(
        json.dumps({"receipt_id": "receipt.b"}),
        encoding="utf-8",
    )
    path_a.write_text(
        json.dumps({"receipt_id": "receipt.a"}),
        encoding="utf-8",
    )

    references = load_receipt_references((path_b, path_a))

    assert tuple(reference.receipt_id for reference in references) == (
        "receipt.a",
        "receipt.b",
    )


def test_load_receipt_reference_dicts(tmp_path):
    path_a = tmp_path / "a.json"
    path_b = tmp_path / "b.json"

    path_a.write_text(
        json.dumps({"receipt_id": "receipt.a"}),
        encoding="utf-8",
    )
    path_b.write_text(
        json.dumps({"receipt_id": "receipt.b"}),
        encoding="utf-8",
    )

    data = load_receipt_reference_dicts((path_b, path_a))

    assert tuple(item["receipt_id"] for item in data) == (
        "receipt.a",
        "receipt.b",
    )
    assert all(item["read_only"] is True for item in data)
    assert all(item["creates_authority"] is False for item in data)


def test_missing_file_rejected(tmp_path):
    with pytest.raises(AFRIPowerReceiptProviderError):
        load_receipt_reference(tmp_path / "missing.json")


def test_invalid_json_rejected(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(AFRIPowerReceiptProviderError):
        load_receipt_reference(path)


def test_non_object_json_rejected(tmp_path):
    path = tmp_path / "list.json"
    path.write_text(
        json.dumps(["not", "an", "object"]),
        encoding="utf-8",
    )

    with pytest.raises(AFRIPowerReceiptProviderError):
        load_receipt_reference(path)


def test_directory_rejected(tmp_path):
    with pytest.raises(AFRIPowerReceiptProviderError):
        load_receipt_reference(tmp_path)
