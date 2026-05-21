from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriRide_AWS_CICD_Deployment_Pipeline.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: CI/CD DEPLOYMENT ROADMAP",
    "CLASSIFICATION: ISOLATED OPERATIONAL DEPLOYMENT SURFACE",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

NON_REDEFINED_SURFACES = (
    "constitutional truth",
    "replay authority",
    "execution legality",
    "core invariants",
    "identity ontology",
    "claim admissibility",
    "production deployment proof",
)

REQUIRED_JOBS = (
    "validate",
    "build_worker_image",
    "deploy_lambda_api",
    "deploy_ecs_workers",
    "post_deploy_smoke",
)

FORBIDDEN_INFLATION = (
    "ci/cd deployment active",
    "aws deployment completed",
    "afriride production readiness achieved",
    "zero-downtime deployment proven",
    "automatic rollback proven",
    "global marketplace readiness achieved",
    "universal fault tolerance achieved",
    "complete state-space exhaustiveness achieved",
    "infinite-scale dispatch guarantees achieved",
    "pci compliance achieved",
    "soc 2 compliance achieved",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_cicd_plan_has_bounded_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "not runtime authority" in lowered
    assert "not evidence that AfriRide CI/CD deployment is already active".lower() in lowered
    assert "does not redefine" in lowered

    for surface in NON_REDEFINED_SURFACES:
        assert surface in text

    before_non_claims = lowered.split("# 13. bounded non-claims")[0]
    for phrase in FORBIDDEN_INFLATION:
        assert phrase not in before_non_claims


def test_cicd_plan_defines_validation_before_deployment() -> None:
    text = read_doc()

    for command in (
        "python -m pytest afritech/tests/governance/test_production_mvp_pipeline_replay.py -q",
        "python -m pytest afritech/tests/governance/test_afriride_aws_deployment_plan_doc.py -q",
        "python -m afritech.ci.claim_discipline_validator",
        "python -m afritech.ci.constitutional_pipeline",
    ):
        assert command in text

    assert "No deploy without constitutional closure." in text
    assert "If validation fails, no image is built and no AWS resource is updated." in text


def test_cicd_plan_defines_required_jobs_and_aws_authentication() -> None:
    text = read_doc()

    for job in REQUIRED_JOBS:
        assert job in text

    for auth_or_secret in (
        "GitHub OIDC federation to AWS IAM role",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_REGION",
        "AWS_ACCOUNT_ID",
        "ECR_REPOSITORY",
        "LAMBDA_FUNCTION_NAME",
        "ECS_CLUSTER_NAME",
        "ECS_SERVICE_NAME",
    ):
        assert auth_or_secret in text

    assert "Long-lived AWS keys should be replaced with OIDC before production." in text
    assert "least-privilege" in text


def test_cicd_plan_defines_ecr_lambda_and_ecs_deployment_controls() -> None:
    text = read_doc()

    for image_control in (
        "git_sha",
        "semver when available",
        "latest for staging convenience only",
        "emit image digest",
        "immutable image digests or commit SHA tags",
    ):
        assert image_control in text

    for lambda_item in (
        "from mangum import Mangum",
        "aws lambda update-function-code",
        "Lambda deployment must occur only after validation passes.",
    ):
        assert lambda_item in text

    for ecs_control in (
        "minimumHealthyPercent: 100",
        "maximumPercent: 200",
        "deployment circuit breaker enabled",
        "rollback enabled",
        "aws ecs update-service",
    ):
        assert ecs_control in text


def test_cicd_plan_defines_post_deploy_smoke_and_rollback() -> None:
    text = read_doc()

    for smoke_step in (
        "API Gateway accepts POST /process",
        "response status is accepted",
        "partition_id is returned",
        "SQS queue receives normalized message",
        "worker consumes message",
        "RDS event_log receives row",
        "replay verification passes",
    ):
        assert smoke_step in text

    for rollback_control in (
        "previous Lambda version or alias",
        "previous ECS task definition",
        "previous ECR image digest",
        "operator approval for production rollback",
        "Rollback must not delete replay ledger rows.",
    ):
        assert rollback_control in text


def test_cicd_plan_defines_observability_and_workflow_skeleton() -> None:
    text = read_doc()

    for metric in (
        "GitHub Actions run id",
        "commit SHA",
        "ECR image digest",
        "Lambda version",
        "ECS task definition revision",
        "SQS queue depth",
        "replay mismatch count",
        "post-deploy smoke status",
    ):
        assert metric in text

    for workflow_token in (
        "name: AfriRide AWS CI/CD",
        "actions/checkout@v4",
        "aws-actions/configure-aws-credentials@v4",
        "aws-actions/amazon-ecr-login@v2",
        "environment: staging",
    ):
        assert workflow_token in text
