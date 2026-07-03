from __future__ import annotations

from pathlib import Path

from architecture_validator.model import RuleResult, pass_or_fail
from architecture_validator.scanners.files import iter_text_files, read_text


TEST_ROOTS = (
    "afritech/tests",
    "dashboard/tests",
    "rider_app/tests",
    "driver_app/tests",
    "afriride_system/tests",
)


def check_tests_alignment(config: dict[str, object]) -> RuleResult:
    issues: list[str] = []
    test_corpus = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in iter_text_files(TEST_ROOTS))
    workflow = read_text(str(config["workflow_path"])) if Path(str(config["workflow_path"])).exists() else ""

    for test_name in config.get("required_tests", []):
        if str(test_name) not in test_corpus:
            issues.append(f"Missing required architecture-alignment test: {test_name}")

    if "architecture_validator.cli" not in workflow and "architecture_validator/cli.py" not in workflow:
        issues.append("Architecture workflow does not run architecture compliance validator")

    return pass_or_fail("Test And CI Alignment", issues)
