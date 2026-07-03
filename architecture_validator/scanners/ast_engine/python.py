from __future__ import annotations

from pathlib import Path
from typing import Iterable

from architecture_validator.scanners.ast_scanner import scan_python_ast


class PythonASTScanner:
    def __init__(self, roots: Iterable[str | Path], forbidden_call_names: Iterable[str]) -> None:
        self.roots = list(roots)
        self.forbidden_call_names = list(forbidden_call_names)

    def scan(self) -> list[str]:
        return scan_python_ast(self.roots, self.forbidden_call_names)
