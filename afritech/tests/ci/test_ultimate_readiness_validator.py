from __future__ import annotations

from afritech.ci.ultimate_readiness_validator import validate


def test_ultimate_readiness_validator_passes():
    assert validate() is True
