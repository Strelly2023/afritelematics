from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from afritech.compliance.continuous_assurance import (
    _build_pdf_document,
    _canonical_hash,
    _slug,
    build_continuous_assurance_dashboard,
    collect_external_evidence_artifacts,
    export_continuous_assurance_artifacts,
    run_continuous_assurance_cycle,
)
from afritech.monitoring.realtime_anomaly_alerting import RealtimeAnomalyAlert


def _write_external_evidence_files(tmp_path: Path) -> list[Path]:
    files = {
        "cryptography_review_report.pdf": "Independent cryptography review report\nRSA signing review\nTrust assumptions\n",
        "penetration_test_report.pdf": "Independent penetration test report\nAttack surface review\nReplay resistance\n",
        "provider_certification_letter.txt": "Provider certification letter\nCallback validation\nDuplicate delivery handling\n",
        "pilot_transaction_evidence.csv": "tx,amount,currency\npilot-001,100,AUD\n",
        "operational_incident_exercise.md": "Operational incident exercises\nRecovery drill\nKey compromise tabletop\n",
        "external_compliance_assessment.md": "External compliance assessment\nSOC2 readiness\nISO 27001 mapping\n",
    }
    paths: list[Path] = []
    for name, body in files.items():
        path = tmp_path / name
        path.write_text(body, encoding="utf-8")
        paths.append(path)
    return paths


@pytest.mark.django_db
def test_slug_is_deterministic_and_safe():
    assert _slug("Hello World") == "hello_world"
    assert _slug("AfriPay Continuous Assurance") == "afripay_continuous_assurance"
    assert _slug("") == ""
    assert _slug("ABC-123") == "abc-123"


@pytest.mark.django_db
def test_canonical_hash_is_deterministic_and_canonical():
    payload_a = {"b": 2, "a": 1}
    payload_b = {"a": 1, "b": 2}

    assert _canonical_hash(payload_a) == _canonical_hash(payload_b)
    assert len(_canonical_hash(payload_a)) == 64
    assert _canonical_hash(payload_a) == _canonical_hash(deepcopy(payload_a))


@pytest.mark.django_db
def test_pdf_builder_emits_valid_deterministic_pdf():
    pdf_1 = _build_pdf_document("Continuous Assurance", ["Line 1", "Line 2"])
    pdf_2 = _build_pdf_document("Continuous Assurance", ["Line 1", "Line 2"])
    pdf_3 = _build_pdf_document("Continuous Assurance", ["Line 1", "Different"])

    assert pdf_1.startswith(b"%PDF-")
    assert pdf_1 == pdf_2
    assert pdf_1 != pdf_3

    decoded = pdf_1.decode("latin-1")
    assert "Continuous Assurance" in decoded
    assert "Line 1" in decoded
    assert "xref" in decoded
    assert "trailer" in decoded
    assert "startxref" in decoded


@pytest.mark.django_db
def test_collect_external_evidence_artifacts_from_file_paths(tmp_path: Path):
    paths = _write_external_evidence_files(tmp_path)

    artifacts = collect_external_evidence_artifacts(paths)
    repeat = collect_external_evidence_artifacts(paths)

    assert len(artifacts) == 6
    assert artifacts == repeat
    assert all(item.collected_from == "outside_repository" for item in artifacts)
    assert all(len(item.sha256_hash) == 64 for item in artifacts)
    assert {item.artifact_type for item in artifacts} >= {"pdf", "txt", "csv", "md"}
    assert artifacts[0].byte_count == len(paths[0].read_bytes())


@pytest.mark.django_db
def test_collect_external_evidence_artifacts_from_descriptors(tmp_path: Path):
    path = tmp_path / "provider_letter.txt"
    path.write_text("provider certification letter", encoding="utf-8")

    artifacts = collect_external_evidence_artifacts(
        [
            {
                "source_name": "provider_certification_letter",
                "artifact_type": "txt",
                "path": str(path),
                "notes": "external partner attestation",
            }
        ]
    )

    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert artifact.source_name == "provider_certification_letter"
    assert artifact.artifact_type == "txt"
    assert artifact.notes == "external partner attestation"


@pytest.mark.django_db
def test_collect_external_evidence_artifacts_rejects_invalid_type():
    with pytest.raises(TypeError):
        collect_external_evidence_artifacts([object()])  # type: ignore[list-item]


