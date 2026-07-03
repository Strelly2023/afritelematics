from __future__ import annotations

from architecture_validator.model import RuleResult, pass_or_fail
from architecture_validator.scanners.files import iter_text_files


def check_ui_authority(config: dict[str, object]) -> RuleResult:
    issues: list[str] = []
    forbidden = tuple(str(item) for item in config.get("forbidden_ui_endpoint_fragments", []))

    for path in iter_text_files(config.get("ui_source_roots", [])):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in forbidden:
            if pattern in text:
                issues.append(f"{path}: UI surface references forbidden authority endpoint: {pattern}")

    return pass_or_fail("UI Authority Boundary", issues)
