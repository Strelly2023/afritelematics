from __future__ import annotations

import subprocess
import sys

import pytest

from afritech.ci import data_decentralization_validator as validator
from afritech.data_governance.contracts import (
    AccessMode,
    DataAccessContract,
    DataGovernanceViolation,
)
from afritech.data_governance.guards import (
    DataWriteIntent,
    guard_cross_domain_access,
    guard_data_write,
    guard_owner_domain,
)
from afritech.data_governance.registry import validate_data_governance_registry


def test_data_decentralization_validator_passes():
    assert validator.validate() is True


def test_data_decentralization_validator_cli_passes():
    result = subprocess.run(
        [sys.executable, "-m", "afritech.ci.data_decentralization_validator"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Data decentralization validation PASSED" in result.stdout
    assert "INV-DATA-001" in result.stdout


def test_data_governance_registry_passes():
    assert validate_data_governance_registry() is True


def test_guard_owner_domain_requires_owner_domain_and_id():
    with pytest.raises(DataGovernanceViolation, match="owner_domain"):
        guard_owner_domain({"id": "record-1"})

    with pytest.raises(DataGovernanceViolation, match="id"):
        guard_owner_domain({"owner_domain": "AfriRide"})


def test_guard_data_write_allows_owner_domain():
    guard_data_write(
        DataWriteIntent(
            actor_domain="AfriRide",
            owner_domain="AfriRide",
            resource="rides",
            entity_id="ride-001",
            payload={"status": "completed"},
        )
    )


def test_guard_data_write_blocks_non_owner_domain():
    with pytest.raises(DataGovernanceViolation, match="only owner domain"):
        guard_data_write(
            DataWriteIntent(
                actor_domain="AfriPay",
                owner_domain="AfriRide",
                resource="rides",
                entity_id="ride-001",
                payload={"status": "completed"},
            )
        )


def test_guard_cross_domain_access_requires_owner_contract():
    with pytest.raises(DataGovernanceViolation, match="does not own"):
        guard_cross_domain_access(
            DataAccessContract(
                contract_id="contract-001",
                requester_domain="AfriRide",
                owner_domain="AfriPay",
                resource="rides",
                access_mode=AccessMode.API,
                purpose="read ride evidence",
            )
        )


def test_guard_cross_domain_access_allows_declared_api_contract():
    guard_cross_domain_access(
        DataAccessContract(
            contract_id="contract-002",
            requester_domain="AfriPay",
            owner_domain="AfriRide",
            resource="rides",
            access_mode=AccessMode.API,
            purpose="reference ride service evidence without payment activation",
        )
    )
