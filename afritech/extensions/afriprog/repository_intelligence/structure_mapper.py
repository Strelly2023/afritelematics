from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


class StructureMapperError(Exception):
    """Raised when repository structure mapping fails."""


@dataclass(frozen=True)
class DirectoryGroup:
    directory: str
    files: tuple[str, ...]

    def canonical_dict(self) -> dict[str, object]:
        return {
            "directory": self.directory,
            "files": list(self.files),
            "file_count": len(self.files),
        }


@dataclass(frozen=True)
class LayerMap:
    tests: tuple[str, ...]
    ci: tuple[str, ...]
    guards: tuple[str, ...]
    constitution: tuple[str, ...]
    applications: tuple[str, ...]
    extensions: tuple[str, ...]

    def canonical_dict(self) -> dict[str, object]:
        return {
            "tests": list(self.tests),
            "ci": list(self.ci),
            "guards": list(self.guards),
            "constitution": list(self.constitution),
            "applications": list(self.applications),
            "extensions": list(self.extensions),
        }


class StructureMapper:
    """
    Deterministic read-only repository structure mapper.

    Constitutional properties:
    - read-only
    - deterministic ordering
    - no filesystem mutation
    - no authority assignment
    - classification only
    """

    def __init__(self, files: Iterable[str]):
        normalized = tuple(sorted(str(Path(item)) for item in files))

        if any(not item for item in normalized):
            raise StructureMapperError("file paths must not be empty")

        self.files = normalized

    def group_by_directory(self) -> tuple[DirectoryGroup, ...]:
        mapping: dict[str, list[str]] = defaultdict(list)

        for file_path in self.files:
            path = Path(file_path)
            mapping[str(path.parent)].append(str(path))

        return tuple(
            DirectoryGroup(
                directory=directory,
                files=tuple(sorted(paths)),
            )
            for directory, paths in sorted(mapping.items())
        )

    def detect_layers(self) -> LayerMap:
        layers: dict[str, list[str]] = {
            "tests": [],
            "ci": [],
            "guards": [],
            "constitution": [],
            "applications": [],
            "extensions": [],
        }

        for file_path in self.files:
            layer = self._classify_layer(file_path)
            layers[layer].append(file_path)

        return LayerMap(
            tests=tuple(sorted(layers["tests"])),
            ci=tuple(sorted(layers["ci"])),
            guards=tuple(sorted(layers["guards"])),
            constitution=tuple(sorted(layers["constitution"])),
            applications=tuple(sorted(layers["applications"])),
            extensions=tuple(sorted(layers["extensions"])),
        )

    def directory_count(self) -> int:
        return len(self.group_by_directory())

    def canonical_dict(self) -> dict[str, object]:
        return {
            "file_count": len(self.files),
            "directory_count": self.directory_count(),
            "layers": self.detect_layers().canonical_dict(),
            "directories": [
                group.canonical_dict()
                for group in self.group_by_directory()
            ],
        }

    @staticmethod
    def _classify_layer(file_path: str) -> str:
        parts = set(Path(file_path).parts)

        if "tests" in parts:
            return "tests"

        if "ci" in parts:
            return "ci"

        if "guards" in parts:
            return "guards"

        if "constitution" in parts:
            return "constitution"

        if "extensions" in parts:
            return "extensions"

        return "applications"