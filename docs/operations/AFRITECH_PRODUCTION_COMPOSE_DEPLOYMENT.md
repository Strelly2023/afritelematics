# AfriTech Production Compose Deployment

Purpose: define the shortest production-style deployment path after staging
closure using Docker Compose, HTTPS termination, and the bounded public
verification surface.

This document is an operational runbook. It is not proof that a production
deployment is already active.

## Components

- `afritech-api`
- `afritech-dashboard`
- `edge` (Caddy reverse proxy with HTTPS)

## Files

- `deploy/production/docker-compose.production.yml`
- `deploy/production/.env.production.example`
- `deploy/production/Caddyfile`
- `scripts/run_local_production_probe.sh`
- `scripts/bootstrap_ec2_afritech.sh`
- `docs/operations/AFRITECH_AWS_EC2_QUICKSTART.md`

## Setup

If you are starting from a fresh Ubuntu EC2 host, use:

```bash
./scripts/bootstrap_ec2_afritech.sh
```

Then continue with the production env file setup below.

1. Copy the production env file:

```bash
cd deploy/production
cp .env.production.example .env.production
```

2. Replace every placeholder secret.
3. Set `AFRITECH_DOMAIN`.
4. Ensure DNS for the domain points to the host.

## Launch

Preferred deployment path:

```bash
./scripts/deploy_production_compose.sh --base-url https://<domain>
```

Use `--no-cache` only when you intentionally need a clean image rebuild:

```bash
./scripts/deploy_production_compose.sh --base-url https://<domain> --no-cache
```

Manual equivalent:

```bash
docker compose --env-file deploy/production/.env.production \
  -f deploy/production/docker-compose.production.yml \
  build
docker compose --env-file deploy/production/.env.production \
  -f deploy/production/docker-compose.production.yml \
  up -d --remove-orphans
./scripts/run_local_production_probe.sh https://<domain>
```

Do not use `docker compose down` as the normal deployment path. It stops the
live stack before proving that the replacement image can build and boot.

## Expected routes

- `https://<domain>/health`
- `https://<domain>/public/verify/health`
- `https://<domain>/public/registry`
- `https://<domain>/`

## Verification

```bash
./scripts/run_local_production_probe.sh https://<domain>
```

## Boundary notes

- public access is limited to `/public/*`
- control-plane routes remain authenticated
- dashboard is served over the same domain
- replay and trace remain authority; reverse proxy only routes traffic
