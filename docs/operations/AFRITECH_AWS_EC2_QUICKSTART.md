# AfriTech AWS EC2 Quickstart

Purpose: turn a fresh Ubuntu EC2 host into a production-style AfriTech node
using the repo's existing Docker Compose deployment assets.

This document is an operator quickstart. It is not proof that a public
production deployment is already active.

## Preconditions

- Ubuntu EC2 host reachable over SSH
- optional DNS A record for the later TLS cutover
- repository available by `git clone` or file copy
- production secrets prepared
- AfriTech signing keypair available for host installation

## Step 1. Patch the host

If the host has just been created or upgraded:

```bash
sudo apt update -y
sudo apt upgrade -y
```

If `needrestart` reports a pending kernel upgrade, reboot before deployment:

```bash
sudo reboot
```

## Step 2. Bootstrap Docker and firewall

From the repo root on your local machine, copy or recreate the repo on the EC2
host, then run:

```bash
./scripts/bootstrap_ec2_afritech.sh
```

The bootstrap script:

- installs Docker and Compose v2
- enables the Docker service
- adds the current user to the `docker` group
- opens `80/tcp`

If the script adds the user to the Docker group, reconnect before continuing.

## Step 3. Configure the production environment

```bash
cd /path/to/afritelematics/deploy/production
cp .env.production.example .env.production
nano .env.production
```

Replace every placeholder in `.env.production`, especially:

- `AFRITECH_JWT_SECRET`
- `AFRITECH_EVENT_INGESTION_SECRET`
- `AFRIRIDE_JWT_SECRET`
- `AFRIRIDE_EVENT_INGESTION_SECRET`
- `AFRIRIDE_DJANGO_SECRET_KEY`
- `AFRIRIDE_AUDIT_API_KEY`
- `VITE_AFRIRIDE_API_URL`

## Step 4. Install signing keys

```bash
sudo mkdir -p /run/secrets
sudo cp /path/to/afritech_private_key.pem /run/secrets/afritech_private_key.pem
sudo cp /path/to/afritech_public_key.pem /run/secrets/afritech_public_key.pem
sudo chmod 600 /run/secrets/afritech_private_key.pem
sudo chmod 644 /run/secrets/afritech_public_key.pem
```

These paths match the defaults in
`/Users/ostrinov/afritelematics/deploy/production/.env.production.example`.

## Step 5. Launch the production stack

From the repo root:

```bash
./scripts/deploy_production_compose.sh --base-url http://<host>
```

This starts:

- `afritech-api`
- `afritech-dashboard`
- `edge` (Caddy for HTTP routing)

Do not run `docker-compose.production.yml` on a host that is already running
the HTTPS trust node. If `production-nginx-1` exists, ports `80` and `443` are
owned by `docker-compose.trust-node.yml`; use the trust-node operations path:

```bash
./scripts/setup_production_trust_node.sh --repair-cert
./scripts/go_live_anchor_now.sh --profile sepolia --skip-anchor
```

## Step 6. Validate HTTP reachability

Ensure the host is reachable on port 80.

Expected public routes:

- `http://<host>/`
- `http://<host>/health`
- `http://<host>/public/verify/health`
- `http://<host>/public/registry`

## Step 7. Run the live production probe

From the repo root:

```bash
./scripts/run_local_production_probe.sh http://<host>
```

This validates:

- edge reachability
- API health
- public verification health
- public registry exposure

## Operational notes

- control-plane routes remain authenticated even when the public verifier is live
- the public verification surface is intentionally bounded to `/public/*`
- TLS is intentionally disabled until the domain-based production cutover
- the zero-downtime deploy script is the normal pilot deploy path
- if Docker build context becomes too large, keep using the tightened
  `.dockerignore` already present in this repo
- if build state on the host becomes unhealthy, inspect:

```bash
docker compose -f deploy/production/docker-compose.production.yml logs --tail=200
docker system df
df -h
```

## Recommended immediate next action after your current host session

If your EC2 log shows:

- packages upgraded successfully
- `Pending kernel upgrade!`

then the next exact step is:

```bash
sudo reboot
```

After reconnecting:

```bash
cd /path/to/afritelematics
./scripts/bootstrap_ec2_afritech.sh
```
