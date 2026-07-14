from __future__ import annotations

from copy import deepcopy

from afritech.api_catalog.breaking_changes import detect_breaking_changes
from afritech.api_catalog.registry import get_api_catalog


def test_stable_endpoint_removal_is_breaking() -> None:
    spec = get_api_catalog().openapi("novapay")
    current = deepcopy(spec)
    current["paths"].pop("/v1/novapay/payment-intents")
    changes = detect_breaking_changes(spec, current)
    assert any(change.code == "OPERATION_REMOVED" for change in changes)


def test_response_property_removal_and_type_change_are_breaking() -> None:
    previous = get_api_catalog().openapi("novapay")
    current = deepcopy(previous)
    current["components"]["schemas"]["NovaTechEnvelope"]["properties"].pop("evidence")
    current["components"]["schemas"]["NovaTechEnvelope"]["properties"]["data"]["type"] = "string"
    changes = detect_breaking_changes(previous, current)
    assert {change.code for change in changes} >= {"PROPERTY_REMOVED", "PROPERTY_TYPE_CHANGED"}


def test_new_required_field_is_breaking() -> None:
    previous = get_api_catalog().openapi("novapay")
    current = deepcopy(previous)
    current["components"]["schemas"]["NovaTechEnvelope"]["required"].append("new_required_field")
    changes = detect_breaking_changes(previous, current)
    assert any(change.code == "REQUIRED_PROPERTY_ADDED" for change in changes)
