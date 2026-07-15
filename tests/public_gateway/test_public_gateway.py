from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from afritech.api.app import app


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

    public_block_start = template.index("server_name ${AFRITECH_DOMAIN};")
    public_block_end = template.index("server_name app.${AFRITECH_DOMAIN};")
    public_block = template[public_block_start:public_block_end]

    assert "set $public_web public-web:4175;" in public_block
    assert "proxy_pass http://$public_web;" in public_block
    assert "proxy_pass http://$afritech_dashboard;" not in public_block
    assert "location /v1/public/" in public_block
    assert "location /rides/" not in public_block
    assert "location /driver/" not in public_block
    assert "location /ws/" not in public_block


def test_app_subdomain_is_noindexed_and_separate() -> None:
    template = (ROOT / "deploy/production/nginx/trust-node.conf.template").read_text()

    app_block_start = template.index("server_name app.${AFRITECH_DOMAIN};")
    app_block_end = template.index("server_name novacodepro.${AFRITECH_DOMAIN};")
    app_block = template[app_block_start:app_block_end]

    assert "add_header X-Robots-Tag \"noindex, nofollow\" always;" in app_block
    assert "set $afritech_dashboard afritech-dashboard:4173;" in app_block
    assert "proxy_pass http://$afritech_dashboard;" in app_block


def test_domain_fabric_rejects_production_wildcard_dns() -> None:
    fabric = (ROOT / "config/afritechnology/domain-fabric.yaml").read_text()

    assert "wildcard_dns_policy: PRODUCTION_EXPLICIT_RECORDS_ONLY" in fabric
    assert 'host_pattern: "*.afritechnology.com"' in fabric
    assert "AfriRide Operator Dashboard" in fabric
