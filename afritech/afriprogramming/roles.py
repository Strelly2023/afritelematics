from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    OPERATOR = "OPERATOR"
    VERIFIER = "VERIFIER"
    OBSERVER = "OBSERVER"
    DEVELOPER = "DEVELOPER"


__all__ = ["Role"]
