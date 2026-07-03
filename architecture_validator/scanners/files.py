from __future__ import annotations

from pathlib import Path
from typing import Iterable


TEXT_SUFFIXES = {
    ".dart",
    ".js",
    ".jsx",
    ".md",
    ".py",
    ".sol",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}


def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def iter_text_files(roots: Iterable[str | Path]) -> Iterable[Path]:
    for root in roots:
        root_path = Path(root)
        if not root_path.exists():
            continue
        if root_path.is_file():
            if root_path.suffix in TEXT_SUFFIXES:
                yield root_path
            continue
        for path in root_path.rglob("*"):
            if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
                continue
            if any(part in {"node_modules", "dist", "dist-web-prototype", ".expo"} for part in path.parts):
                continue
            yield path
