from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.novapay_runtime_api import build_novapay_runtime_router
from afritech.core_platform.canonical import hash_obj
from afritech.core_platform.hash_domains import HASH_DOMAINS
from afritech.core_platform.models import Identity
from afritech.core_platform.novapay_runtime import NovaPayRuntimeEngine, NovaPayTransferAdmissionError


def _client() -> TestClient:
    app = FastAPI()
    runtime = NovaPayRuntimeEngine()
    app.include_router(build_auth_router())
    app.include_router(build_novapay_runtime_router(runtime=runtime))
    return TestClient(app)


def _headers(role: str = "CUSTOMER", user_id: str = "sender-1", organization_id: str = "org-pay") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id)
    return {"Authorization": f"Bearer {token}"}


def _transfer_payload() -> dict[str, object]:
    return {
        "transfer_type": "Cross-Border Remittance",
        "recipient_name": "Amina Okello",
        "recipient_identifier": "+254700000001",
        "recipient_country": "KE",
        "amount": "100.00",
        "source_currency": "AUD",
        "source_country": "AU",
        "funding_source_type": "wallet",
        "funding_source_reference": "wallet-ref-1",
        "payout_method": "mobile_money",
        "use_case": "family_support",
        "memo": "school fees",
        "recipient_type": "individual",
        "live_provider": False,
        "auto_execute": False,
    }


def test_canonical_hash_preserves_order_and_normalizes_common_types() -> None:
    first = {
        "amount": Decimal("100.00"),
        "at": datetime(2026, 6, 29, 12, 0, tzinfo=timezone.utc),
        "blob": b"abc",
        "events": [{"sequence": 1}, {"sequence": 2}],
    }
    equivalent = {
        "blob": b"abc",
        "events": [{"sequence": 1}, {"sequence": 2}],
        "at": "2026-06-29T12:00:00+00:00",
        "amount": "100.00",
    }
    reordered_events = {
        **equivalent,
        "events": [{"sequence": 2}, {"sequence": 1}],
    }

    assert hash_obj(first, domain=HASH_DOMAINS["AUDIT_PACKAGE"]) == hash_obj(
        equivalent,
        domain=HASH_DOMAINS["AUDIT_PACKAGE"],
    )
    assert hash_obj(first, domain=HASH_DOMAINS["AUDIT_PACKAGE"]) != hash_obj(
        reordered_events,
        domain=HASH_DOMAINS["AUDIT_PACKAGE"],
    )


