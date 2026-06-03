from afritech.ci.explain_execution_api_validator import validate
from afritech.explainability.execution_explainer import explain_execution_payload


def test_explain_execution_api_validator_passes():
    validate()


def test_explain_execution_payload_is_display_only():
    payload = {
        "receipt": {
            "receipt_id": "abc123",
            "result": "SUCCESS",
            "execution_hash": "xyz789",
            "governance_traceability": [
                {"type": "ADR", "id": "ADR-0016"},
                {"type": "RULE", "id": "RULE-016-4"},
            ],
        }
    }

    explanation = explain_execution_payload("abc123", payload)

    assert explanation["execution_id"] == "abc123"
    assert explanation["receipt"]["receipt_id"] == "abc123"
    assert explanation["governance"][0]["id"] == "ADR-0016"
    assert explanation["governance"][0]["projection_status"] == "DOCUMENTARY"
    assert explanation["authority"] == {
        "status": "READ_ONLY_EXPLANATION",
        "runtime_authority": False,
        "enforcement_authority": False,
        "validation_authority": False,
        "projection_display_only": True,
    }
    assert "authority remains in governance YAML" in explanation["explanation"]
