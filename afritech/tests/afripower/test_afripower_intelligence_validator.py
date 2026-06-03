from __future__ import annotations

from pathlib import Path

import pytest

from afritech.ci import afripower_intelligence_validator as validator
from afritech.ci.afripower_intelligence_validator import (
    AFRIPowerValidationError,
    validate_afripower_intelligence_surface,
    validate_identity,
    validate_law_flags,
    validate_metadata_contract,
    validate_no_authority,
    validate_no_mutation,
    validate_projection_contracts,
    validate_required_files,
    validate_required_tests,
    validate_safety_flags,
)


# =============================================================================
# REQUIRED FILES
# =============================================================================


def test_required_implementation_files_declared():
    assert validator.REQUIRED_IMPLEMENTATION_FILES
    assert Path("afritech/afripower/constants.py") in (
        validator.REQUIRED_IMPLEMENTATION_FILES
    )
    assert Path("afritech/afripower/projection_models.py") in (
        validator.REQUIRED_IMPLEMENTATION_FILES
    )
    assert Path("afritech/afripower/graph_projection.py") in (
        validator.REQUIRED_IMPLEMENTATION_FILES
    )


def test_required_test_files_declared():
    assert validator.REQUIRED_TEST_FILES
    assert Path("afritech/tests/afripower/test_constants.py") in (
        validator.REQUIRED_TEST_FILES
    )
    assert Path("afritech/tests/afripower/test_projection_models.py") in (
        validator.REQUIRED_TEST_FILES
    )
    assert Path("afritech/tests/afripower/test_graph_projection.py") in (
        validator.REQUIRED_TEST_FILES
    )
    assert Path(
        "afritech/tests/afripower/test_afripower_intelligence_validator.py"
    ) in validator.REQUIRED_TEST_FILES


def test_validate_required_files_passes():
    validate_required_files()


def test_validate_required_tests_passes():
    validate_required_tests()


# =============================================================================
# IDENTITY VALIDATION
# =============================================================================


def test_validate_identity_passes():
    validate_identity()


def test_validator_name_is_stable():
    assert validator.VALIDATOR_NAME == (
        "afritech.ci.afripower_intelligence_validator"
    )


# =============================================================================
# AUTHORITY VALIDATION
# =============================================================================


def test_validate_no_authority_passes():
    validate_no_authority()


def test_authority_flags_are_declared():
    assert validator.AUTHORITY_FLAGS


def test_all_authority_flags_are_false():
    for name, value in validator.AUTHORITY_FLAGS:
        assert value is False, name


def test_validate_no_authority_fails_on_authority_flag(monkeypatch):
    monkeypatch.setattr(
        validator,
        "AUTHORITY_FLAGS",
        (("RUNTIME_AUTHORITY", True),),
    )

    with pytest.raises(AFRIPowerValidationError):
        validate_no_authority()


# =============================================================================
# MUTATION VALIDATION
# =============================================================================


def test_validate_no_mutation_passes():
    validate_no_mutation()


def test_mutation_flags_are_declared():
    assert validator.MUTATION_FLAGS


def test_all_mutation_flags_are_false():
    for name, value in validator.MUTATION_FLAGS:
        assert value is False, name


def test_validate_no_mutation_fails_on_mutation_flag(monkeypatch):
    monkeypatch.setattr(
        validator,
        "MUTATION_FLAGS",
        (("MUTATION_ALLOWED", True),),
    )

    with pytest.raises(AFRIPowerValidationError):
        validate_no_mutation()


# =============================================================================
# SAFETY VALIDATION
# =============================================================================


def test_validate_safety_flags_passes():
    validate_safety_flags()


def test_safety_flags_are_declared():
    assert validator.SAFETY_FLAGS


def test_all_safety_flags_are_true():
    for name, value in validator.SAFETY_FLAGS:
        assert value is True, name


