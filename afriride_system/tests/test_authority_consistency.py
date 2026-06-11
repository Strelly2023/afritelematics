from __future__ import annotations

import pytest

from afriride_system.backend.authority_runtime import (
    AuthorityRuntimeError,
    assert_consistent_authority_hashes,
)


def test_authority_consistency_accepts_matching_hashes() -> None:
    digest = "a" * 64
    assert (
        assert_consistent_authority_hashes(
            trace=digest,
            replay=digest,
            evidence=digest,
            receipt=digest,
        )
        == digest
    )


def test_authority_consistency_rejects_mismatch() -> None:
    with pytest.raises(AuthorityRuntimeError, match="authority hash mismatch"):
        assert_consistent_authority_hashes(
            trace="a" * 64,
            replay="b" * 64,
        )
