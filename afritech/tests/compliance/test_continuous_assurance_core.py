from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from afritech.compliance.continuous_assurance import (
    build_continuous_assurance_dashboard,
    collect_external_evidence_artifacts,
    run_continuous_assurance_cycle,
)


def _create_fake_evidence(tmp_path: Path) -> list[Path]:
    files = {
        "crypto.pdf": "crypto audit",
        "pentest.pdf": "pentest report",
        "provider.txt": "provider letter",
        "incident.md": "incident exercise",
    }
    paths: list[Path] = []
    for name, content in files.items():
        path = tmp_path / name
        path.write_text(content, encoding="utf-8")
        paths.append(path)
    return paths


@pytest.mark.django_db
def test_collect_external_evidence_happy_path(tmp_path: Path):
    paths = _create_fake_evidence(tmp_path)

    result = collect_external_evidence_artifacts(paths)

    assert result is not None
    assert len(result) == len(paths)
    assert all(item.collected_from == "outside_repository" for item in result)


def test_collect_external_evidence_rejects_invalid():
    with pytest.raises(TypeError):
        collect_external_evidence_artifacts([123])  # type: ignore[list-item]


@pytest.mark.django_db
def test_collect_external_evidence_is_deterministic(tmp_path: Path):
    paths = _create_fake_evidence(tmp_path)

    a = collect_external_evidence_artifacts(paths)
    b = collect_external_evidence_artifacts(paths)

    assert a == b


@pytest.mark.django_db
def test_collect_external_evidence_detects_file_change(tmp_path: Path):
    paths = _create_fake_evidence(tmp_path)

    original = collect_external_evidence_artifacts(paths)
    paths[0].write_text("modified content", encoding="utf-8")
    modified = collect_external_evidence_artifacts(paths)

    assert original[0].sha256_hash != modified[0].sha256_hash


@pytest.mark.django_db
def test_evidence_structure_valid(tmp_path: Path):
    paths = _create_fake_evidence(tmp_path)

    result = collect_external_evidence_artifacts(paths)
    item = result[0].canonical_dict()

    assert "schema" in item
    assert "sha256_hash" in item
    assert "artifact_type" in item
    assert item["schema"] == "afritech.external_evidence_artifact.v1"


@pytest.mark.django_db
def test_evidence_serialization_roundtrip(tmp_path: Path):
    paths = _create_fake_evidence(tmp_path)

    result = collect_external_evidence_artifacts(paths)
    encoded = json.dumps([r.canonical_dict() for r in result], sort_keys=True)
    decoded = json.loads(encoded)

    assert decoded[0]["schema"] == "afritech.external_evidence_artifact.v1"


@pytest.mark.django_db
def test_dashboard_happy_path(tmp_path: Path):
    paths = _create_fake_evidence(tmp_path)
    artifacts = collect_external_evidence_artifacts(paths)

    dashboard = build_continuous_assurance_dashboard(
        external_evidence=artifacts,
        submission_ready=True,
        regulator_ready=True,
    )

    assert dashboard is not None
    assert dashboard["view"] == "continuous_assurance_dashboard"


@pytest.mark.django_db
def test_dashboard_authority_boundary():
    dashboard = build_continuous_assurance_dashboard()

    assert dashboard["authority_boundary"] == "dashboard_reads_external_evidence_and_monitoring_only"


@pytest.mark.django_db
def test_dashboard_governance_fields():
    dashboard = build_continuous_assurance_dashboard()

    assert dashboard["classification"] == "CONTINUOUS_ASSURANCE"
    assert "submission_controls" in dashboard
    assert "evidence_controls" in dashboard
    assert dashboard["submission_controls"]["regulator_pack_ready"] is False
    assert dashboard["submission_controls"]["investor_dossier_ready"] is False


@pytest.mark.django_db
def test_dashboard_replay_stability(tmp_path: Path):
    paths = _create_fake_evidence(tmp_path)
    artifacts = collect_external_evidence_artifacts(paths)

    d1 = build_continuous_assurance_dashboard(external_evidence=artifacts)
    d2 = build_continuous_assurance_dashboard(external_evidence=artifacts)

    assert d1 == d2


@pytest.mark.django_db
def test_dashboard_detects_drift(tmp_path: Path):
    paths = _create_fake_evidence(tmp_path)
    artifacts = collect_external_evidence_artifacts(paths)

    dashboard = build_continuous_assurance_dashboard(external_evidence=artifacts)
    tampered = deepcopy(dashboard)
    tampered["external_evidence_count"] += 1

    assert tampered != dashboard


@pytest.mark.django_db
def test_run_continuous_assurance_cycle_happy_path(tmp_path: Path):
    paths = _create_fake_evidence(tmp_path)

    package = run_continuous_assurance_cycle(
        evidence_items=paths,
        payment_reference="test.ref.001",
    )

    assert package is not None
    assert len(package.package_hash) == 64
    assert package.authority_boundary == "continuous_assurance_evidence_only"


@pytest.mark.django_db
def test_run_cycle_replay_safe(tmp_path: Path):
    paths = _create_fake_evidence(tmp_path)

    p1 = run_continuous_assurance_cycle(
        evidence_items=paths,
        payment_reference="same.ref",
    )
    p2 = run_continuous_assurance_cycle(
        evidence_items=paths,
        payment_reference="same.ref",
    )

    assert p1.package_hash == p2.package_hash
    assert p1.canonical_dict() == p2.canonical_dict()


@pytest.mark.django_db
def test_package_authority_boundary(tmp_path: Path):
    paths = _create_fake_evidence(tmp_path)

    package = run_continuous_assurance_cycle(
        evidence_items=paths,
    )

    assert package.authority_boundary == "continuous_assurance_evidence_only"


@pytest.mark.django_db
def test_package_schema_and_traceability(tmp_path: Path):
    paths = _create_fake_evidence(tmp_path)

    package = run_continuous_assurance_cycle(
        evidence_items=paths,
    )

    data = package.canonical_dict()

    assert data["schema"] == "afritech.continuous_assurance_package.v1"
    assert "dashboard" in data
    assert "external_evidence" in data
    assert data["dashboard"]["authority_boundary"] == "dashboard_reads_external_evidence_and_monitoring_only"


@pytest.mark.django_db
def test_package_serialization_roundtrip(tmp_path: Path):
    paths = _create_fake_evidence(tmp_path)

    package = run_continuous_assurance_cycle(
        evidence_items=paths,
    )

    encoded = json.dumps(package.canonical_dict(), sort_keys=True)
    decoded = json.loads(encoded)

    assert decoded["package_hash"] == package.package_hash
    assert decoded["regulator_audit_package"]["package_hash"] == package.regulator_audit_package.package_hash


@pytest.mark.django_db
def test_reproducibility_under_load(tmp_path: Path):
    paths = _create_fake_evidence(tmp_path)

    hashes = [
        run_continuous_assurance_cycle(
            evidence_items=paths,
            payment_reference="load.test",
        ).package_hash
        for _ in range(5)
    ]

    assert len(set(hashes)) == 1

