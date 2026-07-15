"""Optimistic concurrency helpers."""

from __future__ import annotations

from afritech.novaride_runtime.common.errors import ConcurrencyConflict


def require_expected_version(current: int, expected: int | None) -> None:
    if expected is not None and current != expected:
        raise ConcurrencyConflict(f"expected_version:{expected}:actual:{current}")
