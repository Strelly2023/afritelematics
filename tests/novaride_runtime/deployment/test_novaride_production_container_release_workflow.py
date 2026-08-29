from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]

WORKFLOW = (
    ROOT
    / ".github"
    / "workflows"
    / "novaride-production-container-release.yml"
)

BUILD_AUTHORITY = (
    ROOT
    / "scripts"
    / "novaride"
    / "build_production_container.py"
)

REGISTRY_AUTHORITY = (
    ROOT
    / "scripts"
    / "novaride"
    / "production_registry_authority.py"
)

RELEASE_VERIFIER = (
    ROOT
    / "scripts"
    / "novaride"
    / "verify_container_release.py"
)


def workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def workflow_payload() -> dict:
    return yaml.safe_load(workflow_text())


def test_workflow_is_manual_only() -> None:
    payload = workflow_payload()

    triggers = payload.get("on")
    if triggers is None:
        triggers = payload.get(True)

    assert isinstance(triggers, dict)
    assert set(triggers) == {"workflow_dispatch"}


def test_workflow_has_minimum_oidc_permissions() -> None:
    payload = workflow_payload()

    assert payload["permissions"] == {
        "contents": "read",
        "id-token": "write",
    }


def test_workflow_uses_protected_environment() -> None:
    payload = workflow_payload()

    job = payload["jobs"]["publish-production-container"]

    assert (
        job["environment"]
        == "novaride-production-container-publication"
    )


def test_workflow_has_no_static_aws_credentials() -> None:
    text = workflow_text().lower()

    forbidden = (
        "aws_access_key_id",
        "aws_secret_access_key",
        "aws_session_token",
        "access-key-id:",
        "secret-access-key:",
    )

    for token in forbidden:
        assert token not in text


def test_workflow_uses_github_oidc_for_aws() -> None:
    text = workflow_text()

    assert "aws-actions/configure-aws-credentials@v4" in text
    assert "role-to-assume:" in text
    assert "id-token: write" in text


def test_runtime_aws_bindings_are_not_hard_coded() -> None:
    text = workflow_text()

    assert "${{ vars.NOVARIDE_AWS_REGION }}" in text
    assert "${{ vars.NOVARIDE_ECR_PUBLISH_ROLE_ARN }}" in text
    assert "${{ vars.NOVARIDE_AWS_ACCOUNT_ID }}" in text

    assert "210987654321" not in text


def test_canonical_artifact_contract_is_bound() -> None:
    text = workflow_text()

    assert "NOVARIDE_IMAGE_NAME: novaride-api" in text
    assert 'NOVARIDE_RELEASE_TAG: "2026.2"' in text
    assert "NOVARIDE_PLATFORM: linux/amd64" in text


def test_existing_authorities_are_reused() -> None:
    text = workflow_text()

    assert str(
        REGISTRY_AUTHORITY.relative_to(ROOT)
    ) in text

    assert str(
        BUILD_AUTHORITY.relative_to(ROOT)
    ) in text

    assert str(
        RELEASE_VERIFIER.relative_to(ROOT)
    ) in text


def test_build_requires_existing_explicit_approvals() -> None:
    text = workflow_text()

    assert (
        'NOVARIDE_PRODUCTION_IMAGE_BUILD_ALLOW_EXECUTE: "YES"'
        in text
    )

    assert (
        'NOVARIDE_PRODUCTION_IMAGE_BUILD_ALLOW_NETWORK: "YES"'
        in text
    )

    assert "--execute" in text


def test_repository_must_exist_before_publication() -> None:
    text = workflow_text()

    assert "aws ecr describe-repositories" in text
    assert "Canonical ECR repository is absent or mismatched" in text


def test_existing_release_tag_fails_closed() -> None:
    text = workflow_text()

    assert "aws ecr describe-images" in text
    assert "Release tag already exists; overwrite is forbidden" in text
    assert "ImageNotFoundException" in text


def test_publication_is_canonical_and_single_tagged() -> None:
    text = workflow_text()

    assert "docker tag" in text
    assert 'docker push "$NOVARIDE_ECR_MUTABLE_REFERENCE"' in text

    assert ":latest" not in text
    assert "docker push --all-tags" not in text


def test_remote_digest_is_read_back_from_ecr() -> None:
    text = workflow_text()

    assert "NOVARIDE_REMOTE_DIGEST" in text
    assert "imageDetails[0].imageDigest" in text
    assert "NOVARIDE_IMMUTABLE_REFERENCE" in text


def test_immutable_release_verifier_is_mandatory() -> None:
    text = workflow_text()

    assert (
        "scripts/novaride/verify_container_release.py"
        in text
    )

    assert "--expected-commit" in text
    assert "--expected-digest" in text
    assert "--expected-platform" in text


def test_receipt_does_not_claim_kubernetes_binding() -> None:
    text = workflow_text()

    assert '"registry_publication_proven": True' in text
    assert '"remote_digest_proven": True' in text
    assert (
        '"kubernetes_digest_binding_proven": False'
        in text
    )


def test_workflow_contains_no_kubernetes_or_terraform_mutation() -> None:
    text = workflow_text().lower()

    forbidden = (
        "kubectl ",
        "helm ",
        "terraform ",
    )

    for token in forbidden:
        assert token not in text


def test_workflow_does_not_mutate_repository_history() -> None:
    text = workflow_text().lower()

    forbidden = (
        "git commit",
        "git push",
        "git reset",
        "git clean",
        "git checkout",
    )

    for token in forbidden:
        assert token not in text


def test_fresh_runner_materializes_exact_pinned_base() -> None:
    text = workflow_text()

    assert "Materialize exact pinned production base" in text
    assert "--print-pinned-base-image" in text
    assert 'docker pull --platform "$NOVARIDE_PLATFORM" "$PINNED_BASE"' in text
    assert "Pinned production base platform mismatch" in text


def test_build_sbom_is_bound_to_authoritative_build_evidence() -> None:
    text = workflow_text()

    assert 'BUILD_EVIDENCE="$EVIDENCE_DIR/build-evidence.json"' in text
    assert 'SBOM="$EVIDENCE_DIR/sbom.json"' in text
    assert 'payload.get("sbom_sha256")' in text
    assert "Build SBOM digest mismatch" in text
    assert "NOVARIDE_BUILD_SBOM_SHA256" in text


def test_immutable_verifier_receives_build_sbom_contract() -> None:
    text = workflow_text()

    assert '--sbom "$NOVARIDE_BUILD_SBOM"' in text
    assert (
        '--sbom-sha256 "$NOVARIDE_BUILD_SBOM_SHA256"'
        in text
    )


def test_publication_workflow_does_not_claim_provenance() -> None:
    text = workflow_text()

    verify_step = text.split(
        "- name: Verify immutable release reference",
        1,
    )[1].split(
        "- name: Emit bounded publication receipt",
        1,
    )[0]

    assert "--provenance" not in verify_step
