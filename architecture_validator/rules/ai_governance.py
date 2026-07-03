from __future__ import annotations

from architecture_validator.model import RuleResult, pass_or_fail
from architecture_validator.scanners.files import iter_text_files, read_text


FORBIDDEN_AI_AUTHORITY_PATTERNS = (
    "ai_execute_payment",
    "ai_assign_driver",
    "ai_suspend_account",
    "ai_modify_trust_evidence",
    "autonomous_payment_execution",
)


def check_ai_governance(config: dict[str, object]) -> RuleResult:
    issues: list[str] = []
    docs = read_text(str(config["docs_path"]))

    for required in (
        "AI modules SHALL:",
        "AI modules SHALL NOT:",
        "Execution authority SHALL remain with NovaPower and the designated",
    ):
        if required not in docs:
            issues.append(f"Missing AI governance requirement: {required}")

    for path in iter_text_files(config.get("ui_source_roots", [])):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in FORBIDDEN_AI_AUTHORITY_PATTERNS:
            if pattern in text:
                issues.append(f"{path}: forbidden AI authority pattern: {pattern}")

    return pass_or_fail("AI Governance", issues)
