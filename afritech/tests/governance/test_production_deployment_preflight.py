from __future__ import annotations

from pathlib import Path
from scripts import preflight_production_deployment as preflight

import pytest


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "scripts/preflight_production_deployment.py"


def test_trust_node_uses_compose_secrets_instead_of_file_bind_mounts() -> None:
    text = preflight.DEFAULT_COMPOSE.read_text(encoding="utf-8")
    assert "image: ${AFRITECH_API_IMAGE:-afritech/afritech-api:production}" in text
    assert (
        "NOVACODEPRO_DATABASE_URL: "
        "${NOVATECH_CORE_DATABASE_URL:?NovaCodePro PostgreSQL URL required}"
    ) in text
    assert (
        "NOVAPROGRAMMING_DATABASE_URL: "
        "${NOVATECH_CORE_DATABASE_URL:?NovaProgramming PostgreSQL URL required}"
    ) in text
    assert "NOVARIDE_REPLAY_DB_PATH: /var/lib/afritech/novaride-runtime-replay.sqlite3" in text
    assert "NOVACODEPRO_AUTH_DB_PATH: /var/lib/afritech/novacodepro-auth.sqlite3" in text
    assert "NOVACODEPRO_DB_PATH: /var/lib/afritech/novacodepro-platform.sqlite3" in text
    assert "NOVAPAY_PERSISTENCE_BACKEND: postgres" in text
    assert (
        "NOVAPAY_DATABASE_URL: "
        "${NOVATECH_CORE_DATABASE_URL:?NovaPay PostgreSQL URL required}"
    ) in text
    for marker in (
        "NOVAID_PERSISTENCE_BACKEND: postgres",
        "NOVAID_DATABASE_URL: ${NOVATECH_CORE_DATABASE_URL:?NovaID PostgreSQL URL required}",
        "NOVAID_JWT_ISSUER: ${NOVAID_JWT_ISSUER:?NovaID JWT issuer required}",
        "NOVAID_SIGNING_KEYS_JSON: ${NOVAID_SIGNING_KEYS_JSON:?NovaID signing key registry required}",
        "NOVAID_TOKEN_PEPPER: ${NOVAID_TOKEN_PEPPER:?NovaID token pepper required}",
        "NOVAID_REDIS_URL: ${NOVAID_REDIS_URL:?NovaID Redis URL required}",
    ):
        assert marker in text
    assert "secrets:\n      - eth_private_key" in text
    assert "target: afritech_private_key.pem" in text
    assert "target: afritech_public_key.pem" in text
    assert "name: ${AFRITECH_INFRA_NETWORK:-production_infra}" in text
    assert "      - infrastructure" in text
    assert "file: ./secrets/eth_private_key" in text
    assert "./secrets/eth_private_key:/run/secrets/eth_private_key:ro" not in text


def test_all_production_compose_variants_avoid_secret_bind_mounts() -> None:
    for name in (
        "docker-compose.production.yml",
        "docker-compose.production.tls.yml",
        "docker-compose.trust-node.yml",
    ):
        text = (ROOT / "deploy/production" / name).read_text(encoding="utf-8")
        assert "file: ./secrets/eth_private_key" in text
        assert "./secrets/eth_private_key:/run/secrets/eth_private_key:ro" not in text


def test_api_image_packages_runtime_service_dependencies() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    dockerfile = (ROOT / "deploy/staging/Dockerfile.api").read_text(encoding="utf-8")
    assert '"services*"' in pyproject
    assert '"contracts*"' in pyproject
    assert 'contracts = ["*.json"]' in pyproject
    assert "[tool.setuptools.package-data]" in pyproject
    assert '"**/*.json"' in pyproject
    assert '"**/*.yaml"' in pyproject
    assert "COPY services /build/services" in dockerfile
    assert "COPY contracts /build/contracts" in dockerfile
    assert "python -m afritech.tools.production_image_validation" in dockerfile
    assert 'ENTRYPOINT ["afritech-api-entrypoint"]' in dockerfile
    assert "gosu" in dockerfile


def test_production_build_is_cached_compiler_free_and_certified() -> None:
    dockerfile = (ROOT / "deploy/staging/Dockerfile.api").read_text(encoding="utf-8")
    certifier = (ROOT / "scripts/certify_production_build.py").read_text(encoding="utf-8")
    assert "# syntax=docker/dockerfile:1.7" in dockerfile
    assert "FROM ${PYTHON_IMAGE} AS wheelhouse" in dockerfile
    assert "--mount=type=cache,target=/root/.cache/pip" in dockerfile
    assert "--mount=type=cache,target=/wheelhouse-cache" in dockerfile
    assert "requirements-api.lock" in dockerfile
    assert "--constraint /build/requirements-api.lock" in dockerfile
    assert "PYTHON_IMAGE=python:3.11.13-slim-bookworm@sha256:" in dockerfile
    assert "AFRITECH_EVENT_REGISTRY_PATH=/app/resources/" in dockerfile
    assert "--no-index" in dockerfile
    lock = ROOT / "deploy/production/requirements-api.lock"
    assert lock.is_file()
    assert "numpy==2.4.6" in lock.read_text(encoding="utf-8")
    assert "build-essential" not in dockerfile.split("FROM ${PYTHON_IMAGE} AS runtime", 1)[1]
    for artifact in (
        "build-report.json",
        "build-timing.json",
        "image-manifest.json",
        "sbom.json",
        "dependency-tree.txt",
        "runtime-validation.json",
        "certification.json",
    ):
        assert artifact in certifier


def test_environment_template_declares_regional_overlay_inputs() -> None:
    text = (
        ROOT / "deploy/production/.env.production.trust-node.example"
    ).read_text(encoding="utf-8")
    for key in preflight.REGION_ENV:
        assert f"{key}=" in text


def test_preflight_rejects_placeholder_environment(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(f"{key}=valid-value" for key in preflight.REQUIRED_ENV)
        + "\nAFRITECH_DOMAIN=trust.afritech.example\n",
        encoding="utf-8",
    )
    with pytest.raises(
        preflight.DeploymentConfigurationError,
        match="placeholder environment values",
    ):
        preflight.validate_env(env_file)


def test_preflight_rejects_missing_and_insecure_secret_files(tmp_path: Path) -> None:
    insecure = tmp_path / "private-key"
    insecure.write_text("not-a-real-key", encoding="utf-8")
    insecure.chmod(0o644)
    missing = tmp_path / "missing-key"
    with pytest.raises(
        preflight.DeploymentConfigurationError,
        match="insecure mode.*missing regular file",
    ):
        preflight.validate_secret_files((insecure, missing))
