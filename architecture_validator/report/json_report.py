from __future__ import annotations

from pathlib import Path
from typing import Iterable

from architecture_validator.model import RuleResult
from architecture_validator.report.formatter import format_json_report


def write_json_report(results: Iterable[RuleResult], path: str | Path) -> None:
    Path(path).write_text(format_json_report(results) + "\n", encoding="utf-8")
