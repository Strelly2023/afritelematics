from __future__ import annotations

import pytest

from afritech.guards.guard_release_stage import validate as validate_release_stage_guard
from tests.release._helpers import CONFIG_PATH, READINESS_SOURCE, read_json, read_text


pytestmark = [pytest.mark.release, pytest.mark.readiness]


def test_readiness_domains_are_all_passing() -> None:
    config = read_json(CONFIG_PATH)
    readiness = config["readiness"]
    assert set(readiness) == {
        "Engineering",
        "Operations",
        "Governance",
        "Compliance",
        "Commercial",
        "Security",
        "Support",
        "DisasterRecovery",
    }
    assert all(status == "PASS" for status in readiness.values())


def test_readiness_source_has_required_checks_and_authorities() -> None:
    source = read_text(READINESS_SOURCE)
    for phrase in ("requiredChecks", "blockingIssues", "approvalAuthority", "DisasterRecovery"):
        assert phrase in source


def test_release_stage_guard_passes() -> None:
    report = validate_release_stage_guard()
    assert report["status"] == "PASS"
    assert report["release_stage"] == "PUBLIC_PILOT"

