from __future__ import annotations

from afritech.features import registry_payload
from afritech.tools.feature_registry_verifier import verify_registry, verify_registry_payload


def test_verify_registry_accepts_local_derived_registry():
    result = verify_registry()

    assert result["verified"] is True
    assert result["signature_valid"] is True
    assert result["signer_trusted"] is True
    assert result["no_fake_feature_can_exist"] is True
    assert result["no_incomplete_feature_can_appear"] is True
    assert result["no_unverifiable_claim_can_be_exported"] is True
    assert result["no_production_state_can_be_falsely_implied"] is True


def test_verify_registry_rejects_tampered_signature():
    payload = registry_payload()
    payload["signature"] = {**payload["signature"], "value": "00"}

    result = verify_registry_payload(payload)

    assert result["verified"] is False
    assert result["signature_valid"] is False


def test_verify_registry_rejects_untrusted_signer():
    payload = registry_payload()
    payload["signature"] = {**payload["signature"], "signer_id": "UNTRUSTED"}

    result = verify_registry_payload(payload)

    assert result["verified"] is False
    assert result["signature_valid"] is True
    assert result["signer_trusted"] is False
