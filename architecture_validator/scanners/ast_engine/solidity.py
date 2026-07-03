from __future__ import annotations

from pathlib import Path
from typing import Iterable

from architecture_validator.scanners.files import iter_text_files


class SolidityASTScanner:
    def __init__(self, roots: Iterable[str | Path], forbidden_patterns: Iterable[str]) -> None:
        self.roots = list(roots)
        self.forbidden_patterns = [str(pattern) for pattern in forbidden_patterns if str(pattern)]

    def scan(self) -> list[str]:
        issues: list[str] = []
        if not self.forbidden_patterns:
            return issues

        for path in iter_text_files(self.roots):
            if path.suffix != ".sol":
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in self.forbidden_patterns:
                if pattern in text:
                    issues.append(f"{path}: Solidity insecure pattern: {pattern}")
        return issues
