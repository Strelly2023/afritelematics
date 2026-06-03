"""Tests for the AfriRide controlled pilot evidence CLI."""

from __future__ import annotations

from pathlib import Path

import pytest
from afritech.ci.afriride_controlled_pilot_evidence_bundle_validator import (
    ALL_SCENARIO_IDS,
    validate_bundle,
)
from afritech.ci.afriride_controlled_pilot_execution_receipt_validator import (
    validate_receipt,
)
from afritech.cli.afriride_pilot import (
    build_sample_bundle,
    generate_certificate,
    generate_execution_receipt,
    main,
)


def test_build_sample_bundle_is_validator_compatible(tmp_path: Path) -> None:
    bundle_root = build_sample_bundle(tmp_path / "pilot_evidence_bundle")

    report = validate_bundle(bundle_root)

    assert report.verified is True
    assert report.total_scenarios == 16
    for scenario_id in ALL_SCENARIO_IDS:
        assert (bundle_root / "replay_verification_receipts" / f"{scenario_id}.json").is_file()


def test_generate_receipt_from_synthetic_bundle_but_blocks_certification(tmp_path: Path) -> None:
    bundle_root = build_sample_bundle(tmp_path / "pilot_evidence_bundle")
    receipt_path = generate_execution_receipt(bundle_root, tmp_path / "execution_receipt.json")

    receipt_report = validate_receipt(receipt_path, bundle_root)

    assert receipt_report.verified is True
    with pytest.raises(
        RuntimeError,
        match="not admissible for certification|non-field evidence",
    ):
        generate_certificate(
            bundle_root,
            receipt_path,
            tmp_path / "AFRIRIDE_CONTROLLED_PILOT_CERTIFICATE.json",
        )


def test_cli_main_build_validate_receipt_certify_flow(tmp_path: Path) -> None:
    bundle_root = tmp_path / "bundle"
    receipt_path = tmp_path / "receipt.json"
    certificate_path = tmp_path / "certificate.json"

    assert main(["build-sample-bundle", "--output", str(bundle_root)]) == 0
    assert main(["validate-bundle", "--bundle", str(bundle_root)]) == 0
    assert main(["generate-receipt", "--bundle", str(bundle_root), "--output", str(receipt_path)]) == 0
    assert main(
        [
            "certify",
            "--bundle",
            str(bundle_root),
            "--receipt",
            str(receipt_path),
            "--output",
            str(certificate_path),
        ]
    ) == 1
