from __future__ import annotations

from pathlib import Path

import pytest

from afritech.ci import afripower_intelligence_validator as validator
from afritech.ci.afripower_intelligence_validator import (
    AFRIPowerValidationError,
    validate_metadata_contract,
    validate_projection_contracts,
    validate_required_files,
    validate_required_tests,
)


def test_validate_required_files_fails_when_file_missing(monkeypatch):
    monkeypatch.setattr(
        validator,
        "REQUIRED_IMPLEMENTATION_FILES",
        (Path("missing/implementation.py"),),
    )

    with pytest.raises(AFRIPowerValidationError):
        validate_required_files()


def test_validate_required_tests_fails_when_file_missing(monkeypatch):
    monkeypatch.setattr(
        validator,
        "REQUIRED_TEST_FILES",
        (Path("missing/test_file.py"),),
    )

    with pytest.raises(AFRIPowerValidationError):
        validate_required_tests()


@pytest.mark.parametrize(
    "field",
    (
        "runtime_authority",
        "enforcement_authority",
        "validation_authority",
        "replay_authority",
        "proof_authority",
        "ci_authority",
        "governance_authority",
        "decision_authority",
        "admissibility_authority",
        "intelligence_authority",
        "execution_authority",
        "authoritative",
        "mutation_allowed",
        "receipt_mutation_allowed",
        "proof_mutation_allowed",
        "governance_mutation_allowed",
        "runtime_dependency",
        "projection_creates_authority",
    ),
)
def test_validate_metadata_contract_rejects_false_fields_when_true(
    monkeypatch,
    field: str,
):
    metadata = validator.constitutional_afripower_metadata()
    metadata[field] = True

    monkeypatch.setattr(
        validator,
        "constitutional_afripower_metadata",
        lambda: metadata,
    )

    with pytest.raises(AFRIPowerValidationError):
        validate_metadata_contract()


@pytest.mark.parametrize(
    "field",
    (
        "reference_only",
        "read_only",
        "display_only",
        "observational_only",
        "projection_only",
        "enterprise_intelligence_only",
        "law_read_only",
        "law_non_authoritative",
        "law_display_only",
        "law_consumes_authority_only",
        "law_cannot_create_authority_surface",
        "law_cannot_influence_runtime",
        "law_cannot_influence_replay",
        "law_cannot_influence_proof",
        "law_cannot_influence_ci",
        "law_cannot_influence_governance",
    ),
)
def test_validate_metadata_contract_rejects_true_fields_when_false(
    monkeypatch,
    field: str,
):
    metadata = validator.constitutional_afripower_metadata()
    metadata[field] = False

    monkeypatch.setattr(
        validator,
        "constitutional_afripower_metadata",
        lambda: metadata,
    )

    with pytest.raises(AFRIPowerValidationError):
        validate_metadata_contract()


@pytest.mark.parametrize(
    ("projection_field", "bad_value"),
    (
        ("read_only", False),
        ("reference_only", False),
        ("display_only", False),
        ("creates_authority", True),
        ("runtime_authority", True),
        ("validation_authority", True),
        ("governance_authority", True),
    ),
)
def test_validate_projection_contracts_rejects_bad_graph_projection(
    monkeypatch,
    projection_field: str,
    bad_value: object,
):
    def bad_graph_projection(_payloads):
        return {
            "read_only": True,
            "reference_only": True,
            "display_only": True,
            "creates_authority": False,
            "runtime_authority": False,
            "validation_authority": False,
            "governance_authority": False,
            "nodes": [{"id": "node.001"}],
            "edges": [{"source_id": "a", "target_id": "b"}],
            projection_field: bad_value,
        }

    monkeypatch.setattr(
        validator,
        "build_graph_projection",
        bad_graph_projection,
    )

    with pytest.raises(AFRIPowerValidationError):
        validate_projection_contracts()


@pytest.mark.parametrize(
    ("projection_field", "bad_value"),
    (
        ("read_only", False),
        ("reference_only", False),
        ("display_only", False),
        ("creates_authority", True),
        ("runtime_authority", True),
        ("validation_authority", True),
        ("governance_authority", True),
    ),
)
def test_validate_projection_contracts_rejects_bad_model_projection(
    monkeypatch,
    projection_field: str,
    bad_value: object,
):
    def good_graph_projection(_payloads):
        return {
            "read_only": True,
            "reference_only": True,
            "display_only": True,
            "creates_authority": False,
            "runtime_authority": False,
            "validation_authority": False,
            "governance_authority": False,
            "nodes": [{"id": "node.001"}],
            "edges": [{"source_id": "a", "target_id": "b"}],
        }

    def bad_model_projection(_payloads):
        return {
            "read_only": True,
            "reference_only": True,
            "display_only": True,
            "creates_authority": False,
            "runtime_authority": False,
            "validation_authority": False,
            "governance_authority": False,
            "nodes": [{"id": "node.001"}],
            "edges": [{"source_id": "a", "target_id": "b"}],
            projection_field: bad_value,
        }

    monkeypatch.setattr(
        validator,
        "build_graph_projection",
        good_graph_projection,
    )
    monkeypatch.setattr(
        validator,
        "build_afripower_projection_dict",
        bad_model_projection,
    )

    with pytest.raises(AFRIPowerValidationError):
        validate_projection_contracts()


def test_validate_projection_contracts_rejects_non_list_nodes(monkeypatch):
    def bad_projection(_payloads):
        return {
            "read_only": True,
            "reference_only": True,
            "display_only": True,
            "creates_authority": False,
            "runtime_authority": False,
            "validation_authority": False,
            "governance_authority": False,
            "nodes": "bad",
            "edges": [{"source_id": "a", "target_id": "b"}],
        }

    monkeypatch.setattr(
        validator,
        "build_graph_projection",
        bad_projection,
    )

    with pytest.raises(AFRIPowerValidationError):
        validate_projection_contracts()


def test_validate_projection_contracts_rejects_non_list_edges(monkeypatch):
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
            "edges": "bad",
        }

    monkeypatch.setattr(
        validator,
        "build_graph_projection",
        bad_projection,
    )

    with pytest.raises(AFRIPowerValidationError):
        validate_projection_contracts()


def test_run_validation_handles_unexpected_exception(monkeypatch, capsys):
    def explode(*, require_tests: bool = False) -> None:
        raise RuntimeError("unexpected failure")

    monkeypatch.setattr(
        validator,
        "validate_afripower_intelligence_surface",
        explode,
    )

    result = validator.run_validation(())

    captured = capsys.readouterr()

    assert result == 1
    assert "AFRIPower intelligence validation FAILED" in captured.out
