#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import re
import ssl
import sys
import urllib.request


HTML_MARKERS = (b"<!DOCTYPE html", b"<html", b'id="root"', b"dashboard")
APK_CONTENT_TYPE = "application/vnd.android.package-archive"
IPA_CONTENT_TYPES = {"application/octet-stream", "application/x-itunes-ipa"}


def download(url: str) -> tuple[int, str, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": "novaride-release-verifier/2026.1.4"})
    with urllib.request.urlopen(request, timeout=20, context=ssl.create_default_context()) as response:
        return response.status, response.headers.get("content-type", "").split(";")[0], response.read()


def verify(apk_url: str, sha_url: str, artifact_type: str = "apk") -> None:
    status, content_type, body = download(apk_url)
    if status != 200:
        raise SystemExit(f"{apk_url} returned HTTP {status}")
    if artifact_type == "apk" and content_type != APK_CONTENT_TYPE:
        raise SystemExit(f"{apk_url} content-type {content_type!r}, expected {APK_CONTENT_TYPE!r}")
    if artifact_type == "ipa" and content_type not in IPA_CONTENT_TYPES:
        raise SystemExit(f"{apk_url} content-type {content_type!r}, expected one of {sorted(IPA_CONTENT_TYPES)!r}")
    if len(body) < 1024 * 1024:
        raise SystemExit(f"{apk_url} is too small to be a public pilot APK: {len(body)} bytes")
    if not body.startswith(b"PK"):
        raise SystemExit(f"{apk_url} does not start with APK ZIP bytes")
    if any(marker.lower() in body[:4096].lower() for marker in HTML_MARKERS):
        raise SystemExit(f"{apk_url} returned HTML/dashboard content")

    sha_status, sha_type, sha_body = download(sha_url)
    if sha_status != 200:
        raise SystemExit(f"{sha_url} returned HTTP {sha_status}")
    if sha_type not in {"text/plain", "application/octet-stream"}:
        raise SystemExit(f"{sha_url} content-type {sha_type!r} is not checksum text")
    expected = sha_body.decode("utf-8").strip().split()[0]
    if not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
        raise SystemExit(f"{sha_url} does not contain a valid SHA256")
    actual = hashlib.sha256(body).hexdigest()
    if actual.lower() != expected.lower():
        raise SystemExit(f"downloaded SHA mismatch: {actual} != {expected}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apk-url", required=True)
    parser.add_argument("--sha256-url", required=True)
    parser.add_argument("--artifact-type", choices=["apk", "ipa"], default="apk")
    args = parser.parse_args()
    verify(args.apk_url, args.sha256_url, args.artifact_type)
    print(f"public {args.artifact_type.upper()} verification passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
