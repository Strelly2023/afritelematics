from __future__ import annotations

import pytest

from afritech.crypto.anchor_batching import build_anchor_merkle_batch
from afritech.crypto.anchor_publication import build_anchor_publication_envelope
from afritech.crypto.external_anchor import build_external_anchor_commitment


def _envelope(suffix: str):
    commitment = build_external_anchor_commitment(
        tenant_id="tenant-core",
        region_id="mel-ap-southeast-2",
        trace_hash=("a" * 63) + suffix,
        replay_hash="b" * 64,
        receipt_hash="c" * 64,
        authority_hash="d" * 64,
        execution_fingerprint="e" * 64,
    )
    return build_anchor_publication_envelope(
        commitment,
        publication_target="public-ledger-test-anchor",
        external_reference=f"ledger-ref-{suffix}",
    )


def test_anchor_merkle_batch_is_deterministic() -> None:
    first = build_anchor_merkle_batch(
        (_envelope("1"), _envelope("2")),
        publication_target="public-ledger-test-anchor",
    )
    second = build_anchor_merkle_batch(
        (_envelope("2"), _envelope("1")),
        publication_target="public-ledger-test-anchor",
    )

    assert first == second
    assert first.batch_size == 2
    assert len(first.batch_root) == 64


def test_anchor_merkle_batch_requires_envelopes() -> None:
    with pytest.raises(ValueError, match="at least one envelope"):
        build_anchor_merkle_batch((), publication_target="public-ledger-test-anchor")
