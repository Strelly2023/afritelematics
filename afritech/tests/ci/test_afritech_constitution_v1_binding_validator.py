from __future__ import annotations

import yaml

from afritech.ci.afritech_constitution_v1_binding_validator import (
    ADR,
    BINDING,
    RULE,
    validate,
)


def load_yaml(path):
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_constitution_v1_binding_validator_passes():
    validate()


def test_constitution_v1_binding_is_not_runtime_authoritative():
    adr = load_yaml(ADR)["adr"]
    assert adr["constitutional_boundary"]["runtime_authoritative"] is False
    assert adr["constitutional_boundary"]["silent_runtime_promotion_forbidden"] is True

    binding = load_yaml(BINDING)
    for entry in binding["bindings"]:
        assert entry["runtime_authoritative"] is False


def test_constitution_v1_binding_targets_resolve():
    rule = load_yaml(RULE)
    binding = load_yaml(BINDING)

    assert rule["id"] == "RULE-019"
    assert binding["id"] == "BIND-019"
    assert {entry["id"] for entry in binding["bindings"]} == {
        "BIND-019-1",
        "BIND-019-2",
        "BIND-019-3",
        "BIND-019-4",
    }
