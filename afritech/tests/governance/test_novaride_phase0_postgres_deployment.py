from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_phase0_postgres_deployment_bundle_exists() -> None:
    compose = (ROOT / "deploy/phase0/docker-compose.phase0.yml").read_text()
    assert "postgres:16-alpine" in compose
    assert "NOVAPROGRAMMING_DATABASE_URL" in compose
    assert "novaride-postgres" in compose
    assert "uvicorn" in compose
