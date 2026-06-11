from __future__ import annotations

import pytest

from afritech.crypto.anchor_publication import build_anchor_publication_envelope
from afritech.crypto.external_anchor import build_external_anchor_commitment


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64
HASH_E = "e" * 64


def _commitment():
    return build_external_anchor_commitment(
        tenant_id="tenant-core",
        region_id="mel-ap-southeast-2",
        trace_hash=HASH_A,
        replay_hash=HASH_B,
        receipt_hash=HASH_C,
        authority_hash=HASH_D,
        execution_fingerprint=HASH_E,
    )


def test_anchor_publication_envelope_is_deterministic() -> None:
    first = build_anchor_publication_envelope(
        _commitment(),
        publication_target="public-ledger-test-anchor",
        external_reference="ledger-ref-001",
    )
    second = build_anchor_publication_envelope(
        _commitment(),
        publication_target="public-ledger-test-anchor",
        external_reference="ledger-ref-001",
    )

    assert first == second
    assert first.publication_id == second.publication_id
    assert len(first.publication_hash) == 64
    assert len(first.receipt_commitment) == 64


def test_anchor_publication_envelope_changes_with_target() -> None:
    baseline = build_anchor_publication_envelope(
        _commitment(),
        publication_target="public-ledger-test-anchor",
    )
    changed = build_anchor_publication_envelope(
        _commitment(),
        publication_target="partner-ledger-eu",
    )

    assert baseline.publication_hash != changed.publication_hash
    assert baseline.receipt_commitment != changed.receipt_commitment


def test_anchor_publication_requires_target() -> None:
    with pytest.raises(ValueError, match="publication_target"):
        build_anchor_publication_envelope(_commitment(), publication_target="")
