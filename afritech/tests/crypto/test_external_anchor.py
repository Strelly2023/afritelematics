from __future__ import annotations

import pytest

from afritech.crypto.external_anchor import build_external_anchor_commitment


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64
HASH_E = "e" * 64


def test_external_anchor_commitment_is_deterministic() -> None:
    first = build_external_anchor_commitment(
        tenant_id="tenant-core",
        region_id="mel-ap-southeast-2",
        trace_hash=HASH_A,
        replay_hash=HASH_B,
        receipt_hash=HASH_C,
        authority_hash=HASH_D,
        execution_fingerprint=HASH_E,
    )
    second = build_external_anchor_commitment(
        tenant_id="tenant-core",
        region_id="mel-ap-southeast-2",
        trace_hash=HASH_A,
        replay_hash=HASH_B,
        receipt_hash=HASH_C,
        authority_hash=HASH_D,
        execution_fingerprint=HASH_E,
    )

    assert first == second
    assert first.anchor_id == second.anchor_id
    assert len(first.commitment_hash) == 64
    assert len(first.payload_hash) == 64


def test_external_anchor_commitment_changes_when_hashes_change() -> None:
    baseline = build_external_anchor_commitment(
        tenant_id="tenant-core",
        region_id="mel-ap-southeast-2",
        trace_hash=HASH_A,
        replay_hash=HASH_B,
        receipt_hash=HASH_C,
        authority_hash=HASH_D,
        execution_fingerprint=HASH_E,
    )
    changed = build_external_anchor_commitment(
        tenant_id="tenant-core",
        region_id="mel-ap-southeast-2",
        trace_hash=HASH_A,
        replay_hash=HASH_B,
        receipt_hash="d" * 64,
        authority_hash=HASH_D,
        execution_fingerprint=HASH_E,
    )

    assert baseline.commitment_hash != changed.commitment_hash
    assert baseline.payload_hash != changed.payload_hash


def test_external_anchor_commitment_rejects_invalid_hash_lengths() -> None:
    with pytest.raises(ValueError, match="trace_hash"):
        build_external_anchor_commitment(
            tenant_id="tenant-core",
            region_id="mel-ap-southeast-2",
            trace_hash="short",
            replay_hash=HASH_B,
            receipt_hash=HASH_C,
            authority_hash=HASH_D,
            execution_fingerprint=HASH_E,
        )
