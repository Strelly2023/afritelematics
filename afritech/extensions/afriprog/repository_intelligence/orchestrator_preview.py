from __future__ import annotations

from pathlib import Path
from typing import Any

from afritech.extensions.afriprog.repository_intelligence.contract_locator import (
    ContractLocator,
)
from afritech.extensions.afriprog.repository_intelligence.repo_loader import (
    RepoLoader,
    RepositoryFile,
)
from afritech.extensions.afriprog.repository_intelligence.report_builder import (
    RepoReportBuilder,
    RepositorySummary,
)
from afritech.extensions.afriprog.repository_intelligence.structure_mapper import (
    DirectoryGroup,
    LayerMap,
    StructureMapper,
)
from afritech.extensions.afriprog.repository_intelligence.surface_locator import (
    SurfaceLocator,
    SurfaceMap,
)
from afritech.extensions.afriprog.repository_intelligence.test_mapper import (
    TestMapper,
    TestTargetMap,
)


class RepositoryIntelligencePreviewError(Exception):
    """Raised when repository intelligence preview fails."""


def _canonicalize_collection(items: Any) -> Any:
    """
    Convert repository-intelligence dataclasses into deterministic JSON-safe values.
    """

    if hasattr(items, "canonical_dict"):
        return items.canonical_dict()

    if isinstance(items, dict):
        return {
            str(key): _canonicalize_collection(value)
            for key, value in sorted(items.items(), key=lambda item: str(item[0]))
        }

    if isinstance(items, (list, tuple)):
        return [
            _canonicalize_collection(item)
            for item in items
        ]

    return items


def run_repository_intelligence(
    root: str | Path = ".",
    output_path: str | Path | None = None,
) -> RepositorySummary:
    """
    Run Phase-1 AfriProgramming repository intelligence.

    Constitutional behavior:
    - read-only repository inspection
    - deterministic ordering
    - non-authoritative classification
    - optional explicit report persistence
    """

    loader = RepoLoader(root)

    files: tuple[RepositoryFile, ...] = loader.list_files()
    file_paths = tuple(item.path for item in files)

    structure = StructureMapper(file_paths)
    layers: LayerMap = structure.detect_layers()
    directories: tuple[DirectoryGroup, ...] = structure.group_by_directory()

    test_mapper = TestMapper(file_paths)
    test_files = test_mapper.find_tests()
    test_mappings: tuple[TestTargetMap, ...] = test_mapper.map_test_targets()

    surfaces: SurfaceMap = SurfaceLocator(file_paths).detect_surfaces()

    contracts = ContractLocator(file_paths).find_contracts()

    report: dict[str, Any] = {
        "root": str(Path(root).resolve()),
        "files": _canonicalize_collection(files),
        "directories": _canonicalize_collection(directories),
        "layers": _canonicalize_collection(layers),
        "tests": list(test_files),
        "test_mappings": _canonicalize_collection(test_mappings),
        "surfaces": _canonicalize_collection(surfaces),
        "contracts": _canonicalize_collection(contracts),
    }

    builder = RepoReportBuilder(report)

    if output_path is not None:
        builder.write_json(output_path)

    return builder.summary()


if __name__ == "__main__":
    summary = run_repository_intelligence(output_path=None)
    print(summary.canonical_dict())
