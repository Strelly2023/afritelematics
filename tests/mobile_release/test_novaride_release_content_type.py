from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_download_nginx_has_static_apk_content_types() -> None:
    source = (ROOT / "deploy/production/nginx/afritechnology-platform.conf.template").read_text(encoding="utf-8")
    block = source[source.index("server_name download.afritechnology.com") :]
    assert "application/vnd.android.package-archive apk" in block
    assert "application/octet-stream ipa" in block
    assert "text/plain sha256" in block
    assert "X-Content-Type-Options nosniff" in block
    assert "try_files $uri =404" in block
