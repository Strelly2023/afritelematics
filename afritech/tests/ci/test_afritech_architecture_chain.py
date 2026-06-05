from __future__ import annotations

import pytest

from afritech.ci.afritech_architecture_chain import (
    ArchitectureChainValidator,
    ArchitectureViolation,
    validate,
)


def test_afritech_architecture_chain_passes():
    assert validate() is True


def test_afritech_architecture_chain_fails_closed_on_missing_adr_register(tmp_path):
    validator = ArchitectureChainValidator(root=tmp_path)

    with pytest.raises(ArchitectureViolation):
        validator.validate_adrs()