def test_novapay_runtime_admission_and_execution_flow() -> None:
    client = _client()

    jurisdictions = client.get("/v1/jurisdictions", headers=_headers())
    assert jurisdictions.status_code == 200
    assert jurisdictions.json()["jurisdictions"]
    policies = client.get("/v1/policies", headers=_headers())
    assert policies.status_code == 200
    assert policies.json()["policies"][0]["version"] == "2026.06"
    assert "LICENSE-EXEC-001" in policies.json()["policies"][0]["rules"]
    regions = client.get("/v1/regions", headers=_headers())
    assert regions.status_code == 200
    assert any(region["region_id"] == "region_au" for region in regions.json()["regions"])

    funding_source = client.post(
        "/v1/funding-sources/validate",
        headers=_headers(),
        json={
            "funding_source_type": "wallet",
            "owner_id": "sender-1",
            "provider": "novapay-wallet",
            "reference": "wallet-ref-1",
        },
    )
    assert funding_source.status_code == 200
    assert funding_source.json()["funding_source"]["type"] == "wallet"

    quote = client.post("/v1/transfers/quote", headers=_headers(), json=_transfer_payload())
    assert quote.status_code == 200
    quote_body = quote.json()
    assert quote_body["transfer"]["quote"]["quote_id"]
    assert quote_body["transfer"]["quote"]["corridor"] == "AU->KE:AUD->KES"
    assert quote_body["transfer"]["routing"]["corridor"] == "AU->KE:AUD->KES"
    assert quote_body["transfer"]["recipient"]["jurisdiction_id"] == "jur_ke"
    assert quote_body["transfer"]["compliance"]["transfer_id"] == quote_body["transfer_id"]
    assert quote_body["transfer"]["decision_trace"]["policy_id"] == "novapay.transfer.policy.v1"
    assert quote_body["transfer"]["routing"]["score"]["weights"]["liquidity"] == "0.20"
    assert quote_body["transfer"]["routing"]["region_routing"]["origin_region"] == "region_au"
    assert quote_body["transfer"]["routing"]["region_routing"]["primary_region"] == "region_ke"
    assert quote_body["transfer"]["routing"]["region_routing"]["execution_region"] == "region_ke"

    create = client.post("/v1/transfers", headers=_headers(), json=_transfer_payload())
    assert create.status_code == 200
    create_body = create.json()
    transfer_id = create_body["transfer_id"]
    assert create_body["transfer"]["status"] == "quoted"
    assert create_body["receipt"] is None

    execute = client.post(f"/v1/transfers/{transfer_id}/execute", headers=_headers(role="OPERATOR"))
    assert execute.status_code == 200
    execute_body = execute.json()
    assert execute_body["transfer"]["status"] in {"settled", "completed"}
    assert execute_body["receipt"]["signature"]["scheme"] == "ed25519"
    assert execute_body["verification"]["valid"] is True
    assert len(execute_body["ledger_entries"]) == 2
    assert execute_body["ledger_entries"][0]["entry_type"] == "DEBIT"
    assert execute_body["ledger_entries"][1]["entry_type"] == "CREDIT"
    assert execute_body["journal_entry"]["total_debit"] == execute_body["journal_entry"]["total_credit"]
    assert execute_body["transfer"]["policy_version_used"] == "2026.06"

    receipt = client.get(f"/v1/transfers/{transfer_id}/receipt", headers=_headers())
    assert receipt.status_code == 200
    assert receipt.json()["receipt"]["verification_code"]

    verification = client.get(f"/v1/transfers/{transfer_id}/verification", headers=_headers())
    assert verification.status_code == 200
    assert verification.json()["valid"] is True

    timeline = client.get(f"/v1/transfers/{transfer_id}/timeline", headers=_headers())
    assert timeline.status_code == 200
    assert len(timeline.json()["timeline"]) >= 2
    events = timeline.json()["timeline"]
    assert [event["sequence"] for event in events] == [1, 2, 3, 4, 5]
    assert [event["aggregate_version"] for event in events] == [1, 2, 3, 4, 5]
    assert events[0]["previous_event_hash"] == "0" * 64
    assert events[1]["previous_event_hash"] == events[0]["event_hash"]
    assert events[-1]["event_hash"]
    assert events[0]["event_hash"] == hash_obj(
        {key: value for key, value in events[0].items() if key != "event_hash"},
        domain=HASH_DOMAINS["TRANSFER_EVENT"],
    )
    assert events[0]["event_hash"] != hash_obj(
        {key: value for key, value in events[0].items() if key != "event_hash"},
        domain=HASH_DOMAINS["TRANSFER_RECEIPT"],
    )

    replay = client.get(f"/v1/transfers/{transfer_id}/replay", headers=_headers())
    assert replay.status_code == 200
    assert replay.json()["replay_valid"] is True
    assert replay.json()["ledger_entries"] == execute_body["ledger_entries"]
    assert replay.json()["policy"]["version"] == "2026.06"
    assert replay.json()["snapshot"]["version"] == 5

    audit_package = client.get(f"/v1/transfers/{transfer_id}/audit-package", headers=_headers(role="VERIFIER"))
    assert audit_package.status_code == 200
    assert audit_package.json()["verification"]["valid"] is True
    assert audit_package.json()["verification"]["transfer_merkle_valid"] is True
    assert audit_package.json()["verification"]["ledger_checkpoint_valid"] is True
    assert audit_package.json()["verification"]["reconciliation_valid"] is True
    assert audit_package.json()["audit_package"]["event_chain_valid"] is True
    assert audit_package.json()["audit_package"]["transfer_merkle_root"]
    assert audit_package.json()["audit_package"]["global_ledger_root"]
    assert audit_package.json()["audit_package"]["ledger_checkpoint"]["snapshot_hash"]
    assert audit_package.json()["audit_package"]["reconciliation"]["status"] == "clear"
    assert len(audit_package.json()["audit_package"]["merkle_proofs"]) == len(events)
    first_proof = audit_package.json()["audit_package"]["merkle_proofs"][0]
    assert first_proof["event_id"] == events[0]["event_id"]
    assert first_proof["event_type"] == events[0]["event_type"]
    assert first_proof["sequence"] == events[0]["sequence"]
    assert first_proof["aggregate_version"] == events[0]["aggregate_version"]
    assert first_proof["event_hash"] == events[0]["event_hash"]
    assert first_proof["leaf_hash"]

    audit_bundle = client.get(f"/v1/transfers/{transfer_id}/audit-bundle", headers=_headers(role="VERIFIER"))
    assert audit_bundle.status_code == 200
    assert audit_bundle.json()["view"] == "novapay_transfer_audit_bundle"
    assert audit_bundle.json()["verification"]["valid"] is True
    assert audit_bundle.json()["audit_bundle"]["verification_instructions"]

    treasury = client.get("/v1/treasury/snapshot", headers=_headers(role="ADMIN"))
    assert treasury.status_code == 200
    assert treasury.json()["liquidity_positions"]
    assert treasury.json()["prefunding_accounts"]
    account_types = {account["account_type"] for account in treasury.json()["accounts"]}
    assert {"customer", "settlement", "treasury", "fee", "fx_reserve", "suspense"}.issubset(account_types)
    exposure = next(item for item in treasury.json()["settlement_exposures"] if item["transfer_id"] == transfer_id)
    assert exposure["status"] == "settled"
    assert exposure["amount_pending"] == "0"
    assert len(treasury.json()["outbox"]) == 5
    assert {record["status"] for record in treasury.json()["outbox"]} == {"published"}
    assert all(record["payload_json"]["event_hash"] for record in treasury.json()["outbox"])
    assert treasury.json()["snapshots"][0]["version"] == 5
    snapshot = treasury.json()["snapshots"][0]
    assert snapshot["snapshot_root_hash"]
    assert snapshot["event_hash"] == events[-1]["event_hash"]
    assert treasury.json()["global_ledger_root"]
    assert treasury.json()["ledger_checkpoint"]["snapshot_hash"]
    assert treasury.json()["reconciliation"]["status"] == "clear"


