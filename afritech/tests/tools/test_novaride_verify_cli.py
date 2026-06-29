from __future__ import annotations

import json
from pathlib import Path

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


def test_novaride_verify_cli_can_verify_current_registry_version(capsys) -> None:
    exit_code = main(["--version", "2026.07.0", "--format", "json"])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["valid"] is True
    assert output["resolved_version"] == "2026.07.0"
