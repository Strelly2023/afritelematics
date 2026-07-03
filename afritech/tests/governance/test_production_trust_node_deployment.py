from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
COMPOSE = ROOT / "deploy/production/docker-compose.trust-node.yml"
STAGING_COMPOSE = ROOT / "deploy/staging/docker-compose.staging.yml"
NGINX = ROOT / "deploy/production/nginx/trust-node.conf.template"
ENV_EXAMPLE = ROOT / "deploy/production/.env.production.trust-node.example"
RUNBOOK = ROOT / "docs/operations/AFRITECH_PRODUCTION_TRUST_NODE_RUNBOOK.md"
PROBE = ROOT / "scripts/run_local_production_probe.sh"
SETUP = ROOT / "scripts/setup_production_trust_node.sh"
ANCHOR = ROOT / "scripts/enable_live_anchoring.sh"
ACCESS = ROOT / "scripts/open_ecosystem_access.sh"
DASHBOARD = ROOT / "scripts/launch_trust_dashboard.sh"
GO_LIVE = ROOT / "scripts/go_live_anchor_now.sh"


def test_trust_node_compose_defines_nginx_certbot_api_and_dashboard() -> None:
    text = COMPOSE.read_text(encoding="utf-8")

    for item in (
        "afritech-api:",
        "afritech-dashboard:",
        "nginx:",
        "certbot:",
        "80:80",
        "443:443",
        "trust-node.conf.template",
        "certbot_certs",
        "afritech_anchor_index",
        ".env.production.trust-node",
        "AFRIRIDE_DB_PATH: /var/lib/afritech/pilot_state.sqlite3",
        "AFRITECH_RUNTIME_ENVIRONMENT: production",
        "AFRITECH_AGENT_STATE_PATH: /var/lib/afritech/agents/production.sqlite3",
        '127.0.0.1:8000:8000',
    ):
        assert item in text


def test_staging_cannot_claim_production_backend_ports() -> None:
    text = STAGING_COMPOSE.read_text(encoding="utf-8")

    assert "127.0.0.1:${AFRITECH_STAGING_API_PORT:-18000}:8000" in text
    assert "127.0.0.1:${AFRITECH_STAGING_DASHBOARD_PORT:-14173}:4173" in text
    assert "http://127.0.0.1:18000" in text
    assert "AFRIRIDE_DB_PATH: /var/lib/afritech/pilot_state.sqlite3" in text
    assert "AFRITECH_RUNTIME_ENVIRONMENT: staging" in text
    assert "AFRITECH_AGENT_STATE_PATH: /var/lib/afritech/agents/staging.sqlite3" in text
    assert '"8000:8000"' not in text


def test_nginx_routes_public_verification_api_dashboard_and_websockets() -> None:
    text = NGINX.read_text(encoding="utf-8")

    for item in (
        "server_name ${AFRITECH_DOMAIN}",
        "ssl_certificate /etc/letsencrypt/live/${AFRITECH_DOMAIN}/fullchain.pem",
        "Strict-Transport-Security",
        "location /public/",
        "location /api/",
        "location /v1/",
        "location /ws/",
        "resolver 127.0.0.11 valid=10s ipv6=off",
        "set $afritech_api afritech-api:8000",
        "set $afritech_dashboard afritech-dashboard:4173",
        "proxy_pass http://$afritech_dashboard",
        "proxy_pass http://$afritech_api",
    ):
        assert item in text


def test_trust_node_env_template_requires_live_anchor_inputs() -> None:
    text = ENV_EXAMPLE.read_text(encoding="utf-8")

    for item in (
        "AFRITECH_DOMAIN=",
        "AFRITECH_TLS_EMAIL=",
        "AFRITECH_CHAIN_ENABLE_PUBLISH=true",
        "AFRITECH_CHAIN_RPC_URL_SEPOLIA=",
        "AFRITECH_CHAIN_RPC_URL_BASE_SEPOLIA=",
        "AFRITECH_CHAIN_RPC_URL_MAINNET=",
        "AFRITECH_CHAIN_PRIVATE_KEY_PATH=/run/secrets/eth_private_key",
        "AFRITECH_CHAIN_CONTRACT_ADDRESS=",
        "AFRITECH_ECOSYSTEM_LIVE_RECEIPT_FILE=/var/lib/afritech/ecosystem-live-anchor.json",
        "AFRITECH_CHAIN_EVENT_SUBSCRIBER_ENABLED=true",
    ):
        assert item in text


