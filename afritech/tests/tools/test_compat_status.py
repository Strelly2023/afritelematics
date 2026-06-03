import copy
import json

from afritech.tools import compat_status


def test_compat_status_summary_reports_green_baseline(capsys):
    exit_code = compat_status.main(["status"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Compatibility health: green" in output
    assert "Epoch lifecycle: valid" in output
    assert "Active epochs: 1" in output
    assert "Translators: 0" in output


def test_compat_status_json_contains_epoch_rows(capsys):
    exit_code = compat_status.main(["status", "--format", "json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["health"] == "green"
    assert output["epochs"][0]["epoch"] == "EPOCH-1"
    assert output["epochs"][0]["status"] == "ACTIVE"


def test_compat_status_reports_invalid_lifecycle(monkeypatch):
    epoch_payload = compat_status.load_yaml(compat_status.EPOCH_LIFECYCLE_REGISTRY)
    translator_payload = compat_status.load_yaml(compat_status.REPLAY_TRANSLATOR_REGISTRY)
    broken = copy.deepcopy(epoch_payload)
    del broken["epochs"]["EPOCH-1"]["interface_versions"]["replay"]

    def fake_load_yaml(path):
        if path == compat_status.EPOCH_LIFECYCLE_REGISTRY:
            return broken
        if path == compat_status.REPLAY_TRANSLATOR_REGISTRY:
            return translator_payload
        raise AssertionError(path)

    def fake_validate():
        raise RuntimeError("EPOCH-1 missing interface versions: ['replay']")

    monkeypatch.setattr(compat_status, "load_yaml", fake_load_yaml)
    monkeypatch.setattr(compat_status, "validate", fake_validate)

    status = compat_status.compatibility_status()

    assert status["health"] == "red"
    assert status["epoch_lifecycle"] == "invalid"
    assert "missing interface" in status["validation_error"]
