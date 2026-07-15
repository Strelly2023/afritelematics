"""Replay lock primitives."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ReplayLockRegistry:
    locks: set[str] = field(default_factory=set)

    def acquire(self, scope_key: str) -> None:
        if scope_key in self.locks:
            raise RuntimeError(f"replay_scope_locked:{scope_key}")
        self.locks.add(scope_key)

    def release(self, scope_key: str) -> None:
        self.locks.discard(scope_key)