def test_validate_safety_flags_fails_when_false(monkeypatch):
    monkeypatch.setattr(
        validator,
        "SAFETY_FLAGS",
        (("READ_ONLY", False),),
    )

    with pytest.raises(AFRIPowerValidationError):
        validate_safety_flags()


# =============================================================================
# LAW VALIDATION
# =============================================================================


def test_validate_law_flags_passes():
    validate_law_flags()


def test_law_flags_are_declared():
    assert validator.LAW_FLAGS


def test_all_law_flags_are_true():
    for name, value in validator.LAW_FLAGS:
        assert value is True, name


def test_validate_law_flags_fails_when_false(monkeypatch):
    monkeypatch.setattr(
        validator,
        "LAW_FLAGS",
        (("LAW_AFRIPOWER_IS_READ_ONLY", False),),
    )

    with pytest.raises(AFRIPowerValidationError):
        validate_law_flags()


# =============================================================================
# METADATA CONTRACT
# =============================================================================


def test_validate_metadata_contract_passes():
    validate_metadata_contract()


def test_validate_metadata_contract_fails_on_bad_false_field(monkeypatch):
    def bad_metadata() -> dict[str, object]:
        return {
            "runtime_authority": True,
            "enforcement_authority": False,
            "validation_authority": False,
            "replay_authority": False,
            "proof_authority": False,
            "ci_authority": False,
            "governance_authority": False,
            "decision_authority": False,
            "admissibility_authority": False,
            "intelligence_authority": False,
            "execution_authority": False,
            "authoritative": False,
            "mutation_allowed": False,
            "receipt_mutation_allowed": False,
            "proof_mutation_allowed": False,
            "governance_mutation_allowed": False,
            "runtime_dependency": False,
            "projection_creates_authority": False,
            "reference_only": True,
            "read_only": True,
            "display_only": True,
            "observational_only": True,
            "projection_only": True,
            "enterprise_intelligence_only": True,
            "law_read_only": True,
            "law_non_authoritative": True,
            "law_display_only": True,
            "law_consumes_authority_only": True,
            "law_cannot_create_authority_surface": True,
            "law_cannot_influence_runtime": True,
            "law_cannot_influence_replay": True,
            "law_cannot_influence_proof": True,
            "law_cannot_influence_ci": True,
            "law_cannot_influence_governance": True,
        }

    monkeypatch.setattr(
        validator,
        "constitutional_afripower_metadata",
        bad_metadata,
    )

    with pytest.raises(AFRIPowerValidationError):
        validate_metadata_contract()


def test_validate_metadata_contract_fails_on_bad_true_field(monkeypatch):
    def bad_metadata() -> dict[str, object]:
        return {
            "runtime_authority": False,
            "enforcement_authority": False,
            "validation_authority": False,
            "replay_authority": False,
            "proof_authority": False,
            "ci_authority": False,
            "governance_authority": False,
            "decision_authority": False,
            "admissibility_authority": False,
            "intelligence_authority": False,
            "execution_authority": False,
            "authoritative": False,
            "mutation_allowed": False,
            "receipt_mutation_allowed": False,
            "proof_mutation_allowed": False,
            "governance_mutation_allowed": False,
            "runtime_dependency": False,
            "projection_creates_authority": False,
            "reference_only": True,
            "read_only": False,
            "display_only": True,
            "observational_only": True,
            "projection_only": True,
            "enterprise_intelligence_only": True,
            "law_read_only": True,
            "law_non_authoritative": True,
            "law_display_only": True,
            "law_consumes_authority_only": True,
            "law_cannot_create_authority_surface": True,
            "law_cannot_influence_runtime": True,
            "law_cannot_influence_replay": True,
            "law_cannot_influence_proof": True,
            "law_cannot_influence_ci": True,
            "law_cannot_influence_governance": True,
        }

    monkeypatch.setattr(
        validator,
        "constitutional_afripower_metadata",
        bad_metadata,
    )

    with pytest.raises(AFRIPowerValidationError):
        validate_metadata_contract()


