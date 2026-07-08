from __future__ import annotations

import pytest

from afritech.guards.guard_ga_enablement import validate as validate_ga_guard
from tests.release._helpers import CONFIG_PATH, GA_GUARD_SOURCE, read_json, read_text


pytestmark = [pytest.mark.release, pytest.mark.governance]


def test_ga_remains_disabled_before_prr() -> None:
    config = read_json(CONFIG_PATH)
    assert config["gaEnabled"] is False
    assert config["generalAvailabilityAllowed"] is False


def test_ga_guard_blocks_unapproved_enablement() -> None:
    report = validate_ga_guard()
    assert report["status"] == "PASS"
    assert report["ga_enabled"] is False
    assert report["prr_approved"] is False


def test_ga_guard_source_mentions_prr_boundary() -> None:
    source = read_text(GA_GUARD_SOURCE)
    for phrase in ("ga cannot be enabled before prr approval", "generalAvailabilityAllowed", "ga_enabled"):
        assert phrase in source

