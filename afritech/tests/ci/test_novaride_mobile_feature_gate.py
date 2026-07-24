from __future__ import annotations

import json
from pathlib import Path

import yaml

from afritech.ci.novaride_mobile_feature_gate import (
    DEFAULT_MATRICES,
    MANDATORY_GATES,
    evaluate,
)


def test_addendum_matrices_cover_all_feature_groups_and_fail_closed() -> None:
    report = evaluate()
    assert report.requirement_count == 69
    assert report.decision == "NO_GO"
    assert set(report.gates) == set(MANDATORY_GATES)
    assert report.gates["RIDER_FEATURE_COMPLETENESS"] == "FAIL"
    assert report.gates["DRIVER_FEATURE_COMPLETENESS"] == "FAIL"
    assert report.gates["OPERATOR_FEATURE_COMPLETENESS"] == "FAIL"
    assert not report.errors


def test_untrusted_certification_cannot_override_incomplete_features(tmp_path: Path) -> None:
    baseline = evaluate()
    certification = tmp_path / "certification.json"
    certification.write_text(
        json.dumps(
            {
                "tested_commit": baseline.tested_commit,
                "gates": {gate: "PASS" for gate in MANDATORY_GATES},
            }
        ),
        encoding="utf-8",
    )
    report = evaluate(certification=certification)
    assert report.decision == "NO_GO"
    assert report.gates["RIDER_FEATURE_COMPLETENESS"] == "FAIL"
    assert report.gates["DRIVER_FEATURE_COMPLETENESS"] == "FAIL"
    assert report.gates["OPERATOR_FEATURE_COMPLETENESS"] == "FAIL"


def test_verified_requires_objective_existing_evidence(tmp_path: Path) -> None:
    payload = yaml.safe_load(DEFAULT_MATRICES[0].read_text(encoding="utf-8"))
    payload["requirements"] = [payload["requirements"][0]]
    payload["requirements"][0]["state"] = "VERIFIED"
    payload["requirements"][0]["release_commit"] = "0" * 40
    matrix = tmp_path / "matrix.yaml"
    matrix.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    report = evaluate(paths=(matrix,))
    assert report.decision == "NO_GO"
    assert any("missing mobile_e2e_test" in error for error in report.errors)


def test_binary_equality_gate_uses_content_hash(tmp_path: Path) -> None:
    tested = tmp_path / "tested.aab"
    release = tmp_path / "release.aab"
    tested.write_bytes(b"same")
    release.write_bytes(b"same")
    report = evaluate(tested_binary=tested, release_binary=release)
    assert report.gates["TESTED_BINARY_EQUALS_RELEASE_BINARY"] == "PASS"
    release.write_bytes(b"different")
    report = evaluate(tested_binary=tested, release_binary=release)
    assert report.gates["TESTED_BINARY_EQUALS_RELEASE_BINARY"] == "FAIL"