def test_novapay_runtime_rejects_unsupported_transfer_type() -> None:
    client = _client()
    payload = _transfer_payload()
    payload["transfer_type"] = "Unsupported Rail"

    response = client.post("/v1/transfers", headers=_headers(), json=payload)
    assert response.status_code == 400
    assert response.json()["detail"].startswith("transfer_type_not_supported")


def test_novapay_runtime_rejects_insufficient_liquidity() -> None:
    client = _client()
    payload = _transfer_payload()
    payload["amount"] = "10000.00"

    create = client.post("/v1/transfers", headers=_headers(), json=payload)
    assert create.status_code == 400
    assert create.json()["detail"].startswith("insufficient_liquidity")


def test_novapay_runtime_rejects_license_transfer_type_before_execution() -> None:
    client = _client()
    payload = _transfer_payload()
    payload["transfer_type"] = "Payroll"

    response = client.post("/v1/transfers", headers=_headers(), json=payload)

    assert response.status_code == 400
    assert response.json()["detail"].startswith("license_transfer_type_not_allowed")


def test_novapay_replay_normalizes_event_ledger_and_journal_payloads() -> None:
    runtime = NovaPayRuntimeEngine()
    identity = Identity(
        identity_id="sender-1",
        email="sender-1@novapay.local",
        roles=("CUSTOMER",),
        organization_id="org-pay",
        kyc_status="verified",
    )
    record = runtime.create_transfer(_transfer_payload(), identity=identity, auto_execute=True)

    executed_event = next(event for event in record.events if event.event_type == "transfer.executed.v1")
    executed_event.payload["ledger_entries"][0]["amount"] = Decimal("100.00")
    executed_event.payload["ledger_entries"][0]["balance_after"] = Decimal("100.00")
    executed_event.payload["journal_entry"]["total_debit"] = Decimal("100.00")
    executed_event.payload["journal_entry"]["lines"][0]["amount"] = Decimal("100.00")

    replay = runtime.replay_transfer(record.transfer.transfer_id)

    assert replay["replay_valid"] is True
    assert replay["ledger_entries"] == [entry.canonical() for entry in record.ledger_entries]
    assert replay["journal_entry"] == record.journal_entry.canonical()


