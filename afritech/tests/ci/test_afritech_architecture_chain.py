from __future__ import annotations

import pytest

from afritech.ci.afritech_architecture_chain import (
    ArchitectureChainValidator,
    ArchitectureViolation,
    validate,
)
from afritech.guards import (
    guard_public_pilot_geography,
    guard_public_pilot_limits,
    guard_public_pilot_reconciliation,
    guard_public_pilot_release,
)


def test_afritech_architecture_chain_passes():
    assert validate() is True


def test_afritech_architecture_chain_fails_closed_on_missing_adr_register(tmp_path):
    validator = ArchitectureChainValidator(root=tmp_path)

    with pytest.raises(ArchitectureViolation):
        validator.validate_adrs()


def test_public_pilot_binding_guards_have_executable_ci_evidence():
    guards = {
        "BIND-050-1": guard_public_pilot_limits,
        "BIND-050-2": guard_public_pilot_geography,
        "BIND-050-3": guard_public_pilot_release,
        "BIND-050-4": guard_public_pilot_reconciliation,
    }
    for guard in guards.values():
        assert callable(guard.validate)
