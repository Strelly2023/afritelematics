from __future__ import annotations

from afritech.chain.types import ChainReceipt
from afritech.ecosystem_evolution import (
    build_ecosystem_evolution_certificate,
    load_live_ecosystem_anchor,
    publish_live_ecosystem_anchor,
    record_live_ecosystem_anchor,
    verify_ecosystem_evolution_certificate,
)


def test_level16_ecosystem_certificate_verifies_adoption_and_standards():
    certificate = build_ecosystem_evolution_certificate()
    verification = verify_ecosystem_evolution_certificate(certificate)

    assert certificate.classification == "LEVEL_16_ECOSYSTEM_TRUST_INFRASTRUCTURE"
    assert certificate.level == "LEVEL_16"
    assert certificate.status == "ECOSYSTEM_EVOLUTION_READY"
    assert verification["verified"] is True
    assert verification["ecosystem_hash_valid"] is True
    assert verification["organizations"]["organization_count"] >= 3
    assert verification["government_adoption"]["government_profile_count"] >= 2
    assert verification["live_public_ledger_anchoring"]["verified"] is True
    assert verification["interoperable_standard"]["standard_id"] == (
        "AFRITECH_GLOBAL_TRUST_INTEROPERABILITY_STANDARD"
    )
    assert verification["guarantees"]["multi_organization_trust_networks"] is True
    assert verification["guarantees"]["cross_government_adoption_ready"] is True


def test_level16_accepts_live_public_ledger_receipt_when_supplied():
    receipt = ChainReceipt(
        tx_hash="0x" + "a" * 64,
        network="sepolia",
        block_number=123,
        explorer_url="https://sepolia.etherscan.io/tx/" + "a" * 64,
        status="live",
        chain_id=11155111,
        chain_name="Ethereum Sepolia",
        proof_hash="b" * 64,
        authority="smart_contract",
        source="test",
    )

    certificate = build_ecosystem_evolution_certificate(live_receipt=receipt)
    verification = verify_ecosystem_evolution_certificate(certificate)

    assert verification["verified"] is True
    assert verification["live_public_ledger_anchoring"]["status"] == "LIVE_PUBLIC_LEDGER_ANCHORED"
    assert verification["live_public_ledger_anchoring"]["live_receipt_verified"] is True


def test_level16_persists_live_receipt_for_public_verification(tmp_path, monkeypatch):
    monkeypatch.setenv("AFRITECH_ECOSYSTEM_LIVE_RECEIPT_FILE", str(tmp_path / "live.json"))
    receipt = ChainReceipt(
        tx_hash="0x" + "d" * 64,
        network="sepolia",
        status="live",
        chain_id=11155111,
        chain_name="Ethereum Sepolia",
        proof_hash="e" * 64,
        authority="smart_contract",
        source="test",
    )

    path = record_live_ecosystem_anchor(receipt)
    loaded = load_live_ecosystem_anchor()
    certificate = build_ecosystem_evolution_certificate()
    verification = verify_ecosystem_evolution_certificate(certificate)

    assert path.exists()
    assert loaded is not None
    assert loaded["tx_hash"] == receipt.tx_hash
    assert verification["verified"] is True
    assert verification["live_public_ledger_anchoring"]["status"] == "LIVE_PUBLIC_LEDGER_ANCHORED"
    assert verification["live_public_ledger_anchoring"]["live_receipt_verified"] is True


def test_level16_rejects_tampered_standard_hash():
    payload = build_ecosystem_evolution_certificate().canonical_dict()
    payload["interoperable_standard"]["standard_hash"] = "tampered"

    verification = verify_ecosystem_evolution_certificate(payload)

    assert verification["verified"] is False
    assert verification["interoperable_standard"]["verified"] is False
    assert verification["ecosystem_hash_valid"] is False


def test_level16_rejects_removed_government_adoption_profile():
    payload = build_ecosystem_evolution_certificate().canonical_dict()
    payload["government_adoption"] = []

    verification = verify_ecosystem_evolution_certificate(payload)

    assert verification["verified"] is False
    assert verification["government_adoption"]["verified"] is False
    assert verification["ecosystem_hash_valid"] is False


def test_live_anchor_publisher_calls_public_ledger_anchor(monkeypatch):
    captured = {}

    def fake_publish_anchor(proof_hash: str, *, profile_name: str | None = None, require_live: bool = False):
        captured["proof_hash"] = proof_hash
        captured["profile_name"] = profile_name
        captured["require_live"] = require_live
        return ChainReceipt(
            tx_hash="0x" + "c" * 64,
            network=str(profile_name),
            status="live",
            chain_id=11155111,
            chain_name="Ethereum Sepolia",
            proof_hash=proof_hash,
            authority="smart_contract",
            source="test",
        )

    monkeypatch.setattr("afritech.ecosystem_evolution.publish_anchor", fake_publish_anchor)

    receipt = publish_live_ecosystem_anchor(profile_name="sepolia", require_live=True)

    assert receipt.status == "live"
    assert captured["profile_name"] == "sepolia"
    assert captured["require_live"] is True
    assert len(captured["proof_hash"]) == 64
