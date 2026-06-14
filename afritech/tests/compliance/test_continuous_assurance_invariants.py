from __future__ import annotations

from pathlib import Path

import pytest

from afritech.compliance.continuous_assurance import (
    run_continuous_assurance_cycle,
)
from afritech.compliance.continuous_assurance_invariants import (
    ContinuousAssuranceInvariantError,
    evaluate_continuous_assurance_invariants,
    validate_continuous_assurance_invariants,
)


def _make_evidence_files(tmp_path: Path, names: tuple[str, ...] = ("crypto.pdf", "pentest.pdf", "provider.txt")) -> list[Path]:
    paths: list[Path] = []
    for index, name in enumerate(names, start=1):
        path = tmp_path / name
        path.write_text(f"artifact-{index}:{name}", encoding="utf-8")
        paths.append(path)
    return paths


@pytest.mark.django_db
def test_invariants_accept_replay_safe_package(tmp_path: Path) -> None:
    paths = _make_evidence_files(tmp_path)
    package = run_continuous_assurance_cycle(evidence_items=paths, payment_reference="invariants.replay.001")

    report = validate_continuous_assurance_invariants(package)

    assert report.verified is True
    assert report.violations == ()


@pytest.mark.django_db
def test_same_evidence_set_produces_same_package_hash(tmp_path: Path) -> None:
    paths = _make_evidence_files(tmp_path)
    reference = run_continuous_assurance_cycle(
        evidence_items=paths,
        payment_reference="invariants.same.001",
    )
    candidate = run_continuous_assurance_cycle(
        evidence_items=list(reversed(paths)),
        payment_reference="invariants.same.001",
    )

    report = evaluate_continuous_assurance_invariants(candidate, reference_package=reference)

    assert report.verified is True
    assert reference.package_hash == candidate.package_hash


@pytest.mark.django_db
def test_evidence_mutation_changes_hash(tmp_path: Path) -> None:
    paths = _make_evidence_files(tmp_path)
    reference = run_continuous_assurance_cycle(
        evidence_items=paths,
        payment_reference="invariants.mutation.001",
    )

    mutated_path = paths[0]
    mutated_path.write_text("artifact-mutated", encoding="utf-8")
    candidate = run_continuous_assurance_cycle(
        evidence_items=paths,
        payment_reference="invariants.mutation.001",
    )

    report = evaluate_continuous_assurance_invariants(candidate, reference_package=reference)

    assert report.verified is True
    assert reference.package_hash != candidate.package_hash


@pytest.mark.django_db
def test_dashboard_cannot_mutate_evidence(tmp_path: Path) -> None:
    paths = _make_evidence_files(tmp_path)
    package = run_continuous_assurance_cycle(evidence_items=paths, payment_reference="invariants.dashboard.001")

    package.dashboard["external_evidence"][0]["sha256_hash"] = "f" * 64

    report = evaluate_continuous_assurance_invariants(package)

    assert report.verified is False
    assert any(check.invariant_id == "IA-004" for check in report.violations)


@pytest.mark.django_db
def test_package_is_evidence_only_and_has_authority_boundary(tmp_path: Path) -> None:
    paths = _make_evidence_files(tmp_path)
    package = run_continuous_assurance_cycle(evidence_items=paths, payment_reference="invariants.boundary.001")

    report = validate_continuous_assurance_invariants(package)

    assert package.authority_boundary == "continuous_assurance_evidence_only"
    assert package.dashboard["authority_boundary"] == "dashboard_reads_external_evidence_and_monitoring_only"
    assert any(check.invariant_id == "IA-005" for check in report.checks)
    assert any(check.invariant_id == "IA-008" for check in report.checks)


@pytest.mark.django_db
def test_external_evidence_is_never_automatically_trusted(tmp_path: Path) -> None:
    paths = _make_evidence_files(tmp_path)
    package = run_continuous_assurance_cycle(evidence_items=paths, payment_reference="invariants.trust.001")

    report = validate_continuous_assurance_invariants(package)

    assert any(check.invariant_id == "IA-006" for check in report.checks)
    assert package.dashboard["evidence_controls"]["outside_repository_collection"] is True
    assert all(item["collected_from"] == "outside_repository" for item in package.canonical_dict()["external_evidence"])


@pytest.mark.django_db
def test_missing_evidence_fails_visibly() -> None:
    package = run_continuous_assurance_cycle(evidence_items=[], payment_reference="invariants.empty.001")

    with pytest.raises(ContinuousAssuranceInvariantError, match="IA-007"):
        validate_continuous_assurance_invariants(package)


@pytest.mark.django_db
def test_package_schema_is_stable_and_replay_is_deterministic(tmp_path: Path) -> None:
    paths = _make_evidence_files(tmp_path)
    first = run_continuous_assurance_cycle(evidence_items=paths, payment_reference="invariants.schema.001")
    second = run_continuous_assurance_cycle(evidence_items=paths, payment_reference="invariants.schema.001")

    report = evaluate_continuous_assurance_invariants(second, reference_package=first)

    assert report.verified is True
    assert first.package_hash == second.package_hash
    assert first.canonical_dict()["schema"] == "afritech.continuous_assurance_package.v1"
