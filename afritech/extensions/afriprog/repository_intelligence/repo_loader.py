from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SUPPORTED_EXTENSIONS = frozenset(
    {
        ".py",
        ".dart",
        ".yaml",
        ".yml",
    }
)

EXCLUDED_DIRECTORIES = frozenset(
    {
        ".dart_tool",
        ".expo",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "coverage_html",
        "htmlcov",
        "node_modules",
        "venv",
    }
)


class RepoLoaderError(Exception):
    """Raised when repository loading fails."""


@dataclass(frozen=True)
class RepositoryFile:
    path: str
    extension: str
    size_bytes: int

    def canonical_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "extension": self.extension,
            "size_bytes": self.size_bytes,
        }


class RepoLoader:
    """
    Read-only repository discovery.

    Constitutional properties:
    - deterministic ordering
    - read-only
    - no filesystem mutation
    - reproducible output
    """

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.validate_root()

    def validate_root(self) -> None:
        if not self.root.exists():
            raise RepoLoaderError(
                f"repository root does not exist: {self.root}"
            )

        if not self.root.is_dir():
            raise RepoLoaderError(
                f"repository root is not a directory: {self.root}"
            )

    def list_files(
        self,
        extensions: Iterable[str] | None = None,
    ) -> tuple[RepositoryFile, ...]:
        """
        Deterministically enumerate repository files.
        """

        extensions = (
            tuple(sorted(SUPPORTED_EXTENSIONS))
            if extensions is None
            else tuple(sorted(set(extensions)))
        )

        discovered: list[RepositoryFile] = []
        extension_set = set(extensions)

        for current_root, directories, filenames in os.walk(self.root):
            directories[:] = sorted(
                directory
                for directory in directories
                if directory not in EXCLUDED_DIRECTORIES
            )

            for filename in sorted(filenames):
                file_path = Path(current_root) / filename

                if file_path.suffix not in extension_set:
                    continue

                if not file_path.is_file():
                    continue

                relative_path = file_path.relative_to(self.root).as_posix()

                discovered.append(
                    RepositoryFile(
                        path=relative_path,
                        extension=file_path.suffix,
                        size_bytes=file_path.stat().st_size,
                    )
                )

        return tuple(
            sorted(
                discovered,
                key=lambda item: item.path,
            )
        )

    def list_python_files(self) -> tuple[RepositoryFile, ...]:
        return self.list_files([".py"])

    def list_flutter_files(self) -> tuple[RepositoryFile, ...]:
        return self.list_files([".dart"])

    def file_count(
        self,
        extensions: Iterable[str] | None = None,
    ) -> int:
        return len(self.list_files(extensions))

    def canonical_dict(self) -> dict[str, object]:
        return {
            "root": str(self.root),
            "file_count": self.file_count(),
        }
