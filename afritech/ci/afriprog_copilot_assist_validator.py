"""Validate Copilot-style Afriprog assistance as tooling only."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from afritech.extensions.afriprog.copilot_assist import (
    ASSISTANCE_KINDS,
    collect_context,
    explain_code,
    generate_suggestion,
)


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_NAME = "afritech.ci.afriprog_copilot_assist_validator"
COPILOT_ROOT = ROOT / "afritech/extensions/afriprog/copilot_assist"
REQUIRED_FILES = (
    COPILOT_ROOT / "__init__.py",
    COPILOT_ROOT / "suggestion_model.py",
    COPILOT_ROOT / "context_collector.py",
    COPILOT_ROOT / "suggestion_engine.py",
    COPILOT_ROOT / "safety_classifier.py",
    COPILOT_ROOT / "validation_gate.py",
    COPILOT_ROOT / "explanation_builder.py",
)


class AfriprogCopilotAssistValidationError(RuntimeError):
    """Raised when Copilot-style assistance violates tooling constraints."""


def fail(message: str) -> None:
    raise AfriprogCopilotAssistValidationError(message)


def validate_required_files() -> None:
    missing = tuple(path for path in REQUIRED_FILES if not path.is_file())
    if missing:
        fail("missing Copilot Assist files: " + ", ".join(map(str, missing)))


def validate_all_feature_kinds() -> None:
    expected = {
        "inline_code_suggestion",
        "context_file_analysis",
        "explain_this_code",
        "generate_tests",
        "fix_failing_validator",
        "generate_contract_binding",
        "generate_replay_fixture",
        "suggest_refactor",
        "create_rollback_plan",
        "confidence_and_validators",
    }
    if set(ASSISTANCE_KINDS) != expected:
        fail("Copilot Assist feature kind registry mismatch")

    for kind in ASSISTANCE_KINDS:
        suggestion = generate_suggestion(kind=kind, intent="demo", target="target")
        payload = suggestion.canonical_dict()
        if payload["authority"] != "developer_assistance_only":
            fail(f"{kind} gained authority")
        if payload["accepted"] is not False:
            fail(f"{kind} must not be accepted directly")
        if payload["mutates_runtime"] is not False:
            fail(f"{kind} must not mutate runtime")
        if not payload["required_validators"]:
            fail(f"{kind} must declare required validators")


def validate_context_and_explanation() -> None:
    context = collect_context(
        target="afritech/example.py",
        files={"afritech/example.py": "def example():\n    return True\n"},
    )
    explanation = explain_code(
        target="afritech/example.py",
        code="def example():\n    return True\n",
    )
    if context["context_authority"] != "advisory_only":
        fail("context collector must remain advisory")
    if context["mutates_runtime"] is not False:
        fail("context collector must not mutate runtime")
    if explanation["is_proof"] is not False:
        fail("code explanation must not be proof")
    if explanation["requires_validator_confirmation"] is not True:
        fail("code explanation must require validator confirmation")


def validate_cli_commands() -> None:
    commands = (
        ("suggest", "add driver availability endpoint"),
        ("fix", "--validator", "proposal_lifecycle_completion_validator"),
        ("explain", "afritech/proposals/activation.py"),
        ("testgen", "afritech/runtime/admission/"),
        ("replaygen", "proposal-123"),
    )
    for command in commands:
        completed = subprocess.run(
            [sys.executable, "-m", "afritech.cli.main", *command, "--json"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            shell=False,
            timeout=30,
        )
        if completed.returncode != 0:
            fail(f"afri {' '.join(command)} failed: {completed.stderr}")
        if '"accepted": false' not in completed.stdout:
            fail(f"afri {' '.join(command)} must not accept suggestions")
        if '"runtime_mutation": false' not in completed.stdout:
            fail(f"afri {' '.join(command)} must deny runtime mutation")


def validate() -> None:
    validate_required_files()
    validate_all_feature_kinds()
    validate_context_and_explanation()
    validate_cli_commands()


def main() -> int:
    try:
        validate()
        print("Afriprog Copilot Assist validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog Copilot Assist validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
