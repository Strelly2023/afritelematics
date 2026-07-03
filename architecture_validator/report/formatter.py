from __future__ import annotations

import json
from typing import Iterable

from architecture_validator.model import RuleResult


def format_text_report(results: Iterable[RuleResult]) -> str:
    lines = ["Architecture Compliance Report", ""]
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        lines.append(f"{status} - {result.name}")
        for issue in result.issues:
            lines.append(f"  - {issue}")
    return "\n".join(lines)


def format_json_report(results: Iterable[RuleResult]) -> str:
    return json.dumps([result.as_dict() for result in results], indent=2, sort_keys=True)
