from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NGINX_TEMPLATE = ROOT / "deploy/production/nginx/afritechnology-platform.conf.template"
TRUST_NODE_COMPOSE = ROOT / "deploy/production/docker-compose.trust-node.yml"


def test_download_host_serves_apk_artifacts_before_dashboard_fallback() -> None:
    source = NGINX_TEMPLATE.read_text(encoding="utf-8")

    assert "server_name developer.afritechnology.com docs.afritechnology.com;" in source
    assert "server_name download.afritechnology.com;" in source
    assert "application/vnd.android.package-archive apk;" in source
    assert "location = /novaride/rider.apk" in source
    assert "location = /novaride/driver.apk" in source
    assert "location = /novaride/fleet.apk" in source
    assert "location = /novaride/operator.apk" in source
    assert "Content-Disposition \"attachment; filename=novaride-rider-public-pilot-release.apk\"" in source
    assert "Content-Disposition \"attachment; filename=novaride-driver-public-pilot-release.apk\"" in source

    assert source.index("location /novaride/releases/") < source.index("location /novapay/releases/")
    assert source.index("location /novapay/releases/") < source.index("location /novaid/releases/")


def test_novacodepro_host_routes_api_calls_to_fastapi() -> None:
    source = NGINX_TEMPLATE.read_text(encoding="utf-8")

    novacodepro_block = source.split("server_name novacodepro.afritechnology.com;", maxsplit=1)[1].split(
        "server {",
        maxsplit=1,
    )[0]
    assert "set $afritech_api afritech-api:8000;" in novacodepro_block
    assert "location /v1/" in novacodepro_block
    assert "location /api/" in novacodepro_block
    assert novacodepro_block.index("location /v1/") < novacodepro_block.index("location / {")
    assert "proxy_pass http://novacodepro-portal:4174;" in novacodepro_block


def test_trust_node_nginx_mounts_release_apks_read_only() -> None:
    source = TRUST_NODE_COMPOSE.read_text(encoding="utf-8")

    assert "${PWD}/apk:/var/www/afritech-apk:ro" in source
    assert "${PWD}/apk-public:/var/www/afritechnology-downloads:ro" in source
