from __future__ import annotations

from architecture_validator.model import RuleResult, pass_or_fail
from architecture_validator.scanners.files import read_text


def check_security(config: dict[str, object]) -> RuleResult:
    issues: list[str] = []
    docs = read_text(str(config["docs_path"]))
    api_source = read_text(str(config["api_source_path"]))

    for required in (
        "All access MUST be authenticated.",
        "All requests MUST be authorized.",
        "All operations MUST be auditable.",
        "All sensitive actions MUST be replay-verifiable.",
        "All security controls SHALL be centrally enforced through NovaPower policies.",
        "Applications MUST NOT:",
        "All access MUST flow through NovaPower-controlled services.",
    ):
        if required not in docs:
            issues.append(f"Missing security requirement: {required}")

    for source_fragment in ("rbac", "token", "require_roles"):
        if source_fragment not in api_source:
            issues.append(f"API source missing security enforcement signal: {source_fragment}")

    return pass_or_fail("Security Compliance", issues)
