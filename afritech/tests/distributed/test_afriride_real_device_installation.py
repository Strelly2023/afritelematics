from __future__ import annotations

from pathlib import Path

from afritech.ci.afriride_real_device_installation_validator import validate


def test_real_device_installation_validator_passes():
    assert validate() is True


def test_real_device_runbook_preserves_live_hold():
    text = Path("docs/pilot/AFRIRIDE_REAL_DEVICE_INSTALLATION_PATH.md").read_text(
        encoding="utf-8"
    )

    assert "live_pilot_authorized = false" in text
    assert "production = false" in text
    assert "Public production release is not authorized" in text


def test_real_device_runbook_has_android_and_ios_boundaries():
    text = Path("docs/pilot/AFRIRIDE_REAL_DEVICE_INSTALLATION_PATH.md").read_text(
        encoding="utf-8"
    )

    assert "flutter build apk --release" in text
    assert "adb install -r" in text
    assert "iPhone testing is `prepared_not_available`" in text


def test_real_device_runbook_requires_evidence_and_stop_conditions():
    text = Path("docs/pilot/AFRIRIDE_REAL_DEVICE_INSTALLATION_PATH.md").read_text(
        encoding="utf-8"
    )

    assert "signed_event_log.jsonl" in text
    assert "replay_result.json" in text
    assert "Stop Conditions" in text
    assert "operator cannot observe" in text
