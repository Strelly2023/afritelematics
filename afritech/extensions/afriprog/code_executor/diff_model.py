from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any


class DiffModelError(Exception):
    """Raised when diff model construction fails."""


@dataclass(frozen=True)
class Diff:
    """
    Canonical AfriProgramming diff proposal.

    Constitutional properties:
    - immutable
    - deterministic
    - evidence-ready
    - non-authoritative
    - proposal-only
    """

    file_path: str
    diff_text: str
    diff_type: str = "unified_diff"
    write_permitted: bool = False

    def __post_init__(self) -> None:
        if not self.file_path.strip():
            raise DiffModelError("file_path must not be empty")

        if not self.diff_type.strip():
            raise DiffModelError("diff_type must not be empty")

        if self.write_permitted:
            raise DiffModelError(
                "write_permitted must remain False in code_executor proposal mode"
            )

    @property
    def is_empty(self) -> bool:
        return self.diff_text.strip() == ""

    @property
    def changed(self) -> bool:
        return not self.is_empty

    @property
    def diff_hash(self) -> str:
        material = "|".join(
            (
                self.file_path,
                self.diff_type,
                self.diff_text,
                str(self.write_permitted),
            )
        )

        return hashlib.sha256(
            material.encode("utf-8")
        ).hexdigest()

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "diff_type": self.diff_type,
            "write_permitted": self.write_permitted,
            "changed": self.changed,
            "is_empty": self.is_empty,
            "diff_hash": self.diff_hash,
        }

    def to_dict(self) -> dict[str, Any]:
        return self.canonical_dict()