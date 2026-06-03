from __future__ import annotations

import pytest
from django.core.exceptions import ImproperlyConfigured

from afritech.ci.governance_projection_validator import validate


try:
    from afritech.governance_projection.importer import project_governance
except ImproperlyConfigured:
    project_governance = None


def test_governance_projection_validator_passes():
    validate()


def test_governance_projection_importer_is_documentary_only():
    if project_governance is None:
        pytest.skip("Django settings are not configured for governance projection importer.")

    bundle = project_governance()

    assert bundle.adrs
    for collection in (
        bundle.adrs,
        bundle.invariants,
        bundle.rules,
        bundle.bindings,
        bundle.ci_checks,
        bundle.non_claims,
        bundle.next_steps,
    ):
        assert collection
        for item in collection:
            assert item.projection_status == "DOCUMENTARY"
            assert item.projection_is_documentary_only is True
            assert item.runtime_authority is False
            assert item.enforcement_authority is False


def test_consensus_and_federated_adrs_remain_documentary_projection():
    if project_governance is None:
        pytest.skip("Django settings are not configured for governance projection importer.")

    bundle = project_governance()
    adrs = {item.source_id: item for item in bundle.adrs}

    assert adrs["ADR-0016"].runtime_authoritative_declared is False
    assert adrs["ADR-0018"].runtime_authoritative_declared is False