def test_trust_node_scripts_cover_setup_anchoring_access_and_dashboard() -> None:
    scripts = (SETUP, ANCHOR, ACCESS, DASHBOARD, GO_LIVE)
    for script in scripts:
        assert os.access(script, os.X_OK), f"{script} must be executable"

    setup = SETUP.read_text(encoding="utf-8")
    anchor = ANCHOR.read_text(encoding="utf-8")
    access = ACCESS.read_text(encoding="utf-8")
    dashboard = DASHBOARD.read_text(encoding="utf-8")
    go_live = GO_LIVE.read_text(encoding="utf-8")

    assert "--issue-cert" in setup
    assert "--repair-cert" in setup
    assert "--apply-firewall" in setup
    assert "ufw allow 443/tcp" in setup
    assert "certbot certonly" in setup
    assert "--cert-name \"$DOMAIN\"" in setup
    assert "--force-renewal" in setup
    assert "CERT_INSPECT_IMAGE=\"certbot/certbot:v2.11.0\"" in setup
    assert "--entrypoint sh" in setup
    assert "repoint_canonical_cert" in setup
    assert "valid_canonical_cert_exists" in setup
    assert "publish_live_ecosystem_anchor" in anchor
    assert "AFRITECH_CHAIN_PENDING_TX_TIMEOUT" in anchor
    assert "_recover_pending_receipt" in anchor
    assert "require_live=True" in anchor
    assert "record_live_ecosystem_anchor" in anchor
    assert "/public/ecosystem-evolution/verify" in access
    assert "/public/ecosystem-evolution/portal" in dashboard
    assert "setup_production_trust_node.sh" in go_live
    assert "enable_live_anchoring.sh" in go_live
    assert "open_ecosystem_access.sh" in go_live
    assert "launch_trust_dashboard.sh" in go_live
    assert "DNS resolution failed" in go_live
    assert "LIVE TRUST NODE READY" in go_live
    assert "assert_production_api_port_available" in setup
    assert "docker ps --filter publish=8000" in setup
    assert "port 8000 is owned by a non-production backend" in setup


def test_production_probe_checks_level12_15_16_public_surfaces() -> None:
    text = PROBE.read_text(encoding="utf-8")

    for item in (
        "/public/feature-registry/verify",
        "/public/global-verification/verify",
        "/public/ecosystem-evolution/verify",
        "/public/ecosystem-evolution/standard",
    ):
        assert item in text


def test_trust_node_runbook_preserves_authority_boundary() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")

    for item in (
        "PRODUCTION TRUST NODE OPERATIONS",
        "Nginx",
        "Let's Encrypt",
        "./scripts/setup_production_trust_node.sh --issue-cert --apply-firewall",
        "./scripts/setup_production_trust_node.sh --repair-cert",
        "./scripts/go_live_anchor_now.sh --profile sepolia",
        "./scripts/enable_live_anchoring.sh sepolia",
        "./scripts/open_ecosystem_access.sh",
        "./scripts/launch_trust_dashboard.sh",
        "Healthcheck Optimization",
        "docker inspect --format='{{json .State.Health}}' production-afritech-api-1",
        'test: ["CMD", "curl", "-fsS", "--max-time", "10", "http://127.0.0.1:8000/health"]',
        "start_period: 30s",
        "public ledger anchors prove publication only",
        "Dashboard observes trust surfaces only",
        "does not create runtime truth or production authorization",
        "LIVE_PUBLIC_LEDGER_ANCHORED",
    ):
        assert item in text
