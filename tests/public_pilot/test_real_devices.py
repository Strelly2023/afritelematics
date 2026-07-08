from __future__ import annotations

import pytest

from tests.public_pilot._helpers import PUBLIC_PILOT_DEVICE_BINDINGS, read_json, read_text


pytestmark = [pytest.mark.public_pilot, pytest.mark.approved_devices_only]


def test_public_pilot_device_registry_has_forty_trusted_bindings() -> None:
    devices = read_json("pilot/public_pilot/approved_devices.json")
    assert len(devices) == 40
    assert len(PUBLIC_PILOT_DEVICE_BINDINGS) == 40
    for device in devices:
        assert device["device_id"] in PUBLIC_PILOT_DEVICE_BINDINGS
        assert device["owner_id"] == PUBLIC_PILOT_DEVICE_BINDINGS[device["device_id"]]
        assert device["trusted"] is True
        assert device["bound"] is True


def test_public_pilot_device_docs_describe_binding_and_trust() -> None:
    text = read_text("docs/public_pilot/PUBLIC_PILOT_USERS.md")
    assert "device trust" in text.lower()
    assert "approved devices only" in text.lower()
