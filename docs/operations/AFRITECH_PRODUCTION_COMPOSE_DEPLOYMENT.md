# AfriTech Production Compose Deployment

Purpose: define the shortest production-style deployment path after staging
closure using Docker Compose, HTTP-only pilot edge routing, and the bounded
public verification surface.

This document is an operational runbook. It is not proof that a production
deployment is already active.

## Components

- `afritech-api`
- `afritech-dashboard`
- `edge` (Caddy reverse proxy in pilot HTTP mode)

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
3. Leave `AFRITECH_DOMAIN` unset for pilot HTTP mode.
4. If you later switch to production TLS, set `AFRITECH_DOMAIN` and restore the
   HTTPS edge configuration.

## Launch

Preferred deployment path:

```bash
./scripts/deploy_production_zero_downtime.sh --base-url http://<host>
```

If you need a clean rebuild, rerun the same deploy command after a local
`docker compose build --no-cache` in the production directory.

Manual equivalent:

```bash
docker compose --env-file deploy/production/.env.production \
  -f deploy/production/docker-compose.production.yml \
  build
docker compose --env-file deploy/production/.env.production \
  -f deploy/production/docker-compose.production.yml \
  up -d --remove-orphans
./scripts/run_local_production_probe.sh http://<host>
```

Do not use `docker compose down` as the normal deployment path. It stops the
live stack before proving that the replacement image can build and boot.

## Expected routes

- `http://<host>/health`
- `http://<host>/public/verify/health`
- `http://<host>/public/registry`
- `http://<host>/`

## Verification

```bash
./scripts/run_local_production_probe.sh http://<host>
```

## Boundary notes

- public access is limited to `/public/*`
- control-plane routes remain authenticated
- dashboard is served over the same host
- replay and trace remain authority; reverse proxy only routes traffic
- TLS is intentionally disabled in pilot mode
- for TLS cutover, use `docs/operations/AFRITECH_DOMAIN_TLS_CUTOVER.md`
