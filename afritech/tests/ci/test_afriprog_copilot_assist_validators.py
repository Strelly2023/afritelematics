from __future__ import annotations

import subprocess
import sys

from afritech.extensions.afriprog.copilot_assist import (
    ASSISTANCE_KINDS,
    classify_suggestion,
    collect_context,
    explain_code,
    generate_suggestion,
    validate_suggestion_gate,
)
from afritech.ci import (
    afriprog_ai_suggestion_non_authority_validator,
    afriprog_copilot_assist_validator,
    afriprog_inline_fix_validation_gate,
)


VALIDATORS = (
    afriprog_copilot_assist_validator,
    afriprog_ai_suggestion_non_authority_validator,
    afriprog_inline_fix_validation_gate,
)


def test_copilot_assist_supports_all_requested_feature_kinds():
    assert set(ASSISTANCE_KINDS) == {
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

    for kind in ASSISTANCE_KINDS:
        suggestion = generate_suggestion(kind=kind, intent="demo", target="target")
        payload = suggestion.canonical_dict()
        classification = classify_suggestion(suggestion)

        assert payload["authority"] == "developer_assistance_only"
        assert payload["accepted"] is False
        assert payload["mutates_runtime"] is False
        assert classification["admissible"] is False
        assert classification["confidence_is_certification"] is False
        assert payload["required_validators"]


def test_context_explanation_and_inline_fix_gate_are_non_authoritative():
    context = collect_context(
        target="afritech/example.py",
        files={"afritech/example.py": "def example():\n    return True\n"},
    )
    explanation = explain_code(
        target="afritech/example.py",
        code="def example():\n    return True\n",
    )
    suggestion = generate_suggestion(
        kind="fix_failing_validator",
        intent="fix validator",
        target="proposal_lifecycle_completion_validator",
    )

    blocked = validate_suggestion_gate(suggestion)
    ready = validate_suggestion_gate(
        suggestion,
        validators_passed=suggestion.required_validators,
        replay_passed=True,
        governance_approved=True,
    )

    assert context["context_authority"] == "advisory_only"
    assert context["mutates_runtime"] is False
    assert explanation["is_proof"] is False
    assert blocked["status"] == "blocked"
    assert blocked["accepted"] is False
    assert ready["status"] == "ready_for_governed_proposal"
    assert ready["accepted"] is False
    assert ready["proposal_required"] is True


def test_afri_copilot_style_cli_commands_emit_unaccepted_suggestions():
    commands = (
        ("suggest", "add driver availability endpoint"),
        ("fix", "--validator", "proposal_lifecycle_completion_validator"),
        ("explain", "afritech/proposals/activation.py"),
        ("testgen", "afritech/runtime/admission/"),
        ("replaygen", "proposal-123"),
    )
    for command in commands:
        result = subprocess.run(
            [sys.executable, "-m", "afritech.cli.main", *command, "--json"],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert '"accepted": false' in result.stdout
        assert '"runtime_mutation": false' in result.stdout
        assert "developer_assistance_only" in result.stdout


def test_copilot_assist_validators_pass_directly():
    afriprog_copilot_assist_validator.validate()
    afriprog_ai_suggestion_non_authority_validator.validate_ai_suggestion_non_authority()
    afriprog_inline_fix_validation_gate.validate_inline_fix_validation_gate()


def test_copilot_assist_validator_cli_entrypoints_pass():
    for validator in VALIDATORS:
        result = subprocess.run(
            [sys.executable, "-m", validator.VALIDATOR_NAME],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert "PASSED" in result.stdout
