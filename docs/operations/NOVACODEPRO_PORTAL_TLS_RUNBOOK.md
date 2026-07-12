# NovaCodePro Portal TLS Runbook

NovaCodePro is served as a separate frontend at `novacodepro.afritechnology.com`.
It must use a certificate whose subject alternative names include
`DNS:novacodepro.afritechnology.com`; the parent `afritechnology.com`
certificate is not sufficient unless it explicitly contains that SAN.

## 1. Confirm DNS and the Current Certificate

Run these checks from a network path that can reach production:

```bash
dig +short novacodepro.afritechnology.com

echo | openssl s_client \
  -servername novacodepro.afritechnology.com \
  -connect novacodepro.afritechnology.com:443 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
```

The certificate output must include:

```text
DNS:novacodepro.afritechnology.com
```

If it does not, issue the dedicated certificate below.

## 2. Recover or Start NGINX Before Issuing the Certificate

The NGINX container must be able to start before the dedicated NovaCodePro
certificate exists. The trust-node compose service mounts
`deploy/production/nginx/15-novacodepro-cert.envsh`, which sets
`NOVACODEPRO_SSL_CERTIFICATE` and `NOVACODEPRO_SSL_CERTIFICATE_KEY` during
container startup.

If `/etc/letsencrypt/live/novacodepro.afritechnology.com/fullchain.pem` and
`privkey.pem` already exist in the Certbot volume, the script selects them.
Otherwise it selects the existing `afritechnology.com` certificate so NGINX can
boot and serve HTTP-01 challenges. This fallback will still fail browser
hostname validation for `novacodepro.afritechnology.com`; it exists only to keep
the reverse proxy available while Certbot provisions the correct certificate.

After pulling the latest deployment files, recreate NGINX:

```bash
docker compose \
  -f deploy/production/docker-compose.trust-node.yml \
  up -d --force-recreate nginx

docker logs production-nginx-1 --tail=120
docker exec production-nginx-1 nginx -t
docker exec production-nginx-1 wget -qO- http://localhost/healthz
```

Expected local health response:

```text
ok
```

## 3. Confirm ACME Challenge Routing

The production NGINX HTTP server for port `80` must include
`novacodepro.${AFRITECH_DOMAIN}` and must serve the Certbot webroot from
`/var/www/certbot`:

```nginx
location /.well-known/acme-challenge/ {
  root /var/www/certbot;
}
```

From the production server, create a temporary challenge probe:

```bash
docker compose \
  -f deploy/production/docker-compose.trust-node.yml \
  exec nginx sh -lc 'mkdir -p /var/www/certbot/.well-known/acme-challenge && echo ok > /var/www/certbot/.well-known/acme-challenge/test'

curl -sS http://novacodepro.afritechnology.com/.well-known/acme-challenge/test
```

The response should be:

```text
ok
```

## 4. Issue the Dedicated Certificate

Issue a named certificate for NovaCodePro using the shared Certbot webroot.
The Compose service uses the `certbot/certbot:v2.11.0` image and already sets
`certbot` as its entrypoint:

```bash
docker compose \
  -f deploy/production/docker-compose.trust-node.yml \
  run --rm certbot \
  certonly \
  --webroot \
  --webroot-path /var/www/certbot \
  --cert-name novacodepro.afritechnology.com \
  -d novacodepro.afritechnology.com \
  --email admin@afritechnology.com \
  --agree-tos \
  --no-eff-email
```

After issuance, the files must exist in the shared LetsEncrypt volume:

```text
/etc/letsencrypt/live/novacodepro.afritechnology.com/fullchain.pem
/etc/letsencrypt/live/novacodepro.afritechnology.com/privkey.pem
```

## 5. Recreate NGINX

Recreate the NGINX container after the certificate is present. The startup
script will now select the dedicated NovaCodePro certificate automatically:

```bash
docker compose \
  -f deploy/production/docker-compose.trust-node.yml \
  config

docker compose \
  -f deploy/production/docker-compose.trust-node.yml \
  up -d --force-recreate nginx
```

If the portal image was also updated, rebuild both services:

```bash
docker compose \
  -f deploy/production/docker-compose.trust-node.yml \
  up -d --build novacodepro-portal nginx
```

## 6. Verify Public HTTPS

Verify the certificate and the served portal:

```bash
echo | openssl s_client \
  -servername novacodepro.afritechnology.com \
  -connect novacodepro.afritechnology.com:443 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates -ext subjectAltName

curl -I https://novacodepro.afritechnology.com
curl -sS https://novacodepro.afritechnology.com | head -30
```

Expected result:

```text
HTTP/2 200
content-type: text/html
DNS:novacodepro.afritechnology.com
```

Also verify JavaScript and CSS asset URLs from the HTML return `200` and are
served by the NovaCodePro portal, not by the API or the existing dashboard.
