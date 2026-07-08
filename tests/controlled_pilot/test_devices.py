from __future__ import annotations

import pytest

from tests.controlled_pilot._helpers import read_json


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_device_control]


def test_controlled_pilot_devices_are_trusted_and_bound() -> None:
    users = set(read_json("pilot/controlled_pilot/approved_users.json")["approved_users"])
    devices = read_json("pilot/controlled_pilot/approved_devices.json")["approved_devices"]

    assert len(users) == 57
    assert len(devices) == 40

    owners = set()
    for device in devices:
        assert device["device_id"]
        assert device["owner_id"]
        assert device["owner_id"] in users
        assert device["trusted"] is True
        assert device["bound"] is True
        owners.add(device["owner_id"])

    assert len(owners) == 40
    assert len(users) > len(devices)

