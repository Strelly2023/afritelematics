from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_download_host_is_not_dashboard_proxy() -> None:
    source = (ROOT / "deploy/production/nginx/afritechnology-platform.conf.template").read_text(encoding="utf-8")
    start = source.index("server_name download.afritechnology.com")
    end = source.index("server {\n    listen 443 ssl http2 default_server", start)
    block = source[start:end]
    assert "root /var/www/afritechnology-downloads" in block
    assert "proxy_pass http://afritech-dashboard:4173" not in block
    assert "try_files $uri $uri/ /index.html =404" in block
    assert block.index("location /novaride/releases/") < block.rindex("location / {")


def test_download_root_is_mounted_read_only() -> None:
    compose = (ROOT / "deploy/production/docker-compose.trust-node.yml").read_text(encoding="utf-8")
    assert "${PWD}/apk-public:/var/www/afritechnology-downloads:ro" in compose