def test_novapay_replay_rejects_duplicate_event_redelivery() -> None:
    runtime = NovaPayRuntimeEngine()
    identity = Identity(
        identity_id="sender-1",
        email="sender-1@novapay.local",
        roles=("CUSTOMER",),
        organization_id="org-pay",
        kyc_status="verified",
    )
    record = runtime.create_transfer(_transfer_payload(), identity=identity, auto_execute=True)
    duplicate_stream = (*record.events, record.events[-1])
    runtime.store.records[record.transfer.transfer_id] = replace(record, events=duplicate_stream)

    with pytest.raises(NovaPayTransferAdmissionError, match="event_duplicate_id"):
        runtime.replay_transfer(record.transfer.transfer_id)


def test_novapay_replay_rejects_out_of_order_events() -> None:
    runtime = NovaPayRuntimeEngine()
    identity = Identity(
        identity_id="sender-1",
        email="sender-1@novapay.local",
        roles=("CUSTOMER",),
        organization_id="org-pay",
        kyc_status="verified",
    )
    record = runtime.create_transfer(_transfer_payload(), identity=identity, auto_execute=True)
    reordered_stream = (
        record.events[0],
        record.events[2],
        record.events[1],
        *record.events[3:],
    )
    runtime.store.records[record.transfer.transfer_id] = replace(record, events=reordered_stream)

    with pytest.raises(NovaPayTransferAdmissionError, match="invalid_transition"):
        runtime.replay_transfer(record.transfer.transfer_id)


def test_novapay_replay_rejects_unregistered_schema_version() -> None:
    runtime = NovaPayRuntimeEngine()
    identity = Identity(
        identity_id="sender-1",
        email="sender-1@novapay.local",
        roles=("CUSTOMER",),
        organization_id="org-pay",
        kyc_status="verified",
    )
    record = runtime.create_transfer(_transfer_payload(), identity=identity, auto_execute=True)
    invalid_event = replace(record.events[0], schema_version=99)
    runtime.store.records[record.transfer.transfer_id] = replace(
        record,
        events=(invalid_event, *record.events[1:]),
    )

    with pytest.raises(NovaPayTransferAdmissionError, match="schema_version_invalid"):
        runtime.replay_transfer(record.transfer.transfer_id)


def test_novapay_replay_rejects_policy_mismatch() -> None:
    runtime = NovaPayRuntimeEngine()
    identity = Identity(
        identity_id="sender-1",
        email="sender-1@novapay.local",
        roles=("CUSTOMER",),
        organization_id="org-pay",
        kyc_status="verified",
    )
    record = runtime.create_transfer(_transfer_payload(), identity=identity, auto_execute=True)
    record.admission.policy["version"] = "1900.01"
    modified_events = []
    previous_hash = "0" * 64
    previous_version = 0
    for event in record.events:
        payload = dict(event.payload)
        if event.event_type == "transfer.requested.v1":
            payload["admission"] = dict(payload["admission"])
            payload["admission"]["policy"] = dict(payload["admission"]["policy"])
            payload["admission"]["policy"]["version"] = "1900.01"
        modified = runtime._build_transfer_event(
            transfer_id=event.transfer_id,
            event_type=event.event_type,
            payload=payload,
            decision_trace=event.decision_trace,
            sequence=event.sequence,
            previous_event_hash=previous_hash,
            previous_aggregate_version=previous_version,
        )
        modified_events.append(modified)
        previous_hash = modified.event_hash
        previous_version = modified.aggregate_version
    runtime.store.records[record.transfer.transfer_id] = replace(record, events=tuple(modified_events))

    with pytest.raises(NovaPayTransferAdmissionError, match="policy_replay_mismatch"):
        runtime.replay_transfer(record.transfer.transfer_id)


