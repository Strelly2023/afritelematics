from __future__ import annotations

import copy
import json
from pathlib import Path
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from afritech.api.app import app
from afritech.tools.novaride_verify_cli import main


def test_novaride_verify_cli_verifies_signed_publication_file(tmp_path: Path, capsys) -> None:
    client = TestClient(app)
    publication = client.get("/v1/architecture/publication").json()
    artifact = tmp_path / "architecture-publication.json"
    artifact.write_text(json.dumps(publication, indent=2, sort_keys=True), encoding="utf-8")

    exit_code = main([str(artifact), "--format", "json"])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["valid"] is True
    assert output["signature_valid"] is True
    assert output["publication_valid"] is True


def test_novaride_verify_cli_separates_contract_and_signature_validity(tmp_path: Path, capsys) -> None:
    client = TestClient(app)
    publication = client.get("/v1/architecture/publication").json()
    tampered = copy.deepcopy(publication)
    signature_value = tampered["signature"]["value"]
    tampered["signature"]["value"] = ("B" if signature_value[0] != "B" else "C") + signature_value[1:]
    artifact = tmp_path / "architecture-publication-tampered.json"
    artifact.write_text(json.dumps(tampered, indent=2, sort_keys=True), encoding="utf-8")

    exit_code = main([str(artifact), "--format", "json"])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["valid"] is True
    assert output["signature_valid"] is False
    assert output["publication_valid"] is False


def test_novaride_verify_cli_rejects_untrusted_key_id(tmp_path: Path, capsys) -> None:
    client = TestClient(app)
    publication = client.get("/v1/architecture/publication").json()
    tampered = copy.deepcopy(publication)
    tampered["signature"]["key_id"] = "untrusted-architecture-key"
    artifact = tmp_path / "architecture-publication-untrusted-key.json"
    artifact.write_text(json.dumps(tampered, indent=2, sort_keys=True), encoding="utf-8")

    exit_code = main([str(artifact), "--format", "json"])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["valid"] is True
    assert output["signature_valid"] is False
    assert output["publication_valid"] is False


def test_novaride_verify_cli_rejects_revoked_trusted_key(monkeypatch, tmp_path: Path, capsys) -> None:
    client = TestClient(app)
    publication = client.get("/v1/architecture/publication").json()
    signature = publication["signature"]
    monkeypatch.setenv(
        "NOVATRUST_TRUSTED_ARCHITECTURE_KEYS_JSON",
        json.dumps(
            {
                "active_key_id": signature["key_id"],
                "keys": {
                    signature["key_id"]: {
                        "public_key": signature["public_key"],
                        "status": "revoked",
                    }
                },
            },
            sort_keys=True,
        ),
    )
    artifact = tmp_path / "architecture-publication-revoked.json"
    artifact.write_text(json.dumps(publication, indent=2, sort_keys=True), encoding="utf-8")

    exit_code = main([str(artifact), "--format", "json"])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["valid"] is True
    assert output["signature_valid"] is False
    assert output["publication_valid"] is False


def test_novaride_verify_cli_rejects_expired_signed_at(tmp_path: Path, capsys) -> None:
    client = TestClient(app)
    publication = client.get("/v1/architecture/publication").json()
    tampered = copy.deepcopy(publication)
    tampered_signed_at = (datetime.now(UTC) - timedelta(days=8)).isoformat()
    tampered["signed_payload"]["signed_at"] = tampered_signed_at
    tampered["signature"]["signed_at"] = tampered_signed_at
    artifact = tmp_path / "architecture-publication-expired.json"
    artifact.write_text(json.dumps(tampered, indent=2, sort_keys=True), encoding="utf-8")

    exit_code = main([str(artifact), "--format", "json"])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["valid"] is True
    assert output["signature_valid"] is False
    assert output["publication_valid"] is False


def test_novaride_verify_cli_rejects_payload_hash_mismatch(tmp_path: Path, capsys) -> None:
    client = TestClient(app)
    publication = client.get("/v1/architecture/publication").json()
    tampered = copy.deepcopy(publication)
    tampered["signature"]["payload_hash"] = "A" * len(tampered["signature"]["payload_hash"])
    artifact = tmp_path / "architecture-publication-payload-hash.json"
    artifact.write_text(json.dumps(tampered, indent=2, sort_keys=True), encoding="utf-8")

    exit_code = main([str(artifact), "--format", "json"])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["valid"] is True
    assert output["signature_valid"] is False
    assert output["publication_valid"] is False


def test_novaride_verify_cli_can_verify_current_registry_version(capsys) -> None:
    exit_code = main(["--version", "2026.07.0", "--format", "json"])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["valid"] is True
    assert output["resolved_version"] == "2026.07.0"
