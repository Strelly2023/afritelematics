"""Distributed runtime classification governance tests."""

from afritech.ci.ast_import_validator import (
    FORBIDDEN_SPECULATIVE_PREFIXES,
)


def test_distributed_runtime_is_not_speculative() -> None:
    assert "afritech.distributed" not in FORBIDDEN_SPECULATIVE_PREFIXES


def test_actual_speculative_layers_remain_forbidden() -> None:
    assert "afritech.speculative" in FORBIDDEN_SPECULATIVE_PREFIXES
    assert "afritech.civilization" in FORBIDDEN_SPECULATIVE_PREFIXES
    assert "afritech.federation" in FORBIDDEN_SPECULATIVE_PREFIXES