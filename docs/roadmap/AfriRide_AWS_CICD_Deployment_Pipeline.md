# AfriRide - AWS CI/CD Deployment Pipeline

## Document Classification

```text
STATUS: CI/CD DEPLOYMENT ROADMAP
CLASSIFICATION: ISOLATED OPERATIONAL DEPLOYMENT SURFACE
GOVERNANCE MODE: PRESERVE OR ISOLATE
```

This document defines a bounded CI/CD path for deploying the AfriRide AWS production MVP pipeline.

It is not runtime authority, replay authority, proof authority, security certification, compliance certification, and not evidence that AfriRide CI/CD deployment is already active.

It does not redefine:

```text
constitutional truth
replay authority
execution legality
core invariants
identity ontology
claim admissibility
production deployment proof
```

The goal is to automate deployment only after constitutional and replay checks pass.

Permanent rule:

```text
No deploy without constitutional closure.
No deploy without replay-safe MVP pipeline tests.
No deploy from documentation alone.
```

---

# 1. Target Pipeline Flow

```text
Git push
-> GitHub Actions CI
-> dependency install
-> unit and governance tests
-> claim discipline validation
-> constitutional pipeline validation
-> replay MVP pipeline validation
-> Docker worker image build
-> ECR image push
-> Lambda API package update
-> ECS worker service rollout
-> post-deploy smoke validation
-> rollback readiness
```

The pipeline automates deployment mechanics. It does not change AfriTech proof authority.

---

# 2. Required Repository Surfaces

The CI/CD pipeline depends on:

```text
.github/workflows/
pyproject.toml
afritech/api/app.py
afritech/execution/partition/router.py
afritech/execution/queue/partitioned_queue.py
afritech/execution/worker/worker_pool.py
afritech/storage/event_schema.py
afritech/storage/replay_engine.py
afritech/tests/governance/test_production_mvp_pipeline_replay.py
afritech.ci.claim_discipline_validator
afritech.ci.constitutional_pipeline
```

The actual deploy workflow should be introduced only when AWS account, IAM, ECR, Lambda, ECS, and RDS resources are provisioned.

---

# 3. GitHub Actions Workflow Shape

Proposed file:

```text
.github/workflows/afriride-aws-deploy.yml
```

Trigger:

```yaml
on:
  push:
    branches:
      - main
  workflow_dispatch:
```

Required jobs:

```text
validate
build_worker_image
deploy_lambda_api
deploy_ecs_workers
post_deploy_smoke
```

The workflow should use GitHub environments for deployment approval:

```text
staging
production
```

Production deployment should require manual approval until operational maturity is proven.

---

# 4. Validate Job

The validate job must run before any AWS deployment step:

```bash
python -m pytest afritech/tests/governance/test_production_mvp_pipeline_replay.py -q
python -m pytest afritech/tests/governance/test_afriride_aws_deployment_plan_doc.py -q
python -m afritech.ci.claim_discipline_validator
python -m afritech.ci.constitutional_pipeline
```

Blocking rule:

```text
If validation fails, no image is built and no AWS resource is updated.
```

This preserves the chain:

```text
code change
-> replay test
-> claim discipline
-> constitutional closure
-> deployment eligibility
```

---

# 5. AWS Authentication

Preferred authentication:

```text
GitHub OIDC federation to AWS IAM role
```

