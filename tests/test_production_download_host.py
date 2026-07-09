from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NGINX_TEMPLATE = ROOT / "deploy/production/nginx/afritechnology-platform.conf.template"
TRUST_NODE_COMPOSE = ROOT / "deploy/production/docker-compose.trust-node.yml"


def test_download_host_serves_apk_artifacts_before_dashboard_fallback() -> None:
    source = NGINX_TEMPLATE.read_text(encoding="utf-8")

    assert "server_name developer.afritechnology.com docs.afritechnology.com;" in source
    assert "server_name download.afritechnology.com;" in source
    assert "alias /var/www/afritech-apk/$apk_file;" in source
    assert "application/vnd.android.package-archive apk;" in source
    assert "Content-Disposition \"attachment; filename=$apk_file\"" in source

    download_block = source.split("server_name download.afritechnology.com;", maxsplit=1)[1].split(
        "server {",
        maxsplit=1,
    )[0]
    assert "location ~ ^/(novaride|novapay|novaid)/" in download_block
    assert "proxy_pass http://afritech-dashboard:4173;" in download_block
    assert download_block.index("alias /var/www/afritech-apk/$apk_file;") < download_block.index(
        "proxy_pass http://afritech-dashboard:4173;",
    )


def test_trust_node_nginx_mounts_release_apks_read_only() -> None:
    source = TRUST_NODE_COMPOSE.read_text(encoding="utf-8")

    assert "- ../../apk:/var/www/afritech-apk:ro" in source
