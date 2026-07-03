from __future__ import annotations

import base64
import json
import zlib
from datetime import UTC, datetime

from afritech.core_platform.cross_chain_light_client import (
    LightClientState,
    build_cross_chain_bridge,
    verify_cross_chain_bridge,
)
from afritech.core_platform.onchain_light_verifier import build_light_verifier_source
from afritech.core_platform.privacy_qr import (
    build_privacy_qr_payload,
    decode_privacy_qr_payload,
    encode_privacy_qr_payload,
)
from afritech.core_platform.proof_receipts import build_proof_receipt
from afritech.core_platform.stateless_verifier import verify_stateless_privacy_qr
from afritech.core_platform.zk_receipts import build_zk_receipt, verify_zk_receipt

CURRENT_TEST_TIME = datetime.now(UTC).replace(microsecond=0).isoformat()


def _trust_seal() -> dict[str, object]:
    return {
        "seal_id": "seal-demo-001",
        "seal_hash": "a" * 64,
        "trust_id": "trust-demo-001",
        "packet_hash": "b" * 64,
        "consensus_root": "c" * 64,
        "validator_root": "d" * 64,
        "aggregate_signature": "e" * 128,
        "aggregate_signature_scheme": "bls-threshold",
        "signature_threshold": 2,
        "accepted_validators": ["validator-a", "validator-b"],
        "rejected_validators": [],
        "violations_hash": "f" * 64,
        "cryptographic_consensus": True,
        "total_votes_raw": 2,
        "total_votes_effective": 2,
        "node_health_hash": "1" * 64,
        "node_health_status": "healthy",
        "signer_set": ["0" * 96, "1" * 96],
        "signer_pop_proofs": ["2" * 96, "3" * 96],
    }


def _build_receipt() -> dict[str, object]:
    return build_proof_receipt(
        _trust_seal(),
        issuer="demo-issuer",
        issued_at=CURRENT_TEST_TIME,
    )


def _light_client_state() -> LightClientState:
    return LightClientState(
        chain_id="ETH",
        block_height=12_345_678,
        state_root="4" * 64,
        validator_set_hash="5" * 64,
        block_hash="6" * 64,
        trusted_height=12_345_600,
        timestamp=CURRENT_TEST_TIME,
    )


def test_privacy_qr_receipt_bridge_and_stateless_verification_round_trip() -> None:
    receipt = _build_receipt()
    zk_receipt = build_zk_receipt(
        receipt,
        hidden_fields=["issuer"],
        chain_id="ETH",
        epoch=12,
    )
    assert verify_zk_receipt(zk_receipt, expected_receipt=receipt)["valid"] is True

    state = _light_client_state()
    bridge = build_cross_chain_bridge(
        zk_receipt,
        state,
        receipt_batch=[zk_receipt],
    )
    bridge_verification = verify_cross_chain_bridge(
        bridge,
        expected_commitment=zk_receipt["commitment"],
        expected_light_client_state=state,
    )
    assert bridge_verification["valid"] is True

    qr_payload = build_privacy_qr_payload(
        receipt,
        hidden_fields=["issuer"],
        chain_id="ETH",
        epoch=12,
        bridge=bridge,
    )

    decoded = decode_privacy_qr_payload(qr_payload)
    assert decoded["type"] == "novatrust-zk-qr"
    assert decoded["zk_receipt"]["commitment"] == zk_receipt["commitment"]

    verification = verify_stateless_privacy_qr(
        qr_payload,
        expected_receipt=receipt,
        expected_light_client_state=state,
    )
    assert verification["status"] is True
    assert verification["trust_level"] == "HIGH"
    assert verification["reason"] == "stateless_verified"
    assert verification["zk_receipt"]["commitment"] == zk_receipt["commitment"]
    assert verification["bridge"]["bridge_hash"] == bridge["bridge_hash"]


def test_privacy_qr_rejects_tampering_and_invalid_bridge_state() -> None:
    receipt = _build_receipt()
    zk_receipt = build_zk_receipt(
        receipt,
        hidden_fields=["issuer"],
        chain_id="ETH",
        epoch=12,
    )
    state = _light_client_state()
    bridge = build_cross_chain_bridge(
        zk_receipt,
        state,
        receipt_batch=[zk_receipt],
    )

    tampered_bundle = decode_privacy_qr_payload(
        build_privacy_qr_payload(
            receipt,
            hidden_fields=["issuer"],
            chain_id="ETH",
            epoch=12,
            bridge=bridge,
        )
    )
    tampered_bundle["bridge"]["light_client_state"]["state_root"] = "9" * 64
    tampered_payload = encode_privacy_qr_payload(tampered_bundle)

    verification = verify_stateless_privacy_qr(tampered_payload)
    assert verification["status"] is False
    assert verification["reason"] in {
        "cross_chain_light_client_state_hash_mismatch",
        "cross_chain_light_client_state_mismatch",
    }


def test_privacy_qr_rejects_missing_hash_field() -> None:
    receipt = _build_receipt()
    zk_receipt = build_zk_receipt(
        receipt,
        hidden_fields=["issuer"],
        chain_id="ETH",
        epoch=12,
    )
    state = _light_client_state()
    bridge = build_cross_chain_bridge(
        zk_receipt,
        state,
        receipt_batch=[zk_receipt],
    )

    bundle = decode_privacy_qr_payload(
        build_privacy_qr_payload(
            receipt,
            hidden_fields=["issuer"],
            chain_id="ETH",
            epoch=12,
            bridge=bridge,
        )
    )
    bundle["qr_hash"] = None
    invalid_payload = base64.urlsafe_b64encode(
        zlib.compress(
            json.dumps(bundle, sort_keys=True, separators=(",", ":"), default=str).encode(
                "utf-8"
            ),
            level=9,
        )
    ).decode("utf-8")

    verification = verify_stateless_privacy_qr(invalid_payload)
    assert verification["status"] is False
    assert verification["reason"] == "qr_invalid_hash"


def test_onchain_light_verifier_source_is_available() -> None:
    source = build_light_verifier_source()
    assert "contract NovaTrustLightVerifier" in source
    assert "anchorReceipt" in source
