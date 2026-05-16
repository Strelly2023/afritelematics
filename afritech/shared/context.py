"""
Shared runtime context

Neutral, dependency-free representation of execution context.

Must not import runtime.engine or guards.
"""

from typing import Dict, Any


class RuntimeContext:
    """
    Shared context used across runtime and evaluation.
    """

    def __init__(
        self,
        *,
        authority_profile: str,
        payload: Dict[str, Any],
        replay_requirements: Dict[str, Any],
        context_hash: str,
        timestamp: str,
    ):
        self.authority_profile = authority_profile
        self.payload = payload
        self.replay_requirements = replay_requirements
        self.context_hash = context_hash
        self.timestamp = timestamp

    def verify(self) -> bool:
        # minimal integrity check (real logic can stay in runtime if needed)
        return bool(self.context_hash and self.timestamp)

    def to_dict(self):
        return {
            "authority_profile": self.authority_profile,
            "payload": self.payload,
            "replay_requirements": self.replay_requirements,
            "context_hash": self.context_hash,
            "timestamp": self.timestamp,
        }