Fallback secrets for early MVP only:

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
AWS_ACCOUNT_ID
ECR_REPOSITORY
LAMBDA_FUNCTION_NAME
ECS_CLUSTER_NAME
ECS_SERVICE_NAME
```

Long-lived AWS keys should be replaced with OIDC before production.

Required IAM permissions should be least-privilege and limited to:

```text
ECR image push
Lambda update-function-code
ECS update-service
CloudWatch log access
SQS deployment smoke checks
```

The CI role must not mutate constitutional proof surfaces.

---

# 6. Worker Image Build and ECR Push

Worker image tagging must not rely only on `latest`.

Required tags:

```text
git_sha
semver when available
latest for staging convenience only
```

Example image identity:

```text
${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/afriride-worker:${GITHUB_SHA}
```

Required build job responsibilities:

```text
authenticate to ECR
build worker image
tag image with commit SHA
push image to ECR
emit image digest
```

Deployment must prefer immutable image digests or commit SHA tags.

---

# 7. Lambda API Deployment

The Lambda API deployment packages:

```text
afritech/api/app.py
afritech/edge/
afritech/execution/partition/
afritech/storage/event_schema.py
Lambda handler using Mangum
runtime dependencies
```

Required Lambda handler:

```python
from afritech.api.app import app
from mangum import Mangum

handler = Mangum(app)
```

Deployment command shape:

```bash
aws lambda update-function-code \
  --function-name "$LAMBDA_FUNCTION_NAME" \
  --zip-file fileb://function.zip
```

Lambda deployment must occur only after validation passes.

---

# 8. ECS Worker Deployment

The ECS deployment updates worker tasks after the ECR image is pushed.

Required ECS controls:

```text
minimumHealthyPercent: 100
maximumPercent: 200
force-new-deployment
deployment circuit breaker enabled
rollback enabled
```

Deployment command shape:

```bash
aws ecs update-service \
  --cluster "$ECS_CLUSTER_NAME" \
  --service "$ECS_SERVICE_NAME" \
  --force-new-deployment
```

Worker rollout must preserve:

```text
partitioned queue semantics
worker-only core invocation
event_log append-only persistence
replay hash generation
```

---

# 9. Post-Deploy Smoke Validation

Post-deploy validation must verify:

```text
API Gateway accepts POST /process
response status is accepted
partition_id is returned
SQS queue receives normalized message
worker consumes message
RDS event_log receives row
replay verification passes
CloudWatch contains no critical deployment errors
```

Post-deploy smoke tests are operational checks. They do not replace constitutional validation.

---

# 10. Rollback Strategy

Rollback must be explicit and traceable.

Rollback controls:

```text
previous Lambda version or alias
previous ECS task definition
previous ECR image digest
deployment event record
operator approval for production rollback
```

Rollback triggers:

```text
replay mismatch
worker crash loop
event_log write failure
SQS dead-letter growth
API error-rate threshold
post-deploy smoke failure
```

Rollback must not delete replay ledger rows. Operational rollback changes serving infrastructure, not historical truth.

---

# 11. Observability Gates

Deployment should emit or verify metrics for:

```text
GitHub Actions run id
commit SHA
ECR image digest
Lambda version
ECS task definition revision
SQS queue depth
worker failure count
event_log write failures
replay mismatch count
post-deploy smoke status
```

Minimum alerting:

```text
replay mismatch > 0
event_log write failures > 0
dead-letter queue messages > 0
worker crash loop detected
API 5xx rate above threshold
```

---

# 12. Safe Workflow Skeleton

This is a non-authoritative workflow skeleton. It must be adapted to actual AWS resource names before use.

```yaml
name: AfriRide AWS CI/CD

on:
  push:
    branches:
      - main
  workflow_dispatch:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install -e ".[dev]"
      - run: python -m pytest afritech/tests/governance/test_production_mvp_pipeline_replay.py -q
      - run: python -m pytest afritech/tests/governance/test_afriride_aws_deployment_plan_doc.py -q
      - run: python -m afritech.ci.claim_discipline_validator
      - run: python -m afritech.ci.constitutional_pipeline

  build_worker_image:
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
          aws-region: ${{ secrets.AWS_REGION }}
      - name: Login to ECR
        uses: aws-actions/amazon-ecr-login@v2
      - name: Build and push worker image
        run: |
          docker build -t "$ECR_REPOSITORY:$GITHUB_SHA" .
          docker push "$ECR_REPOSITORY:$GITHUB_SHA"

  deploy_lambda_api:
    needs: validate
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - name: Package Lambda API
        run: zip -r function.zip afritech handler.py pyproject.toml
      - name: Update Lambda code
        run: |
          aws lambda update-function-code \
            --function-name "$LAMBDA_FUNCTION_NAME" \
            --zip-file fileb://function.zip

  deploy_ecs_workers:
    needs: build_worker_image
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Update ECS service
        run: |
          aws ecs update-service \
            --cluster "$ECS_CLUSTER_NAME" \
            --service "$ECS_SERVICE_NAME" \
            --force-new-deployment

  post_deploy_smoke:
    needs:
      - deploy_lambda_api
      - deploy_ecs_workers
    runs-on: ubuntu-latest
    steps:
      - run: echo "Run API, queue, worker, event_log, and replay smoke checks"
```

---

# 13. Bounded Non-Claims

This document does not claim:

```text
CI/CD deployment active
AWS deployment completed
AfriRide production readiness achieved
zero-downtime deployment proven
automatic rollback proven
global marketplace readiness achieved
universal fault tolerance achieved
complete state-space exhaustiveness achieved
infinite-scale dispatch guarantees achieved
PCI compliance achieved
SOC 2 compliance achieved
```

---

# 14. Safe Final Classification

```text
AfriRide AWS CI/CD planning is a bounded operational deployment roadmap
for connecting GitHub Actions validation, constitutional closure,
replay-safe MVP tests, ECR worker images, Lambda API updates,
ECS worker rollouts, post-deploy smoke checks, and explicit rollback
without redefining AfriTech constitutional truth or claiming active
production deployment.
```

