from __future__ import annotations

from afritech.partner_governance import (
    PartnerGovernanceStore,
    build_partner_governance_record,
)


def create_store() -> PartnerGovernanceStore:
    record = build_partner_governance_record(
        org_id="org-test",
        organization="Test Org",
        country="AU",
        business_type="mobility",
        contact_email="test@example.com",
    )
    return PartnerGovernanceStore((record,))


def test_sla_state_persists_on_record() -> None:
    store = create_store()

    updated = store.record_usage("org-test", requests=10_000_000)

    assert updated.sla_state in {"warning", "breached"}
    assert updated.enforcement_state in {"throttled", "enabled"}


def test_enforcement_state_not_in_billing() -> None:
    store = create_store()

    updated = store.record_usage("org-test", requests=1000)

    assert "sla_state" not in updated.billing
    assert "enforcement_state" not in updated.billing


def test_requests_increment_independently() -> None:
    store = create_store()

    first = store.record_usage("org-test", requests=100)
    second = store.record_usage("org-test", requests=50)

    assert first.usage["requests"] == 100
    assert second.usage["requests"] == 150


def test_snapshot_matches_record() -> None:
    store = create_store()

    updated = store.record_usage("org-test", requests=1000)

    snapshot = store.usage_snapshot("org-test")

    assert snapshot["sla_state"] == updated.sla_state
    assert snapshot["enforcement_state"] == updated.enforcement_state


def test_sla_breach_persists() -> None:
    store = create_store()

    updated = store.record_usage("org-test", requests=10_000_000)

    snapshot = store.usage_snapshot("org-test")

    assert snapshot["sla_state"] == updated.sla_state
