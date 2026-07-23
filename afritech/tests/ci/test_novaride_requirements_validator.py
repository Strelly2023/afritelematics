from pathlib import Path

import yaml

from afritech.ci.novaride_requirements_validator import DEFAULT_CATALOGUE, validate_catalogue


def test_enterprise_catalogue_covers_required_domains_and_has_valid_links() -> None:
    report = validate_catalogue()
    assert report.valid, report.errors
    assert report.requirement_count >= 15
    assert set(report.phases) == set(range(1, 12))


def test_validator_rejects_missing_owner(tmp_path: Path) -> None:
    payload = yaml.safe_load(DEFAULT_CATALOGUE.read_text(encoding="utf-8"))
    payload["requirements"][0]["owner"] = ""
    path = tmp_path / "requirements.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    report = validate_catalogue(path)
    assert not report.valid
    assert any("requires owner" in error for error in report.errors)


def test_validator_rejects_broken_evidence_link(tmp_path: Path) -> None:
    payload = yaml.safe_load(DEFAULT_CATALOGUE.read_text(encoding="utf-8"))
    payload["requirements"][0]["evidence_links"] = ["missing/evidence.json"]
    path = tmp_path / "requirements.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    report = validate_catalogue(path)
    assert not report.valid
    assert any("broken evidence_links" in error for error in report.errors)
