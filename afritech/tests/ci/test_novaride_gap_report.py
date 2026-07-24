from pathlib import Path

from afritech.ci.novaride_gap_report import build_report, write_reports


def test_gap_report_is_derived_from_all_mandatory_feature_groups(tmp_path: Path) -> None:
    report = build_report()
    assert report["requirement_count"] == 69
    assert report["application_counts"] == {
        "driver": 33,
        "operator": 18,
        "rider": 18,
    }
    assert report["state_counts"] == {
        "NOT_IMPLEMENTED": 13,
        "PARTIALLY_IMPLEMENTED": 56,
    }
    assert report["missing"]["missing-api-bindings"]
    assert report["missing"]["missing-release-evidence"]
    write_reports(tmp_path, report)
    assert (tmp_path / "current-feature-state.json").is_file()
    assert (tmp_path / "current-feature-state.md").is_file()
    assert (tmp_path / "missing-source-bindings.json").is_file()
    assert (tmp_path / "missing-api-bindings.json").is_file()
    assert (tmp_path / "missing-test-bindings.json").is_file()
    assert (tmp_path / "missing-release-evidence.json").is_file()


def test_gap_report_does_not_treat_pending_paths_as_evidence() -> None:
    report = build_report()
    missing_e2e = [
        item
        for item in report["missing"]["missing-test-bindings"]
        if item["field"] == "mobile_e2e_test"
    ]
    # Rider and Driver still use pending mobile E2E paths. Operator rows bind
    # to existing browser E2E coverage and are therefore not reported here.
    assert len(missing_e2e) == 51
