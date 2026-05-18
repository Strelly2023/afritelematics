"""Deterministic concurrency primitives."""

from afritech.runtime.concurrency.resolver import (
    ConcurrentMutation,
    resolve_conflicts,
)

__all__ = ["ConcurrentMutation", "resolve_conflicts"]
