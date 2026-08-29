from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = (
    ROOT
    / "scripts"
    / "novaride"
    / "build_production_container.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "novaride_production_container_build",
        MODULE_PATH,
    )

    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_authority_binds_canonical_inputs() -> None:
    module = load_module()

    assert module.IMAGE == "novaride-api:2026.2"
    assert module.PLATFORM == "linux/amd64"

    assert (
        module.DOCKERFILE
        == ROOT / "deploy/staging/Dockerfile.api"
    )
    assert (
        module.LOCK
        == ROOT
        / "deploy/production/requirements-api.lock"
    )

    module.require_authoritative_inputs()


def test_build_command_is_linux_amd64_and_local_only() -> None:
    module = load_module()

    command = module.build_command(
        docker="/usr/local/bin/docker",
        commit="abc123",
        branch="feature/test",
        timestamp="2026-08-29T00:00:00Z",
    )

    joined = " ".join(command)

    assert command[1] == "build"
    assert "--platform" in command
    assert "linux/amd64" in command
    assert "--pull=false" in command
    assert "--no-cache" in command

    assert str(module.DOCKERFILE) in command
    assert module.IMAGE in command

    assert "BUILD_COMMIT=abc123" in command
    assert "BUILD_BRANCH=feature/test" in command
    assert (
        "BUILD_TIMESTAMP=2026-08-29T00:00:00Z"
        in command
    )

    forbidden = (
        "push",
        "kubectl",
        "terraform",
        "aws ",
        "docker compose",
    )

    for token in forbidden:
        assert token not in joined.lower()


def test_runtime_validation_has_no_network() -> None:
    module = load_module()

    command = module.runtime_validation_command(
        docker="/usr/local/bin/docker",
        output_dir=Path("/tmp/evidence"),
    )

    joined = " ".join(command)

    assert command[1] == "run"
    assert "--network none" in joined
    assert (
        "afritech.tools.production_image_validation"
        in command
    )
    assert "/evidence/runtime-validation.json" in command
    assert "/evidence/sbom.json" in command


def test_execute_requires_explicit_approval(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = load_module()

    monkeypatch.delenv(
        module.EXECUTE_APPROVAL,
        raising=False,
    )
    monkeypatch.delenv(
        module.NETWORK_APPROVAL,
        raising=False,
    )

    with pytest.raises(
        module.BuildAuthorityError,
        match="explicit approval required",
    ):
        module.execute(
            output_dir=tmp_path,
            timestamp="2026-08-29T00:00:00Z",
        )


def test_execute_requires_network_approval(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = load_module()

    monkeypatch.setenv(
        module.EXECUTE_APPROVAL,
        "YES",
    )
    monkeypatch.delenv(
        module.NETWORK_APPROVAL,
        raising=False,
    )

    with pytest.raises(
        module.BuildAuthorityError,
        match="explicit approval required",
    ):
        module.execute(
            output_dir=tmp_path,
            timestamp="2026-08-29T00:00:00Z",
        )


def test_local_base_image_must_exist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_module()

    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="missing",
        ),
    )

    with pytest.raises(
        module.BuildAuthorityError,
        match="not available locally",
    ):
        module.require_local_base_image(
            docker="/usr/local/bin/docker",
        )


def test_built_image_requires_linux_amd64(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_module()

    payload = [
        {
            "Id": "sha256:" + ("1" * 64),
            "Os": "linux",
            "Architecture": "arm64",
            "Config": {
                "Labels": {
                    "org.opencontainers.image.revision":
                        "abc123"
                }
            },
            "RepoDigests": [],
        }
    ]

    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout=module.json.dumps(payload),
            stderr="",
        ),
    )

    with pytest.raises(
        module.BuildAuthorityError,
        match="platform mismatch",
    ):
        module.inspect_built_image(
            docker="/usr/local/bin/docker",
            expected_commit="abc123",
        )


def test_built_image_requires_exact_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_module()

    payload = [
        {
            "Id": "sha256:" + ("1" * 64),
            "Os": "linux",
            "Architecture": "amd64",
            "Config": {
                "Labels": {
                    "org.opencontainers.image.revision":
                        "wrong"
                }
            },
            "RepoDigests": [],
        }
    ]

    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout=module.json.dumps(payload),
            stderr="",
        ),
    )

    with pytest.raises(
        module.BuildAuthorityError,
        match="OCI revision mismatch",
    ):
        module.inspect_built_image(
            docker="/usr/local/bin/docker",
            expected_commit="abc123",
        )


def test_source_contains_no_publication_or_deployment_calls() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lower = source.lower()

    forbidden = (
        '"push"',
        "'push'",
        '"kubectl"',
        "'kubectl'",
        '"terraform"',
        "'terraform'",
        '"aws"',
        "'aws'",
        '"compose"',
        "'compose'",
    )

    for token in forbidden:
        assert token not in lower


def test_evidence_explicitly_refuses_registry_claims() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")

    assert '"registry_digest": None' in source
    assert '"registry_publication": False' in source
    assert '"kubernetes_digest_binding": False' in source
    assert '"registry_digest_proven": False' in source
    assert (
        '"kubernetes_digest_binding_proven": False'
        in source
    )


def test_cli_exposes_exact_pinned_base_image(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = load_module()

    monkeypatch.setattr(
        "sys.argv",
        [
            str(MODULE_PATH),
            "--print-pinned-base-image",
        ],
    )

    assert module.main() == 0

    assert (
        capsys.readouterr().out.strip()
        == module.PINNED_BASE_IMAGE
    )