def test_novapay_replay_rejects_event_hash_tampering() -> None:
    runtime = NovaPayRuntimeEngine()
    identity = Identity(
        identity_id="sender-1",
        email="sender-1@novapay.local",
        roles=("CUSTOMER",),
        organization_id="org-pay",
        kyc_status="verified",
    )
    record = runtime.create_transfer(_transfer_payload(), identity=identity, auto_execute=True)
    executed_event = next(event for event in record.events if event.event_type == "transfer.executed.v1")
    executed_event.payload["ledger_entries"][0]["amount"] = "101.00"

    with pytest.raises(NovaPayTransferAdmissionError, match="event_hash_invalid"):
        runtime.replay_transfer(record.transfer.transfer_id)


def test_novapay_execute_rejects_stale_aggregate_version() -> None:
    runtime = NovaPayRuntimeEngine()
    identity = Identity(
        identity_id="sender-1",
        email="sender-1@novapay.local",
        roles=("CUSTOMER",),
        organization_id="org-pay",
        kyc_status="verified",
    )
    record = runtime.create_transfer(_transfer_payload(), identity=identity, auto_execute=False)

    with pytest.raises(NovaPayTransferAdmissionError, match="aggregate_version_conflict"):
        runtime.execute_transfer(record.transfer.transfer_id, identity=identity, expected_version=1)


def test_novapay_outbox_records_publish_for_each_runtime_event() -> None:
    runtime = NovaPayRuntimeEngine()
    identity = Identity(
        identity_id="sender-1",
        email="sender-1@novapay.local",
        roles=("CUSTOMER",),
        organization_id="org-pay",
        kyc_status="verified",
    )
    record = runtime.create_transfer(_transfer_payload(), identity=identity, auto_execute=True)

    outbox = runtime.build_outbox()

    assert len(outbox) == 5
    assert {item["status"] for item in outbox} == {"published"}
    assert [item["aggregate_version"] for item in outbox] == [1, 2, 3, 4, 5]
    assert {item["aggregate_id"] for item in outbox} == {record.transfer.transfer_id}
    assert all(item["payload_json"]["aggregate_version"] == item["aggregate_version"] for item in outbox)


def test_novapay_outbox_read_rejects_payload_corruption() -> None:
    runtime = NovaPayRuntimeEngine()
    identity = Identity(
        identity_id="sender-1",
        email="sender-1@novapay.local",
        roles=("CUSTOMER",),
        organization_id="org-pay",
        kyc_status="verified",
    )
    runtime.create_transfer(_transfer_payload(), identity=identity, auto_execute=True)
    runtime.store.outbox[0].payload_json["status"] = "tampered"

    with pytest.raises(NovaPayTransferAdmissionError, match="outbox_payload_corrupted"):
        runtime.build_outbox()


