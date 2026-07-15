from __future__ import annotations

from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from afritech.api.app import app
from afritech.architecture.domain_fabric import DOMAIN_FABRIC_PATH, load_domain_fabric, validate_domain_fabric


ROOT = Path(__file__).resolve().parents[2]


def test_public_site_metadata_is_corporate_not_operator_dashboard() -> None:
    client = TestClient(app)
    response = client.get("/v1/public/site")

    assert response.status_code == 200
    metadata = response.json()["metadata"]
    assert metadata["title"] == "AfriTechnology | Trusted Digital Platforms"
    assert metadata["canonical"] == "https://afritechnology.com/"
    assert "AfriRide Operator Dashboard" not in metadata["title"]
    assert metadata["robots"] == "index,follow"


def test_product_catalog_distinguishes_lifecycle_and_availability() -> None:
    client = TestClient(app)
    response = client.get("/v1/public/products")

    assert response.status_code == 200
    products = response.json()["products"]
    by_slug = {product["slug"]: product for product in products}
    assert by_slug["novacodepro"]["availability"] == "Available"
    assert by_slug["novaride"]["availability"] == "Controlled Pilot"
    assert by_slug["novapay"]["availability"] == "Controlled Pilot"
    assert by_slug["novacommerce"]["availability"] == "Coming Soon"
    assert by_slug["novapay"]["payment_boundary"] == "Real payments require separate financial governance."


def test_contact_request_returns_trackable_reference() -> None:
    client = TestClient(app)
    response = client.post(
        "/v1/public/contact-requests",
        json={
            "request_type": "START_PROJECT",
            "name": "Example User",
            "email": "user@example.com",
            "organization": "Example Business",
            "country": "AU",
            "product_interests": ["NOVAPAY", "NOVACODEPRO"],
            "message": "We want to build a governed payment platform with operating evidence.",
            "preferred_contact_method": "EMAIL",
            "consent": {"privacy_policy_version": "2026.1", "marketing": False},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "RECEIVED"
    assert payload["reference"].startswith("AFR-2026-")
    assert payload["sla_timer_started"] is True
    assert payload["consent_recorded"] is True


def test_enterprise_service_catalog_is_machine_readable_and_explicit() -> None:
    client = TestClient(app)
    response = client.get("/v1/catalog/services")

    assert response.status_code == 200
    payload = response.json()
    services = {service["domain"]: service for service in payload["services"]}
    assert payload["wildcard_dns_policy"] == "PRODUCTION_EXPLICIT_RECORDS_ONLY"
    assert payload["unknown_host_policy"] == "RETURN_404_OR_TLS_EDGE_REJECT"
    assert services["afritechnology.com"]["name"] == "Public Website"
    assert services["app.afritechnology.com"]["indexing"] == "noindex,nofollow"
    assert services["novacodepro.afritechnology.com"]["authentication_required"] is True


def test_security_disclosure_routes_to_security_owner() -> None:
    client = TestClient(app)
    response = client.post(
        "/v1/public/contact-requests",
        json={
            "request_type": "SECURITY_DISCLOSURE",
            "name": "Security Reporter",
            "email": "security@example.com",
            "country": "AU",
            "product_interests": ["NOVATRUST"],
            "message": "I need to report a vulnerability in a responsible disclosure workflow.",
            "preferred_contact_method": "EMAIL",
            "consent": {"privacy_policy_version": "2026.1", "marketing": False},
        },
    )

    assert response.status_code == 200
    assert response.json()["owner"] == "Security Response"


def test_nginx_public_root_is_not_dashboard_upstream() -> None:
    template = (ROOT / "deploy/production/nginx/trust-node.conf.template").read_text()

    public_block_start = template.index("server_name ${AFRITECH_DOMAIN} about.${AFRITECH_DOMAIN}")
    public_block_end = template.index("server_name app.${AFRITECH_DOMAIN};")
    public_block = template[public_block_start:public_block_end]

    assert "set $public_web public-web:4175;" in public_block
    assert "proxy_pass http://$public_web;" in public_block
    assert "proxy_pass http://$afritech_dashboard;" not in public_block
    assert "location /v1/public/" in public_block
    assert "location /rides/" not in public_block
    assert "location /driver/" not in public_block
    assert "location /ws/" not in public_block
    assert "listen 80 default_server;" in template
    assert "return 404;" in template


def test_app_subdomain_is_noindexed_and_separate() -> None:
    template = (ROOT / "deploy/production/nginx/trust-node.conf.template").read_text()

    app_block_start = template.index("server_name app.${AFRITECH_DOMAIN};")
    app_block_end = template.index("server_name novacodepro.${AFRITECH_DOMAIN};")
    app_block = template[app_block_start:app_block_end]

    assert "add_header X-Robots-Tag \"noindex, nofollow\" always;" in app_block
    assert "set $afritech_dashboard afritech-dashboard:4173;" in app_block
    assert "proxy_pass http://$afritech_dashboard;" in app_block


def test_caddyfile_separates_public_root_from_app_portal() -> None:
    caddyfile = (ROOT / "deploy/production/Caddyfile").read_text()

    assert "http://afritechnology.com, http://about.afritechnology.com" in caddyfile
    assert "reverse_proxy public-web:4175" in caddyfile
    assert "http://app.afritechnology.com" in caddyfile
    assert "X-Robots-Tag \"noindex, nofollow\"" in caddyfile
    assert "reverse_proxy afritech-dashboard:4173" in caddyfile
    assert "http://afritechnology.com, http://app.afritechnology.com" not in caddyfile


def test_domain_fabric_rejects_production_wildcard_dns() -> None:
    fabric_text = (ROOT / "config/afritechnology/domain-fabric.yaml").read_text()
    fabric = yaml.safe_load(fabric_text)

    assert fabric["wildcard_dns_policy"] == "PRODUCTION_EXPLICIT_RECORDS_ONLY"
    assert any(entry["host_pattern"] == "*.afritechnology.com" for entry in fabric["forbidden"])
    assert fabric["private_hosted_zone"]["domain"] == "internal.afritechnology.com"
    assert fabric["private_hosted_zone"]["access_model"] == "zero-trust-private-hosted-zone"

    validate_domain_fabric(load_domain_fabric(DOMAIN_FABRIC_PATH))

    public_hosts = {record["host"] for record in fabric["domains"] if record["exposure"] != "private"}
    private_hosts = {record["host"] for record in fabric["domains"] if record["exposure"] == "private"}

    assert "afritechnology.com" in public_hosts
    assert "app.afritechnology.com" in public_hosts
    assert "monitoring.internal.afritechnology.com" in private_hosts
    assert "vault.internal.afritechnology.com" in private_hosts
    assert all(not host.startswith("*.") for host in public_hosts)


def test_routing_isolation_reports_private_access_boundary_without_leaking_private_service_state() -> None:
    client = TestClient(app)
    response = client.get("/v1/public/routing-isolation")

    assert response.status_code == 200
    payload = response.json()
    assert payload["domain_fabric"]["private_hosted_zone"] == "internal.afritechnology.com"
    assert payload["private_access_boundary"]["publicly_exposed_internal_services"] == 0
    assert "vault.internal.afritechnology.com" not in payload["domain_fabric"]["public_hosts"]
