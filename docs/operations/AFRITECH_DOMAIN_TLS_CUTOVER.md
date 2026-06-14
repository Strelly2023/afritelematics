# AfriTech Domain TLS Cutover

Status: READY FOR DOMAIN CUTOVER

Purpose: define the clean production cutover from pilot HTTP mode to a
domain-based TLS edge without IP-bound Caddy configuration.

## Preconditions

- DNS A record points `AFRITECH_DOMAIN` to the host
- ports `80/tcp` and `443/tcp` are open
- production secrets are installed
- pilot HTTP stack is healthy before cutover
- `deploy/production/.env.production.tls` has been created from the example

## Clean TLS Files

- `deploy/production/Caddyfile.tls`
- `deploy/production/docker-compose.production.tls.yml`
- `deploy/production/.env.production.tls.example`

## Cutover Steps

1. Copy the TLS env example:

```bash
cd deploy/production
cp .env.production.tls.example .env.production.tls
```

2. Replace every placeholder value.
3. Set `AFRITECH_DOMAIN` to the final domain name.
4. Set `VITE_AFRIRIDE_API_URL` to the final `https://` URL.
5. Confirm DNS resolves to the host.
6. Deploy with the TLS compose bundle:

```bash
./scripts/deploy_production_zero_downtime.sh \
  --compose-file deploy/production/docker-compose.production.tls.yml \
  --env-file deploy/production/.env.production.tls \
  --base-url https://api.your-domain.example
```

7. Validate the domain edge and health routes:

```bash
curl -fsS https://<domain>/health
curl -fsS https://<domain>/public/verify/health
curl -fsS https://<domain>/public/registry
```

8. Confirm the edge is using the domain-only Caddyfile.
9. Confirm the pilot HTTP bundle is no longer the active production bundle.

## Clean Caddy Rules

- use the domain-only site block in `Caddyfile.tls`
- do not bind the edge to an IP address
- do not use `auto_https off` for the TLS cutover
- do not reuse the pilot HTTP compose file for TLS
- do not keep the pilot HTTP env file active after cutover

## Verification

- `https://<domain>/health`
- `https://<domain>/public/verify/health`
- `https://<domain>/public/registry`

## Failure Conditions

Stop the cutover if:

- DNS does not resolve
- Caddy fails to obtain a certificate
- API health fails
- public verification health fails
- operator cannot confirm that the domain is the only public ingress

## Boundary Notes

- pilot HTTP mode and domain TLS mode are separate deployment surfaces
- pilot HTTP mode remains valid for shadow execution
- the TLS cutover does not change authority rules, replay rules, or proof rules