# =============================================================================
# PROJECTION CONTRACTS
# =============================================================================


def test_validate_projection_contracts_passes():
    validate_projection_contracts()


def test_validate_projection_contracts_fails_on_authoritative_projection(
    monkeypatch,
):
    def bad_projection(_payloads):
        return {
            "read_only": True,
            "reference_only": True,
            "display_only": True,
            "creates_authority": True,
            "runtime_authority": False,
            "validation_authority": False,
            "governance_authority": False,
            "nodes": [{"id": "node.001"}],
            "edges": [{"source_id": "a", "target_id": "b"}],
        }

    monkeypatch.setattr(validator, "build_graph_projection", bad_projection)

    with pytest.raises(AFRIPowerValidationError):
        validate_projection_contracts()


def test_validate_projection_contracts_fails_on_runtime_authority(
    monkeypatch,
):
    def bad_projection(_payloads):
        return {
            "read_only": True,
            "reference_only": True,
            "display_only": True,
            "creates_authority": False,
            "runtime_authority": True,
            "validation_authority": False,
            "governance_authority": False,
            "nodes": [{"id": "node.001"}],
            "edges": [{"source_id": "a", "target_id": "b"}],
        }

    monkeypatch.setattr(validator, "build_graph_projection", bad_projection)

    with pytest.raises(AFRIPowerValidationError):
        validate_projection_contracts()


def test_validate_projection_contracts_fails_without_nodes(monkeypatch):
    def bad_projection(_payloads):
        return {
            "read_only": True,
            "reference_only": True,
            "display_only": True,
            "creates_authority": False,
            "runtime_authority": False,
            "validation_authority": False,
            "governance_authority": False,
            "nodes": [],
            "edges": [{"source_id": "a", "target_id": "b"}],
        }

    monkeypatch.setattr(validator, "build_graph_projection", bad_projection)

    with pytest.raises(AFRIPowerValidationError):
        validate_projection_contracts()


def test_validate_projection_contracts_fails_without_edges(monkeypatch):
    def bad_projection(_payloads):
        return {
            "read_only": True,
            "reference_only": True,
            "display_only": True,
            "creates_authority": False,
            "runtime_authority": False,
            "validation_authority": False,
            "governance_authority": False,
            "nodes": [{"id": "node.001"}],
            "edges": [],
        }

    monkeypatch.setattr(validator, "build_graph_projection", bad_projection)

    with pytest.raises(AFRIPowerValidationError):
        validate_projection_contracts()


# =============================================================================
# FULL SURFACE VALIDATION
# =============================================================================


def test_validate_afripower_intelligence_surface_passes_without_test_gate():
    validate_afripower_intelligence_surface(require_tests=False)


def test_validate_afripower_intelligence_surface_passes_with_test_gate():
    validate_afripower_intelligence_surface(require_tests=True)


def test_run_validation_passes_without_test_gate(capsys):
    result = validator.run_validation(())

    captured = capsys.readouterr()

    assert result == 0
    assert "AFRIPower intelligence validation PASSED" in captured.out


def test_run_validation_passes_with_test_gate(capsys):
    result = validator.run_validation(("--require-tests",))

    captured = capsys.readouterr()

    assert result == 0
    assert "AFRIPower intelligence validation PASSED" in captured.out


def test_run_validation_fails_closed(monkeypatch, capsys):
    def fail_validation(*, require_tests: bool = False) -> None:
        raise AFRIPowerValidationError("forced failure")

    monkeypatch.setattr(
        validator,
        "validate_afripower_intelligence_surface",
        fail_validation,
    )

    result = validator.run_validation(())

    captured = capsys.readouterr()

    assert result == 1
    assert "AFRIPower intelligence validation FAILED" in captured.out


def test_main_returns_zero():
    assert validator.main() == 0
