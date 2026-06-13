from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from afritech.api.app import app
from afritech.api.auth.jwt_device_auth import JWT
from afritech.compliance.continuous_assurance import (
    build_continuous_assurance_dashboard,
    collect_external_evidence_artifacts,
    export_continuous_assurance_artifacts,
    run_continuous_assurance_cycle,
)


client = TestClient(app)


def auth_headers(role: str = "OPERATOR", user_id: str = "ops-1") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role)
    return {"Authorization": f"Bearer {token}"}


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
def test_live_production_monitoring_dashboard_reports_alerts():
    response = client.get("/v1/ops/continuous-assurance/dashboard", headers=auth_headers())

    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "continuous_assurance_dashboard"
    assert payload["monitoring_status"] in {"GREEN", "WATCH"}
    assert payload["submission_ready"] is True
    assert payload["regulator_ready"] is True
    assert payload["anomaly_alert_counts"]["total"] >= 1


@pytest.mark.django_db
def test_automatic_anomaly_detection_and_dashboard_builder():
    dashboard = build_continuous_assurance_dashboard(
        anomaly_alerts=(),
        monitoring_status="GREEN",
        submission_ready=True,
        regulator_ready=True,
    )

    assert dashboard["view"] == "continuous_assurance_dashboard"
    assert dashboard["external_evidence_count"] == 0
    assert dashboard["submission_controls"]["regulator_pack_ready"] is True
    assert dashboard["submission_controls"]["anomaly_alert_export_ready"] is False


@pytest.mark.django_db
def test_collects_external_evidence_from_outside_repository(tmp_path: Path):
    paths = _write_external_evidence_files(tmp_path)
    artifacts = collect_external_evidence_artifacts(paths)

    assert len(artifacts) == 6
    assert all(item.collected_from == "outside_repository" for item in artifacts)
    assert {item.artifact_type for item in artifacts} >= {"pdf", "txt", "csv", "md"}
    assert all(len(item.sha256_hash) == 64 for item in artifacts)


@pytest.mark.django_db
def test_regulator_submission_automation_builds_package_from_external_evidence(tmp_path: Path):
    paths = _write_external_evidence_files(tmp_path)
    package = run_continuous_assurance_cycle(evidence_items=paths, payment_reference="continuous.assurance.test.001")

    assert len(package.package_hash) == 64
    assert package.dashboard["submission_ready"] is True
    assert package.dashboard["regulator_ready"] is True
    assert len(package.external_evidence) == 6
    assert package.regulator_audit_package.package_hash
    assert package.investor_dossier.dossier_hash
    assert package.provider_certification.package_hash


@pytest.mark.django_db
def test_submission_preview_api_returns_package(tmp_path: Path):
    paths = _write_external_evidence_files(tmp_path)
    payload = {
        "evidence_items": [
            {
                "source_name": path.stem,
                "artifact_type": path.suffix.lstrip(".") or "artifact",
                "path": str(path),
            }
            for path in paths
        ]
    }

    response = client.post(
        "/v1/ops/regulatory/submission/preview",
        json=payload,
        headers=auth_headers(role="VERIFIER", user_id="verifier-1"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["classification"] == "REGULATORY_SUBMISSION_AUTOMATION"
    assert body["verified"] is True
    assert body["package"]["dashboard"]["submission_ready"] is True
    assert len(body["package"]["external_evidence"]) == 6


@pytest.mark.django_db
def test_continuous_assurance_artifacts_export(tmp_path: Path):
    paths = _write_external_evidence_files(tmp_path)
    package = run_continuous_assurance_cycle(evidence_items=paths, payment_reference="continuous.assurance.test.002")
    exported = export_continuous_assurance_artifacts(package, tmp_path / "exported")

    assert exported["json"].exists()
    assert exported["pdf"].exists()
    assert exported["pdf"].read_bytes().startswith(b"%PDF-")

    payload = json.loads(exported["json"].read_text(encoding="utf-8"))
    assert payload["schema"] == "afritech.continuous_assurance_package.v1"
    assert payload["package_hash"] == package.package_hash


@pytest.mark.django_db
def test_continuous_assurance_docs_and_controls_exist():
    root = Path(__file__).resolve().parents[3]
    compliance_doc = root / "docs" / "compliance" / "AFRIPAY_CONTINUOUS_ASSURANCE_SUBMISSION_PACK.md"
    ops_doc = root / "docs" / "operations" / "AFRIPAY_CONTINUOUS_ASSURANCE_DASHBOARD.md"

    assert compliance_doc.exists()
    assert ops_doc.exists()
    assert "continuous assurance" in compliance_doc.read_text(encoding="utf-8").lower()
    assert "external evidence" in ops_doc.read_text(encoding="utf-8").lower()
