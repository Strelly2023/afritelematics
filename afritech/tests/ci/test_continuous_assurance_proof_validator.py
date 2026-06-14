from __future__ import annotations

from afritech.ci.continuous_assurance_proof_validator import validate


def test_continuous_assurance_proof_validator_passes():
    report = validate()

    assert report.verified is True
    assert len(report.registry_hash) == 64
    assert len(report.proof_hash) == 64
    assert report.binding_count > 0
    assert report.invariant_count > 0
    assert report.guard_count > 0

