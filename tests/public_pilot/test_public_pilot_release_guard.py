from __future__ import annotations

import json

import pytest

from afriride_system.pilot import public_pilot
from tests.public_pilot._helpers import PUBLIC_PILOT_EXIT_REPORT_PATH, public_pilot_approval_payload


pytestmark = [pytest.mark.public_pilot, pytest.mark.public_pilot_release_guard]


@pytest.fixture(autouse=True)
def _reset_public_pilot_state() -> None:
    public_pilot.load_public_pilot_approval.cache_clear()
    public_pilot.reset_runtime_state()


def _install_approval(monkeypatch: pytest.MonkeyPatch, tmp_path, **overrides) -> None:
    payload = public_pilot_approval_payload(**overrides)
    path = tmp_path / "PUBLIC_PILOT_APPROVAL.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    monkeypatch.setattr(public_pilot, "PUBLIC_PILOT_APPROVAL_PATH", path)
    public_pilot.load_public_pilot_approval.cache_clear()
    public_pilot.reset_runtime_state()


def test_public_pilot_release_guard_reports_not_ready_by_default() -> None:
    report = public_pilot.public_pilot_release_guard()
    assert report["environment"] == "PUBLIC_PILOT"
    assert report["ga_enabled"] is False
    assert report["general_availability_allowed"] is False
    assert report["ready_for_prr"] is False


def test_public_pilot_release_guard_can_become_ready_with_approval(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _install_approval(monkeypatch, tmp_path)
    report = public_pilot.public_pilot_release_guard()
    assert report["ready_for_prr"] is True
    assert report["approval"]["public_pilot_approved"] is True


def test_public_pilot_exit_report_is_not_ready_for_prr() -> None:
    assert "NOT_READY_FOR_PRR" in PUBLIC_PILOT_EXIT_REPORT_PATH.read_text(encoding="utf-8")