@pytest.mark.django_db
def test_build_continuous_assurance_dashboard_reports_controls(tmp_path: Path):
    paths = _write_external_evidence_files(tmp_path)
    artifacts = collect_external_evidence_artifacts(paths)
    alert = RealtimeAnomalyAlert(
        alert_id="alert-001",
        alert_type="REPLAY_MISMATCH_ALERT",
        ride_id="ride-001",
        trace_id="trace-001",
        event_id="event-001",
        replay_hash="r" * 64,
        receipt_hash_optional="s" * 64,
        evidence_pointer="trace:trace-001:event:event-001:ride:ride-001",
        severity="CRITICAL",
        opened_at="2026-06-14T00:00:00Z",
        anomaly_type="replay_mismatch",
        actor_id="operator-1",
        device_id="console-1",
    )

    dashboard = build_continuous_assurance_dashboard(
        external_evidence=artifacts,
        anomaly_alerts=(alert,),
        monitoring_status="WATCH",
        submission_ready=True,
        regulator_ready=True,
    )

    assert dashboard["view"] == "continuous_assurance_dashboard"
    assert dashboard["classification"] == "CONTINUOUS_ASSURANCE"
    assert dashboard["authority_boundary"] == "dashboard_reads_external_evidence_and_monitoring_only"
    assert dashboard["monitoring_status"] == "WATCH"
    assert dashboard["anomaly_status"] == "WATCH"
    assert dashboard["submission_ready"] is True
    assert dashboard["regulator_ready"] is True
    assert dashboard["external_evidence_count"] == 6
    assert dashboard["anomaly_alert_counts"] == {"total": 1, "critical": 1, "high": 0, "medium": 0}
    assert dashboard["evidence_controls"]["outside_repository_collection"] is True
    assert dashboard["evidence_controls"]["cryptography_review_attached"] is True
    assert dashboard["evidence_controls"]["penetration_test_attached"] is True
    assert dashboard["evidence_controls"]["provider_certification_attached"] is True
    assert dashboard["evidence_controls"]["incident_exercises_attached"] is True
    assert dashboard["evidence_controls"]["compliance_assessment_attached"] is True
    assert dashboard["submission_controls"] == {
        "regulator_pack_ready": True,
        "investor_dossier_ready": True,
        "anomaly_alert_export_ready": True,
    }


@pytest.mark.django_db
def test_build_continuous_assurance_dashboard_serialization_roundtrip():
    dashboard = build_continuous_assurance_dashboard()

    encoded = json.dumps(dashboard, sort_keys=True)
    decoded = json.loads(encoded)

    assert decoded == dashboard
    assert decoded["external_evidence_count"] == 0
    assert decoded["submission_controls"]["anomaly_alert_export_ready"] is False


@pytest.mark.django_db
def test_run_continuous_assurance_cycle_builds_package(tmp_path: Path):
    paths = _write_external_evidence_files(tmp_path)

    package = run_continuous_assurance_cycle(
        evidence_items=paths,
        payment_reference="continuous.assurance.test.001",
    )

    assert package.title == "AfriPay Continuous Assurance Package"
    assert package.authority_boundary == "continuous_assurance_evidence_only"
    assert len(package.package_hash) == 64
    assert package.dashboard["submission_ready"] is True
    assert package.dashboard["regulator_ready"] is True
    assert package.dashboard["external_evidence_count"] == 6
    assert len(package.external_evidence) == 6
    assert package.regulator_audit_package.package_hash
    assert package.investor_dossier.dossier_hash
    assert package.provider_certification.package_hash


@pytest.mark.django_db
def test_run_continuous_assurance_cycle_is_replay_safe(tmp_path: Path):
    paths = _write_external_evidence_files(tmp_path)

    first = run_continuous_assurance_cycle(
        evidence_items=paths,
        payment_reference="continuous.assurance.test.002",
    )
    second = run_continuous_assurance_cycle(
        evidence_items=paths,
        payment_reference="continuous.assurance.test.002",
    )

    assert first.title == second.title
    assert first.dashboard["submission_ready"] is True
    assert second.dashboard["submission_ready"] is True
    assert len(first.external_evidence) == len(second.external_evidence) == 6
    assert len(first.package_hash) == 64
    assert len(second.package_hash) == 64


@pytest.mark.django_db
def test_export_continuous_assurance_artifacts(tmp_path: Path):
    paths = _write_external_evidence_files(tmp_path)
    package = run_continuous_assurance_cycle(
        evidence_items=paths,
        payment_reference="continuous.assurance.test.003",
    )

    exported = export_continuous_assurance_artifacts(package, tmp_path / "exported")

    assert exported["json"].exists()
    assert exported["pdf"].exists()
    assert exported["pdf"].read_bytes().startswith(b"%PDF-")

    payload = json.loads(exported["json"].read_text(encoding="utf-8"))
    assert payload["schema"] == "afritech.continuous_assurance_package.v1"
    assert payload["package_hash"] == package.package_hash
    assert payload["external_evidence"][0]["schema"] == "afritech.external_evidence_artifact.v1"

