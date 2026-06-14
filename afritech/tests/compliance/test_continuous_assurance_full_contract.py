from __future__ import annotations

import json
import random
from copy import deepcopy
from pathlib import Path

import pytest

from afritech.compliance.continuous_assurance import (
    build_continuous_assurance_dashboard,
    collect_external_evidence_artifacts,
    run_continuous_assurance_cycle,
)


def _make_files(tmp_path: Path, n: int = 3) -> list[Path]:
    paths: list[Path] = []
    for i in range(n):
        path = tmp_path / f"file_{i}.txt"
        path.write_text(f"content-{i}", encoding="utf-8")
        paths.append(path)
    return paths


@pytest.mark.django_db
def test_happy_path(tmp_path: Path):
    paths = _make_files(tmp_path)

    result = run_continuous_assurance_cycle(evidence_items=paths)

    assert result is not None
    assert len(result.package_hash) == 64
    assert result.authority_boundary == "continuous_assurance_evidence_only"


def test_invalid_input():
    with pytest.raises(Exception):
        collect_external_evidence_artifacts([123])  # type: ignore[list-item]


@pytest.mark.django_db
def test_determinism(tmp_path: Path):
    paths = _make_files(tmp_path)

    a = run_continuous_assurance_cycle(evidence_items=paths)
    b = run_continuous_assurance_cycle(evidence_items=paths)

    assert a.package_hash == b.package_hash


@pytest.mark.django_db
def test_replay_stability(tmp_path: Path):
    paths = _make_files(tmp_path)

    first = run_continuous_assurance_cycle(
        evidence_items=paths,
        payment_reference="same.ref",
    )
    second = run_continuous_assurance_cycle(
        evidence_items=paths,
        payment_reference="same.ref",
    )

    assert first.package_hash == second.package_hash
    assert first.canonical_dict() == second.canonical_dict()


@pytest.mark.django_db
def test_tampering_detection(tmp_path: Path):
    paths = _make_files(tmp_path)

    package = run_continuous_assurance_cycle(evidence_items=paths)

    tampered = deepcopy(package.canonical_dict())
    tampered["package_hash"] = "f" * 64

    assert tampered != package.canonical_dict()


@pytest.mark.django_db
def test_serialization_roundtrip(tmp_path: Path):
    paths = _make_files(tmp_path)

    package = run_continuous_assurance_cycle(evidence_items=paths)

    encoded = json.dumps(package.canonical_dict(), sort_keys=True)
    decoded = json.loads(encoded)

    assert decoded["package_hash"] == package.package_hash


@pytest.mark.django_db
def test_schema_integrity(tmp_path: Path):
    paths = _make_files(tmp_path)

    package = run_continuous_assurance_cycle(evidence_items=paths)

    data = package.canonical_dict()

    assert data["schema"] == "afritech.continuous_assurance_package.v1"
    assert "dashboard" in data
    assert "external_evidence" in data
    assert "regulator_audit_package" in data
    assert "investor_dossier" in data
    assert "provider_certification" in data


@pytest.mark.django_db
def test_authority_boundary(tmp_path: Path):
    paths = _make_files(tmp_path)

    package = run_continuous_assurance_cycle(evidence_items=paths)

    assert package.authority_boundary == "continuous_assurance_evidence_only"
    assert package.dashboard["authority_boundary"] == "dashboard_reads_external_evidence_and_monitoring_only"


@pytest.mark.django_db
def test_governance_constraints():
    dashboard = build_continuous_assurance_dashboard()

    assert dashboard["classification"] == "CONTINUOUS_ASSURANCE"
    assert "submission_controls" in dashboard
    assert "evidence_controls" in dashboard
    assert dashboard["authority_boundary"] == "dashboard_reads_external_evidence_and_monitoring_only"


@pytest.mark.django_db
def test_backward_compatibility(tmp_path: Path):
    paths = _make_files(tmp_path)

    package = run_continuous_assurance_cycle(evidence_items=paths)

    data = package.canonical_dict()
    modified = deepcopy(data)
    modified.pop("authority_boundary", None)

    assert "package_hash" in modified
    assert modified["schema"] == "afritech.continuous_assurance_package.v1"


@pytest.mark.django_db
def test_detects_drift(tmp_path: Path):
    paths = _make_files(tmp_path)

    original = run_continuous_assurance_cycle(evidence_items=paths)

    tampered = deepcopy(original.canonical_dict())
    tampered["dashboard"]["external_evidence_count"] += 1

    assert tampered != original.canonical_dict()


@pytest.mark.django_db
def test_reproducibility_under_load(tmp_path: Path):
    paths = _make_files(tmp_path)

    hashes = [
        run_continuous_assurance_cycle(
            evidence_items=paths,
            payment_reference="load.test",
        ).package_hash
        for _ in range(10)
    ]

    assert len(set(hashes)) == 1


@pytest.mark.django_db
def test_random_corruption(tmp_path: Path):
    paths = _make_files(tmp_path)

    baseline = collect_external_evidence_artifacts(paths)

    random.choice(paths).write_text("CORRUPTED", encoding="utf-8")

    corrupted = collect_external_evidence_artifacts(paths)

    assert any(a.sha256_hash != b.sha256_hash for a, b in zip(baseline, corrupted))


@pytest.mark.django_db
def test_randomized_input_order(tmp_path: Path):
    paths = _make_files(tmp_path)

    base = run_continuous_assurance_cycle(evidence_items=paths)

    random.shuffle(paths)

    shuffled = run_continuous_assurance_cycle(evidence_items=paths)

    assert base.package_hash == shuffled.package_hash


@pytest.mark.django_db
def test_file_processing(tmp_path: Path):
    paths = _make_files(tmp_path)

    artifacts = collect_external_evidence_artifacts(paths)

    assert len(artifacts) == len(paths)
    assert all(len(a.sha256_hash) == 64 for a in artifacts)
    assert all(a.collected_from == "outside_repository" for a in artifacts)