def test_novapay_audit_package_is_portable_and_verifiable() -> None:
    runtime = NovaPayRuntimeEngine()
    identity = Identity(
        identity_id="sender-1",
        email="sender-1@novapay.local",
        roles=("CUSTOMER",),
        organization_id="org-pay",
        kyc_status="verified",
    )
    record = runtime.create_transfer(_transfer_payload(), identity=identity, auto_execute=True)

    package = runtime.build_audit_package(record.transfer.transfer_id)
    verification = runtime.verify_audit_package(package)

    assert package["schema"] == "novapay.audit_package.v1"
    assert package["canonical_format"] == "canonical.v1"
    assert package["hash_domain_version"] == 1
    assert package["hash_algorithm"] == "sha256"
    assert package["root_hash"]
    assert package["signature"]["scheme"] == "ed25519"
    assert package["snapshot"]["version"] == 5
    assert package["snapshot"]["snapshot_root_hash"]
    assert "event_chain_valid" in package
    assert "ledger_hash" in package
    assert "replay_hash" in package
    assert verification["protocol_valid"] is True
    assert verification["valid"] is True


def test_novapay_audit_package_rejects_protocol_identifier_tampering() -> None:
    runtime = NovaPayRuntimeEngine()
    identity = Identity(
        identity_id="sender-1",
        email="sender-1@novapay.local",
        roles=("CUSTOMER",),
        organization_id="org-pay",
        kyc_status="verified",
    )
    record = runtime.create_transfer(_transfer_payload(), identity=identity, auto_execute=True)
    package = runtime.build_audit_package(record.transfer.transfer_id)
    package["canonical_format"] = "canonical.v2"

    verification = runtime.verify_audit_package(package)

    assert verification["valid"] is False
    assert verification["protocol_valid"] is False


def test_novapay_audit_package_rejects_snapshot_root_tampering() -> None:
    runtime = NovaPayRuntimeEngine()
    identity = Identity(
        identity_id="sender-1",
        email="sender-1@novapay.local",
        roles=("CUSTOMER",),
        organization_id="org-pay",
        kyc_status="verified",
    )
    record = runtime.create_transfer(_transfer_payload(), identity=identity, auto_execute=True)
    package = runtime.build_audit_package(record.transfer.transfer_id)
    package["snapshot"]["ledger_hash"] = "tampered"

    verification = runtime.verify_audit_package(package)

    assert verification["valid"] is False
    assert verification["snapshot_root_valid"] is False


def test_novapay_audit_package_recomputes_event_chain_flag() -> None:
    runtime = NovaPayRuntimeEngine()
    identity = Identity(
        identity_id="sender-1",
        email="sender-1@novapay.local",
        roles=("CUSTOMER",),
        organization_id="org-pay",
        kyc_status="verified",
    )
    record = runtime.create_transfer(_transfer_payload(), identity=identity, auto_execute=True)
    package = runtime.build_audit_package(record.transfer.transfer_id)
    package["event_chain_valid"] = False

    verification = runtime.verify_audit_package(package)

    assert verification["event_chain_valid"] is True
    assert verification["valid"] is True


def test_novapay_audit_package_normalizes_ledger_before_hashing() -> None:
    runtime = NovaPayRuntimeEngine()
    identity = Identity(
        identity_id="sender-1",
        email="sender-1@novapay.local",
        roles=("CUSTOMER",),
        organization_id="org-pay",
        kyc_status="verified",
    )
    record = runtime.create_transfer(_transfer_payload(), identity=identity, auto_execute=True)
    package = runtime.build_audit_package(record.transfer.transfer_id)
    package["ledger"][0]["amount"] = Decimal("100.00")
    package["ledger"][0]["balance_after"] = Decimal("100.00")

    verification = runtime.verify_audit_package(package)

    assert verification["ledger_hash_valid"] is True
    assert verification["valid"] is True


def test_novapay_audit_package_rejects_ledger_hash_tampering() -> None:
    runtime = NovaPayRuntimeEngine()
    identity = Identity(
        identity_id="sender-1",
        email="sender-1@novapay.local",
        roles=("CUSTOMER",),
        organization_id="org-pay",
        kyc_status="verified",
    )
    record = runtime.create_transfer(_transfer_payload(), identity=identity, auto_execute=True)
    package = runtime.build_audit_package(record.transfer.transfer_id)
    package["ledger"][0]["amount"] = "101.00"

    verification = runtime.verify_audit_package(package)

    assert verification["valid"] is False
    assert verification["ledger_hash_valid"] is False
