from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
NGINX = ROOT / "deploy/production/nginx/afritechnology-platform.conf.template"
RUNBOOK = ROOT / "docs/operations/AFRITECH_NGINX_HOST_ROUTING_RUNBOOK.md"


def test_afritechnology_nginx_template_routes_all_subdomains_to_documented_ports() -> None:
    text = NGINX.read_text(encoding="utf-8")

    for item in (
        "server_name afritechnology.com *.afritechnology.com",
        "server_name afritechnology.com www.afritechnology.com app.afritechnology.com",
        "server_name api.afritechnology.com",
        "server_name identity.afritechnology.com",
        "server_name trust.afritechnology.com",
        "server_name merchant.afritechnology.com",
        "server_name business.afritechnology.com",
        "server_name operator.afritechnology.com",
        "server_name agent.afritechnology.com",
        "server_name fleet.afritechnology.com",
        "server_name support.afritechnology.com",
        "server_name status.afritechnology.com",
        "server_name developer.afritechnology.com docs.afritechnology.com download.afritechnology.com",
        "proxy_pass http://127.0.0.1:3000",
        "proxy_pass http://127.0.0.1:3001",
        "proxy_pass http://127.0.0.1:4001",
        "proxy_pass http://127.0.0.1:4002",
        "proxy_pass http://127.0.0.1:4003",
        "proxy_pass http://127.0.0.1:4004",
        "proxy_pass http://127.0.0.1:4005",
        "proxy_pass http://127.0.0.1:4006",
        "proxy_pass http://127.0.0.1:4007",
        "proxy_pass http://127.0.0.1:4008",
        "proxy_pass http://127.0.0.1:4009",
        "proxy_pass http://127.0.0.1:4010",
        "return 302 https://app.afritechnology.com",
    ):
        assert item in text


def test_afritechnology_nginx_runbook_explains_failure_mode_and_ports() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    for item in (
        "Routing Topology",
        "Port Map",
        "502 Bad Gateway",
        "app.afritechnology.com",
        "developer.afritechnology.com",
        "4010",
    ):
        assert item in text
