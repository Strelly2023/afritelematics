from __future__ import annotations

from pathlib import Path

import pytest

from afritech.ci.certificate_validator import (
    CertificateValidationError,
    require_valid_certificate,
    validate_certificate,
)


def write_certificate(path: Path, *, epoch: int = 6, status: str = "valid") -> None:
    path.write_text(
        (
            "{\n"
            '  "certificate_type": "runtime_certificate",\n'
            f'  "epoch": {epoch},\n'
            f'  "status": "{status}"\n'
            "}\n"
        ),
        encoding="utf-8",
    )


def test_validate_certificate_accepts_valid_runtime_certificate(tmp_path: Path):
    certificate = tmp_path / "runtime_epoch_6.json"
    write_certificate(certificate, epoch=6)

    result = validate_certificate(certificate, expected_epoch=6)

    assert result.valid is True
    assert result.reason == "certificate_valid"
    assert result.epoch == 6


def test_validate_certificate_rejects_missing_file(tmp_path: Path):
    with pytest.raises(CertificateValidationError):
        validate_certificate(tmp_path / "runtime_epoch_6.json")


def test_validate_certificate_rejects_directory(tmp_path: Path):
    with pytest.raises(CertificateValidationError):
        validate_certificate(tmp_path)


def test_validate_certificate_rejects_bad_filename(tmp_path: Path):
    certificate = tmp_path / "certificate.json"
    write_certificate(certificate, epoch=6)

    with pytest.raises(CertificateValidationError):
        validate_certificate(certificate)


def test_validate_certificate_rejects_invalid_json(tmp_path: Path):
    certificate = tmp_path / "runtime_epoch_6.json"
    certificate.write_text("{not-json", encoding="utf-8")

    with pytest.raises(CertificateValidationError):
        validate_certificate(certificate)


def test_validate_certificate_rejects_missing_required_fields(tmp_path: Path):
    certificate = tmp_path / "runtime_epoch_6.json"
    certificate.write_text('{"epoch": 6}', encoding="utf-8")

    with pytest.raises(CertificateValidationError):
        validate_certificate(certificate)


def test_validate_certificate_rejects_wrong_certificate_type(tmp_path: Path):
    certificate = tmp_path / "runtime_epoch_6.json"
    certificate.write_text(
        (
            "{\n"
            '  "certificate_type": "other",\n'
            '  "epoch": 6,\n'
            '  "status": "valid"\n'
            "}\n"
        ),
        encoding="utf-8",
    )

    with pytest.raises(CertificateValidationError):
        validate_certificate(certificate)


def test_validate_certificate_rejects_invalid_status(tmp_path: Path):
    certificate = tmp_path / "runtime_epoch_6.json"
    write_certificate(certificate, epoch=6, status="invalid")

    with pytest.raises(CertificateValidationError):
        validate_certificate(certificate)


def test_validate_certificate_rejects_epoch_mismatch_with_filename(tmp_path: Path):
    certificate = tmp_path / "runtime_epoch_7.json"
    write_certificate(certificate, epoch=6)

    with pytest.raises(CertificateValidationError):
        validate_certificate(certificate)


def test_validate_certificate_rejects_expected_epoch_mismatch(tmp_path: Path):
    certificate = tmp_path / "runtime_epoch_6.json"
    write_certificate(certificate, epoch=6)

    with pytest.raises(CertificateValidationError):
        validate_certificate(certificate, expected_epoch=7)


def test_require_valid_certificate_helper(tmp_path: Path):
    certificate = tmp_path / "runtime_epoch_9.json"
    write_certificate(certificate, epoch=9)

    result = require_valid_certificate(certificate, expected_epoch=9)

    assert result.valid is True
    assert result.epoch == 9