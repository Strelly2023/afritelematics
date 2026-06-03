from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Any


class PatchModelError(Exception):
    """Raised when patch model construction fails."""


class PatchMode(str, Enum):
    PROPOSAL_ONLY = "proposal_only"
    SIMULATION = "simulation"
    WRITE_DISABLED = "write_disabled"


class PatchRiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class Patch:
    """
    Canonical AfriProgramming patch proposal.

    Constitutional properties:
    - immutable
    - deterministic
    - proposal-only by default
    - evidence-ready
    - non-authoritative
    """

    file_path: str
    original_content: str
    updated_content: str
    patch_type: str = "proposal"
    risk_level: str = PatchRiskLevel.LOW.value
    mode: str = PatchMode.PROPOSAL_ONLY.value
    write_permitted: bool = False

    def __post_init__(self) -> None:
        if not self.file_path.strip():
            raise PatchModelError("file_path must not be empty")

        if self.risk_level not in {item.value for item in PatchRiskLevel}:
            raise PatchModelError(f"invalid risk level: {self.risk_level}")

        if self.mode not in {item.value for item in PatchMode}:
            raise PatchModelError(f"invalid patch mode: {self.mode}")

        if self.write_permitted:
            raise PatchModelError(
                "write_permitted must remain False in Phase 3"
            )

    @property
    def is_noop(self) -> bool:
        return self.original_content == self.updated_content

    @property
    def original_hash(self) -> str:
        return self._hash_text(self.original_content)

    @property
    def updated_hash(self) -> str:
        return self._hash_text(self.updated_content)

    @property
    def patch_hash(self) -> str:
        material = "|".join(
            (
                self.file_path,
                self.original_hash,
                self.updated_hash,
                self.patch_type,
                self.risk_level,
                self.mode,
                str(self.write_permitted),
            )
        )
        return self._hash_text(material)

    @property
    def changed(self) -> bool:
        return not self.is_noop

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "patch_type": self.patch_type,
            "risk_level": self.risk_level,
            "mode": self.mode,
            "write_permitted": self.write_permitted,
            "changed": self.changed,
            "is_noop": self.is_noop,
            "original_hash": self.original_hash,
            "updated_hash": self.updated_hash,
            "patch_hash": self.patch_hash,
        }

    def to_dict(self) -> dict[str, Any]:
        return self.canonical_dict()

    @staticmethod
    def _hash_text(value: str) -> str:
        return hashlib.sha256(
            value.encode("utf-8")
        ).hexdigest()