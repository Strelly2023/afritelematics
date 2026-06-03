from __future__ import annotations

import pytest

from afritech.afripower.contracts import read_only_contract as contract_module
from afritech.afripower.contracts.read_only_contract import (
    AFRIPOWER_READ_ONLY_CONTRACT,
    AFRIPowerReadOnlyContract,
    assert_read_only_contract,
    read_only_contract_metadata,
)


def test_read_only_contract_instance_exists():
    assert isinstance(
        AFRIPOWER_READ_ONLY_CONTRACT,
        AFRIPowerReadOnlyContract,
    )


def test_contract_identity():
    assert AFRIPOWER_READ_ONLY_CONTRACT.component == "AFRIPower"
    assert AFRIPOWER_READ_ONLY_CONTRACT.version == "1.0"


def test_contract_required_safe_flags_are_true():
    assert AFRIPOWER_READ_ONLY_CONTRACT.read_only is True
    assert AFRIPOWER_READ_ONLY_CONTRACT.display_only is True
    assert AFRIPOWER_READ_ONLY_CONTRACT.reference_only is True
    assert AFRIPOWER_READ_ONLY_CONTRACT.projection_only is True
    assert AFRIPOWER_READ_ONLY_CONTRACT.enterprise_intelligence_only is True


def test_contract_authority_flags_are_false():
    assert AFRIPOWER_READ_ONLY_CONTRACT.authoritative is False
    assert AFRIPOWER_READ_ONLY_CONTRACT.runtime_authority is False
    assert AFRIPOWER_READ_ONLY_CONTRACT.validation_authority is False
    assert AFRIPOWER_READ_ONLY_CONTRACT.replay_authority is False
    assert AFRIPOWER_READ_ONLY_CONTRACT.proof_authority is False
    assert AFRIPOWER_READ_ONLY_CONTRACT.ci_authority is False
    assert AFRIPOWER_READ_ONLY_CONTRACT.governance_authority is False
    assert AFRIPOWER_READ_ONLY_CONTRACT.execution_authority is False
    assert AFRIPOWER_READ_ONLY_CONTRACT.projection_creates_authority is False


def test_contract_mutation_flags_are_false():
    assert AFRIPOWER_READ_ONLY_CONTRACT.mutation_allowed is False
    assert AFRIPOWER_READ_ONLY_CONTRACT.receipt_mutation_allowed is False
    assert AFRIPOWER_READ_ONLY_CONTRACT.proof_mutation_allowed is False
    assert AFRIPOWER_READ_ONLY_CONTRACT.governance_mutation_allowed is False


def test_contract_law_flags_are_true():
    assert AFRIPOWER_READ_ONLY_CONTRACT.law_read_only is True
    assert AFRIPOWER_READ_ONLY_CONTRACT.law_non_authoritative is True
    assert AFRIPOWER_READ_ONLY_CONTRACT.law_display_only is True
    assert AFRIPOWER_READ_ONLY_CONTRACT.law_consumes_authority_only is True
    assert AFRIPOWER_READ_ONLY_CONTRACT.law_cannot_create_authority_surface is True
    assert AFRIPOWER_READ_ONLY_CONTRACT.law_cannot_influence_runtime is True
    assert AFRIPOWER_READ_ONLY_CONTRACT.law_cannot_influence_replay is True
    assert AFRIPOWER_READ_ONLY_CONTRACT.law_cannot_influence_proof is True
    assert AFRIPOWER_READ_ONLY_CONTRACT.law_cannot_influence_ci is True
    assert AFRIPOWER_READ_ONLY_CONTRACT.law_cannot_influence_governance is True


def test_contract_canonical_dict_contains_boundary_fields():
    data = AFRIPOWER_READ_ONLY_CONTRACT.canonical_dict()

    assert data["component"] == "AFRIPower"
    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["authoritative"] is False
    assert data["runtime_authority"] is False
    assert data["projection_creates_authority"] is False


def test_read_only_contract_metadata_is_deterministic():
    first = read_only_contract_metadata()
    second = read_only_contract_metadata()

    assert first == second


def test_assert_read_only_contract_passes():
    assert_read_only_contract()


def test_assert_read_only_contract_fails_on_authority(monkeypatch):
    broken = AFRIPowerReadOnlyContract(
        **{
            **AFRIPOWER_READ_ONLY_CONTRACT.canonical_dict(),
            "runtime_authority": True,
        }
    )

    monkeypatch.setattr(
        contract_module,
        "AFRIPOWER_READ_ONLY_CONTRACT",
        broken,
    )

    with pytest.raises(RuntimeError):
        assert_read_only_contract()


def test_assert_read_only_contract_fails_on_mutation(monkeypatch):
    broken = AFRIPowerReadOnlyContract(
        **{
            **AFRIPOWER_READ_ONLY_CONTRACT.canonical_dict(),
            "mutation_allowed": True,
        }
    )

    monkeypatch.setattr(
        contract_module,
        "AFRIPOWER_READ_ONLY_CONTRACT",
        broken,
    )

    with pytest.raises(RuntimeError):
        assert_read_only_contract()


def test_assert_read_only_contract_fails_on_missing_safety(monkeypatch):
    broken = AFRIPowerReadOnlyContract(
        **{
            **AFRIPOWER_READ_ONLY_CONTRACT.canonical_dict(),
            "read_only": False,
        }
    )

    monkeypatch.setattr(
        contract_module,
        "AFRIPOWER_READ_ONLY_CONTRACT",
        broken,
    )

    with pytest.raises(RuntimeError):
        assert_read_only_contract()
