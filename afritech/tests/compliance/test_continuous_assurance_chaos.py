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
from afritech.runtime_monitoring.anomaly_classifier import classify_anomaly
from afritech.runtime_monitoring.anomaly_context_builder import build_anomaly_context
from afritech.runtime_monitoring.anomaly_detector import detect_anomalies
from afritech.runtime_monitoring.monitor import collect_runtime_events


def _create_files(tmp_path: Path) -> list[Path]:
    files = ["a.txt", "b.txt", "c.txt"]
    paths: list[Path] = []
    for name in files:
        path = tmp_path / name
        path.write_text(f"content-{name}", encoding="utf-8")
        paths.append(path)
    return paths


@pytest.mark.django_db
def test_random_file_corruption_detection(tmp_path: Path):
    paths = _create_files(tmp_path)

    original = collect_external_evidence_artifacts(paths)
    victim = random.choice(paths)
    victim.write_text("CORRUPTED", encoding="utf-8")
    corrupted = collect_external_evidence_artifacts(paths)

    diffs = [a.sha256_hash != b.sha256_hash for a, b in zip(original, corrupted)]

    assert any(diffs)


@pytest.mark.django_db
def test_random_field_deletion_on_dashboard(tmp_path: Path):
    dashboard = build_continuous_assurance_dashboard(
        external_evidence=collect_external_evidence_artifacts(_create_files(tmp_path)),
        submission_ready=True,
        regulator_ready=True,
    )

    tampered = deepcopy(dashboard)
    key = random.choice(list(tampered.keys()))
    tampered.pop(key)

    assert tampered != dashboard


@pytest.mark.django_db
def test_malformed_inputs_do_not_crash():
    bad_inputs = [None, 123, {"bad": "structure"}, [object()]]

    for inp in bad_inputs:
        try:
            collect_external_evidence_artifacts(inp)  # type: ignore[arg-type]
        except Exception:
            pass


@pytest.mark.django_db
def test_partial_evidence_loss(tmp_path: Path):
    paths = _create_files(tmp_path)
    paths[1].unlink()

    with pytest.raises(Exception):
        collect_external_evidence_artifacts(paths)


@pytest.mark.django_db
def test_invariant_hash_stability_under_repetition(tmp_path: Path):
    paths = _create_files(tmp_path)

    hashes = [
        run_continuous_assurance_cycle(
            evidence_items=paths,
            payment_reference="chaos.test",
        ).package_hash
        for _ in range(10)
    ]

    assert len(set(hashes)) == 1


@pytest.mark.django_db
def test_evidence_order_does_not_affect_hash(tmp_path: Path):
    paths = _create_files(tmp_path)

    p1 = run_continuous_assurance_cycle(evidence_items=paths)
    p2 = run_continuous_assurance_cycle(evidence_items=list(reversed(paths)))

    assert p1.package_hash == p2.package_hash


@pytest.mark.django_db
def test_duplicate_evidence_entries(tmp_path: Path):
    paths = _create_files(tmp_path)
    duplicated = paths + [paths[0]]

    result = collect_external_evidence_artifacts(duplicated)
    hashes = [r.sha256_hash for r in result]

    assert len(hashes) != len(set(hashes))


@pytest.mark.django_db
def test_serialization_does_not_change_meaning(tmp_path: Path):
    paths = _create_files(tmp_path)

    package = run_continuous_assurance_cycle(evidence_items=paths)
    dumped = json.dumps(package.canonical_dict(), sort_keys=True)
    loaded = json.loads(dumped)

    assert loaded["package_hash"] == package.package_hash


@pytest.mark.django_db
def test_large_number_of_files(tmp_path: Path):
    paths = []

    for i in range(50):
        path = tmp_path / f"{i}.txt"
        path.write_text(f"file-{i}", encoding="utf-8")
        paths.append(path)

    package = run_continuous_assurance_cycle(evidence_items=paths)

    assert len(package.external_evidence) == 50


@pytest.mark.django_db
def test_empty_evidence_input():
    package = run_continuous_assurance_cycle(evidence_items=[])

    assert package.dashboard["external_evidence_count"] == 0


@pytest.mark.django_db
def test_randomized_runs_are_stable(tmp_path: Path):
    paths = _create_files(tmp_path)

    hashes = set()

    for _ in range(10):
        random.shuffle(paths)
        pkg = run_continuous_assurance_cycle(evidence_items=paths)
        hashes.add(pkg.package_hash)

    assert len(hashes) == 1


@pytest.mark.django_db
def test_live_anomaly_ai_detection_layer_is_trace_linked():
    events = collect_runtime_events(
        validation_failures=("device_clock_skew",),
        contract_mismatches=("receipt mismatch",),
        replay_mismatches=("replay delta",),
        timing_violations=("time skew",),
    )
    anomalies = detect_anomalies(events)
    classified = [classify_anomaly(anomaly) for anomaly in anomalies]
    contexts = [
        build_anomaly_context(
            anomaly,
            timestamp="2026-06-14T00:00:00Z",
            event_trace=("TraceStart", "TraceEnd"),
            current_receipt="v1",
            expected_receipt="v2",
            affected_files=("afritech/compliance/continuous_assurance.py",),
            validator_failures=("continuous_assurance_validator",),
        )
        for anomaly in classified
    ]

    assert len(anomalies) == 4
    assert {item["severity"] for item in classified} == {"MEDIUM", "HIGH"}
    assert all(item["decision_authority"] is False for item in classified)
    assert all(item["context_hash"] and len(item["context_hash"]) == 64 for item in contexts)
    assert all(item["replay_sufficient"] is True for item in contexts)
    assert all(item["activation_allowed"] is False for item in contexts)
    assert all(item["runtime_mutation_allowed"] is False for item in contexts)

