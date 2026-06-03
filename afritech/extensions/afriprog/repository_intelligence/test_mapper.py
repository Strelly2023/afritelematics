from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
#afritech/extensions/afriprog/repository_intelligence/test_mapper.py

class TestMapperError(Exception):
    """Raised when test mapping fails."""


@dataclass(frozen=True)
class TestTargetMap:
    test_file: str
    target_candidates: tuple[str, ...]

    def canonical_dict(self) -> dict[str, object]:
        return {
            "test_file": self.test_file,
            "target_candidates": list(self.target_candidates),
            "candidate_count": len(self.target_candidates),
        }


class TestMapper:
    """
    Deterministic read-only test mapper.

    Constitutional properties:
    - read-only
    - deterministic
    - inference only
    - non-authoritative
    """

    def __init__(self, files: Iterable[str]):
        normalized = tuple(sorted(str(Path(file_path)) for file_path in files))

        if any(not path for path in normalized):
            raise TestMapperError("file paths must not be empty")

        self.files = normalized

    def find_tests(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                file_path
                for file_path in self.files
                if self._is_test_file(file_path)
            )
        )

    def map_test_targets(self) -> tuple[TestTargetMap, ...]:
        mappings: list[TestTargetMap] = []

        for test_file in self.find_tests():
            base_name = self._infer_target_base_name(test_file)

            candidates = tuple(
                sorted(
                    file_path
                    for file_path in self.files
                    if file_path != test_file
                    and base_name
                    and self._is_candidate_target(
                        file_path=file_path,
                        base_name=base_name,
                    )
                )
            )

            mappings.append(
                TestTargetMap(
                    test_file=test_file,
                    target_candidates=candidates,
                )
            )

        return tuple(
            sorted(
                mappings,
                key=lambda item: item.test_file,
            )
        )

    def test_count(self) -> int:
        return len(self.find_tests())

    def canonical_dict(self) -> dict[str, object]:
        return {
            "file_count": len(self.files),
            "test_count": self.test_count(),
            "test_mappings": [
                item.canonical_dict()
                for item in self.map_test_targets()
            ],
        }

    @staticmethod
    def _is_test_file(file_path: str) -> bool:
        path = Path(file_path)
        name = path.name

        if path.suffix == ".py":
            return (
                name.startswith("test_")
                or name.endswith("_test.py")
                or "tests" in path.parts
            )

        if path.suffix == ".dart":
            return name.endswith("_test.dart")

        return False

    @staticmethod
    def _infer_target_base_name(test_file: str) -> str:
        name = Path(test_file).name

        if name.startswith("test_"):
            name = name.removeprefix("test_")

        if name.endswith("_test.dart"):
            name = name.removesuffix("_test.dart")

        if name.endswith("_test.py"):
            name = name.removesuffix("_test.py")

        if name.endswith(".py"):
            name = name.removesuffix(".py")

        if name.endswith(".dart"):
            name = name.removesuffix(".dart")

        return name

    @staticmethod
    def _is_candidate_target(
        file_path: str,
        base_name: str,
    ) -> bool:
        path = Path(file_path)

        if path.suffix not in {".py", ".dart"}:
            return False

        if TestMapper._is_test_file(file_path):
            return False

        return base_name in path.stem