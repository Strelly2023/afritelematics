from __future__ import annotations

import pytest

from afritech.afritpps.domain_contracts import (
    DOMAIN_CONTRACTS,
    AfriTPPSContractError,
    execute_domain_operation,
    get_domain_contract,
)
from afritech.models import EventRecord, EvidenceBundle


def test_domain_contract_registry_contains_required_domains_and_blocks_afripay():
    assert set(DOMAIN_CONTRACTS) == {
        "AfriRide",
        "AfriConnect",
        "AfriPay",
        "AfriHealth",
        "AfriLearning",
        "AfriTalent",
        "AfriMarket",
        "AfriHome",
        "AfriID",
        "AfriCloud",
    }
    assert get_domain_contract("AfriRide").identity == "Mobility Execution System"
    assert get_domain_contract("AfriPay").execution_allowed is False


@pytest.mark.django_db
def test_domain_operation_executes_through_tpps_and_trust_kernel():
    outcome = execute_domain_operation(
        operation_id="op.ride.complete.001",
        domain="AfriRide",
        operation="TripCompleted",
        actor_id="driver:D001",
        subject_id="ride:001",
        payload={"ride_id": "ride:001", "driver_id": "D001"},
        signature={"signature_mode": "development_adapter"},
    )

    event = EventRecord.objects.get(event_id=outcome.event_id)
    EvidenceBundle.objects.get(event=event)

    assert outcome.verified is True
    assert outcome.domain == "AfriRide"
    assert outcome.action == "TripCompleted"
    assert event.event_type == "AfriTPPSOperationExecuted"


def test_domain_operation_rejects_missing_required_payload_fields():
    with pytest.raises(AfriTPPSContractError, match="driver_id"):
        execute_domain_operation(
            operation_id="op.ride.complete.invalid",
            domain="AfriRide",
            operation="TripCompleted",
            actor_id="driver:D001",
            subject_id="ride:001",
            payload={"ride_id": "ride:001"},
            signature={"signature_mode": "development_adapter"},
        )


def test_afripay_domain_execution_is_blocked_until_evidence_gate():
    with pytest.raises(AfriTPPSContractError, match="DESIGNED_BLOCKED"):
        execute_domain_operation(
            operation_id="op.pay.raw.001",
            domain="AfriPay",
            operation="RawTransactionEvidence",
            actor_id="operator:001",
            subject_id="tx:001",
            payload={
                "transaction_id": "tx:001",
                "payer": "rider",
                "payee": "driver",
                "amount": 10,
                "currency": "AUD",
                "method": "cash",
                "outcome": "completed",
            },
            signature={"signature_mode": "development_adapter"},
        )


def test_unknown_domain_and_operation_fail_closed():
    with pytest.raises(AfriTPPSContractError, match="unknown AfriTPPS domain"):
        get_domain_contract("AfriUnknown")

    with pytest.raises(AfriTPPSContractError, match="AfriRide.UnknownOperation"):
        get_domain_contract("AfriRide").operation_contract("UnknownOperation")
