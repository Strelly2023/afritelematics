# AfriTech Staging Deployment And Partner Demo Runbook

Purpose: define the beyond-GA execution path for staging deployment, real secret
injection, remote verification, controlled public exposure, and live partner
demo operation.

This runbook is an execution artifact. It does not itself prove that a staging
or production deployment is already active.

## 1. Staging environment

- deploy `afritech.api.app:app` behind a staging HTTPS endpoint
- deploy the React operator dashboard against the same staging API
- enable only bounded public verification routes:
  - `GET /public/verify/health`
  - `GET /public/registry`
  - `GET /public/verify/{anchor_id}`
  - `GET /public/partners/registry`
- keep all `v1` control-plane routes authenticated

## 2. Real secrets

- inject `AFRITECH_JWT_SECRET`
- inject `AFRITECH_EVENT_INGESTION_SECRET`
- inject `AFRIRIDE_JWT_SECRET`
- inject `AFRIRIDE_EVENT_INGESTION_SECRET`
- inject `AFRIRIDE_DJANGO_SECRET_KEY`
- inject `AFRITECH_SIGNING_PRIVATE_KEY_PATH`
- inject `AFRITECH_SIGNING_PUBLIC_KEY_PATH`
- store secrets in AWS Secrets Manager, GCP Secret Manager, or Azure Key Vault

## 3. Remote verification

- run `./scripts/run_remote_afritech_verification.sh https://staging.example`
- verify operator auth, observability dashboard, audit dashboard, partner
  registry, and public verification surfaces
- capture the staging transcript as a partner evidence artifact

## 4. Controlled public endpoint

- expose only public verification
- never expose replay mutation, governance mutation, or worker control publicly
- public verification reads registry and anchor packet only
- trace and replay remain truth

## 5. Real partner demo

- onboard partner in `partner registry`
- publish one replay-backed registry entry
- open Trust Explorer and public verification endpoint
- walk trace -> replay -> receipt -> anchor -> registry
- show rejection boundary: public registry visibility does not create authority

## 6. Demo acceptance

- staging health green
- observability dashboard reachable
- audit dashboard reachable
- partner registry contains the demo partner
- one public verification anchor resolves successfully
- no auth bypass, no raw 500 leaks, no repo secrets
