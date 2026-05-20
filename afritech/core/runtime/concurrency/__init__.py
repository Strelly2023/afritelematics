"""Deterministic concurrency primitives."""

from afritech.core.runtime.concurrency.resolver import (
    ConcurrentMutation,
    resolve_conflicts,
)

__all__ = ["ConcurrentMutation", "resolve_conflicts"]
