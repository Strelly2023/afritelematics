from __future__ import annotations

from afritech.ci.predictive_federation_validator import validate


def test_predictive_federation_validator_passes():
    assert validate() is True
