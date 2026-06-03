from __future__ import annotations

from pathlib import Path

import pytest

from afritech.runtime.admission.admission_engine import (
    RuntimeAdmissionEngine,
    RuntimeAdmissionError,
    require_runtime_admission,
)


def test_runtime_admission_accepts_valid_certificate(tmp_path: Path):
    certificate = tmp_path / "runtime_epoch_6.json"
    certificate.write_text("{}")

    decision = RuntimeAdmissionEngine(
        certificate_path=certificate,
        expected_epoch=6,
    ).admit()

    assert decision.admitted is True
    assert decision.reason == "runtime_admitted"
    assert decision.epoch == 6


def test_runtime_admission_rejects_missing_certificate(tmp_path: Path):
    certificate = tmp_path / "missing.json"

    with pytest.raises(RuntimeAdmissionError):
        RuntimeAdmissionEngine(
            certificate_path=certificate,
        ).admit()


def test_runtime_admission_rejects_directory(tmp_path: Path):
    with pytest.raises(RuntimeAdmissionError):
        RuntimeAdmissionEngine(
            certificate_path=tmp_path,
        ).admit()


def test_runtime_admission_rejects_invalid_filename(tmp_path: Path):
    certificate = tmp_path / "certificate.json"
    certificate.write_text("{}")

    with pytest.raises(RuntimeAdmissionError):
        RuntimeAdmissionEngine(
            certificate_path=certificate,
        ).admit()


def test_runtime_admission_rejects_epoch_mismatch(tmp_path: Path):
    certificate = tmp_path / "runtime_epoch_7.json"
    certificate.write_text("{}")

    with pytest.raises(RuntimeAdmissionError):
        RuntimeAdmissionEngine(
            certificate_path=certificate,
            expected_epoch=6,
        ).admit()


def test_require_runtime_admission_helper(tmp_path: Path):
    certificate = tmp_path / "runtime_epoch_9.json"
    certificate.write_text("{}")

    decision = require_runtime_admission(
        certificate_path=certificate,
        expected_epoch=9,
    )

    assert decision.admitted is True
    assert decision.epoch == 9