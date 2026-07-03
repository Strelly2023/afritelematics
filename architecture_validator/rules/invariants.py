from __future__ import annotations

from architecture_validator.model import RuleResult, pass_or_fail
from architecture_validator.scanners.files import read_text


REQUIRED_INVARIANTS = (
    "User interfaces SHALL NOT execute business authority.",
    "APIs SHALL validate and route requests only.",
    "NovaPower SHALL evaluate policy before execution.",
    "NovaRide Core SHALL own ride lifecycle state.",
    "NovaPay SHALL own payment execution.",
    "NovaTrust SHALL own trust verification.",
    "Replay SHALL remain the authoritative operational evidence.",
    "AI SHALL provide recommendations only unless explicitly authorized.",
    "Every authoritative action SHALL produce audit evidence.",
    "Every public contract SHALL be versioned.",
)


def check_invariants(config: dict[str, object]) -> RuleResult:
    issues: list[str] = []
    content = read_text(str(config["docs_path"]))

    for invariant in REQUIRED_INVARIANTS:
        if invariant not in content:
            issues.append(f"Missing architecture invariant: {invariant}")

    if "## System Truth Model" not in content:
        issues.append("Missing System Truth Model section")
    if "Only authoritative systems may mutate their domain." not in content:
        issues.append("System Truth Model does not restrict mutation to authoritative systems")

    return pass_or_fail("Architecture Invariants", issues)
