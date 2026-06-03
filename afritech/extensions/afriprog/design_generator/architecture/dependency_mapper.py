from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DependencyMap:
    dependencies: tuple[tuple[str, str], ...]

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "dependencies": [
                {"from": source, "to": target}
                for source, target in self.dependencies
            ],
        }


class DependencyMapper:
    """Map proposed modules into deterministic dependency direction."""

    def map(self, modules: tuple[str, ...]) -> DependencyMap:
        ordering = ("ui", "api", "application", "domain", "infrastructure", "validators", "tests")
        present = tuple(module for module in ordering if module in modules)
        dependencies: list[tuple[str, str]] = []

        for source, target in (
            ("ui", "api"),
            ("api", "application"),
            ("application", "domain"),
            ("application", "infrastructure"),
            ("validators", "domain"),
            ("tests", "api"),
            ("tests", "application"),
        ):
            if source in present and target in present:
                dependencies.append((source, target))

        return DependencyMap(dependencies=tuple(dependencies))
