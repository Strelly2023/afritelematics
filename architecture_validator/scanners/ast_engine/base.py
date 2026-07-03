from __future__ import annotations

from typing import Protocol


class ASTEngine(Protocol):
    def scan(self) -> list[str]:
        """Return architecture violations discovered by the scanner."""
