from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ValidatorContext:
    config: dict[str, Any]
    root: Path = Path(".")

    def path(self, key: str) -> Path | None:
        raw = self.config.get(key)
        if raw is None or raw == "":
            return None
        return self.root / str(raw)
