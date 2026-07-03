from __future__ import annotations

from architecture_validator.model import RuleResult, pass_or_fail
from architecture_validator.scanners.files import read_text


def check_documentation(config: dict[str, object]) -> RuleResult:
    issues: list[str] = []
    doc_path = str(config["docs_path"])
    content = read_text(doc_path)

    for section in config.get("required_sections", []):
        if str(section) not in content:
            issues.append(f"Missing required section in {doc_path}: {section}")

    for fragment in config.get("required_fragments", []):
        if str(fragment) not in content:
            issues.append(f"Missing required normative fragment in {doc_path}: {fragment}")

    for pattern in config.get("forbidden_patterns", []):
        if str(pattern) in content:
            issues.append(f"Forbidden transcript/debug content in {doc_path}: {pattern}")

    return pass_or_fail("Documentation Governance", issues)
