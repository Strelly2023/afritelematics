from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class RepoReportBuilderError(Exception):
    """Raised when repository report generation fails."""


@dataclass(frozen=True)
class RepositorySummary:
    total_files: int
    tests: int
    contracts: int

    def canonical_dict(self) -> dict[str, int]:
        return {
            "total_files": self.total_files,
            "tests": self.tests,
            "contracts": self.contracts,
        }


class RepoReportBuilder:
    """
    Deterministic repository intelligence report builder.

    Constitutional properties:
    - deterministic
    - replay-safe
    - read-only by default
    - persistence is explicit
    """

    def __init__(self, repo_map: dict[str, Any]):
        if not isinstance(repo_map, dict):
            raise RepoReportBuilderError(
                "repo_map must be a dictionary"
            )

        self.repo_map = repo_map

    def summary(self) -> RepositorySummary:
        return RepositorySummary(
            total_files=len(self.repo_map.get("files", [])),
            tests=len(self.repo_map.get("tests", [])),
            contracts=len(self.repo_map.get("contracts", [])),
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary().canonical_dict(),
            "repository": self.repo_map,
        }

    def to_json_string(self) -> str:
        return json.dumps(
            self.canonical_dict(),
            indent=2,
            sort_keys=True,
        )

    def write_json(
        self,
        path: str | Path = "repo_intelligence.json",
    ) -> Path:
        output_path = Path(path)

        output_path.write_text(
            self.to_json_string(),
            encoding="utf-8",
        )

        return output_path.resolve()

    def report_size_bytes(self) -> int:
        return len(
            self.to_json_string().encode("utf-8")
        )